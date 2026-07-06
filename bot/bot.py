import asyncio
import html
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import ADMIN_ID, BOT_TOKEN
import database as db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ──────────────────────────────────────────
# FSM: Создание сервера
# ──────────────────────────────────────────
class CreateServer(StatesGroup):
    name = State()
    description = State()
    ip = State()
    port = State()
    password = State()


# ──────────────────────────────────────────
# Утилиты
# ──────────────────────────────────────────
def e(text: str) -> str:
    """Экранирует HTML-спецсимволы в пользовательском контенте."""
    return html.escape(str(text))


def status_badge(online: int) -> str:
    return "🟢 Онлайн" if online else "⚫ Оффлайн"


async def notify_owner(owner_id: int, text: str):
    """Отправляет уведомление владельцу; молча проглатывает ошибки (бот заблокирован и т.п.)."""
    try:
        await bot.send_message(owner_id, text, parse_mode="HTML")
    except Exception as exc:
        logger.warning("Не удалось уведомить пользователя %s: %s", owner_id, exc)


# ──────────────────────────────────────────
# /start — регистрация
# ──────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await db.register_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "👋 Добро пожаловать в <b>LostMiner</b> — каталог игровых серверов!\n\n"
        "📋 <b>Команды:</b>\n"
        "/серверы — список серверов\n"
        "/создать — добавить свой сервер\n"
        "/включить — включить сервер на 1 час\n\n"
        "Используй команды в меню или пиши их вручную.",
        parse_mode="HTML",
    )


# ──────────────────────────────────────────
# /серверы — список одобренных серверов
# ──────────────────────────────────────────
@dp.message(Command("серверы"))
async def cmd_servers(message: Message):
    servers = await db.get_approved_servers()
    if not servers:
        await message.answer("📭 Пока нет ни одного одобренного сервера.")
        return

    text = "🗂 <b>Список серверов LostMiner:</b>\n\n"
    for s in servers:
        text += (
            f"<b>{e(s['name'])}</b>\n"
            f"📝 {e(s['description'])}\n"
            f"🌐 <code>{e(s['ip'])}:{e(str(s['port']))}</code>\n"
            f"🔑 Пароль: <code>{e(s['password']) if s['password'] else 'нет'}</code>\n"
            f"📶 {status_badge(s['online'])}\n"
            f"{'─' * 24}\n"
        )
    await message.answer(text, parse_mode="HTML")


# ──────────────────────────────────────────
# /создать — пошаговое создание сервера
# ──────────────────────────────────────────
@dp.message(Command("создать"))
async def cmd_create(message: Message, state: FSMContext):
    await db.register_user(message.from_user.id, message.from_user.username)
    await state.set_state(CreateServer.name)
    await message.answer(
        "🛠 <b>Создание сервера</b>\n\n"
        "Шаг 1/5 — Введи <b>название</b> сервера:\n"
        "<i>Для отмены напиши /отмена</i>",
        parse_mode="HTML",
    )


@dp.message(CreateServer.name)
async def create_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текст.")
        return
    if len(message.text) > 64:
        await message.answer("❌ Название слишком длинное (макс. 64 символа). Попробуй ещё раз:")
        return
    await state.update_data(name=message.text)
    await state.set_state(CreateServer.description)
    await message.answer("Шаг 2/5 — Введи <b>описание</b> сервера:", parse_mode="HTML")


@dp.message(CreateServer.description)
async def create_description(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текст.")
        return
    if len(message.text) > 512:
        await message.answer("❌ Описание слишком длинное (макс. 512 символов). Попробуй ещё раз:")
        return
    await state.update_data(description=message.text)
    await state.set_state(CreateServer.ip)
    await message.answer("Шаг 3/5 — Введи <b>IP-адрес</b> сервера:", parse_mode="HTML")


@dp.message(CreateServer.ip)
async def create_ip(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текст.")
        return
    await state.update_data(ip=message.text.strip())
    await state.set_state(CreateServer.port)
    await message.answer("Шаг 4/5 — Введи <b>порт</b> сервера (число):", parse_mode="HTML")


@dp.message(CreateServer.port)
async def create_port(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текст.")
        return
    try:
        port = int(message.text.strip())
        if not (1 <= port <= 65535):
            raise ValueError
    except ValueError:
        await message.answer("❌ Некорректный порт. Введи число от 1 до 65535:")
        return
    await state.update_data(port=port)
    await state.set_state(CreateServer.password)
    await message.answer(
        "Шаг 5/5 — Введи <b>пароль</b> для входа на сервер\n"
        "(или напиши <code>нет</code>, если пароля нет):",
        parse_mode="HTML",
    )


@dp.message(CreateServer.password)
async def create_password(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текст.")
        return

    data = await state.get_data()
    password = message.text.strip()
    if password.lower() == "нет":
        password = ""

    await db.create_server(
        owner_id=message.from_user.id,
        name=data["name"],
        description=data["description"],
        ip=data["ip"],
        port=data["port"],
        password=password,
    )
    await state.clear()

    await message.answer(
        "✅ <b>Сервер отправлен на модерацию!</b>\n\n"
        f"📛 Название: {e(data['name'])}\n"
        f"🌐 Адрес: {e(data['ip'])}:{e(str(data['port']))}\n\n"
        "Ожидайте одобрения администратора.",
        parse_mode="HTML",
    )

    # Уведомляем администратора (ошибки не прерывают основной флоу)
    await notify_owner(
        ADMIN_ID,
        f"🔔 <b>Новый сервер на модерации!</b>\n\n"
        f"📛 {e(data['name'])}\n"
        f"🌐 {e(data['ip'])}:{e(str(data['port']))}\n\n"
        f"Используй /админ для проверки.",
    )


# ──────────────────────────────────────────
# /включить — включить свой сервер на 1 час
# ──────────────────────────────────────────
@dp.message(Command("включить"))
async def cmd_enable(message: Message):
    servers = await db.get_owner_servers(message.from_user.id)
    if not servers:
        await message.answer(
            "❌ У тебя нет одобренных серверов.\n"
            "Создай сервер командой /создать."
        )
        return

    if len(servers) == 1:
        server = servers[0]
        await db.set_server_online(server["id"])
        await message.answer(
            f"🟢 <b>Сервер «{e(server['name'])}» включён!</b>\n"
            f"Он будет отображаться онлайн в течение <b>1 часа</b>.",
            parse_mode="HTML",
        )
        return

    # Несколько серверов — показываем выбор
    buttons = [
        [InlineKeyboardButton(text=s["name"], callback_data=f"enable:{s['id']}")]
        for s in servers
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выбери сервер, который хочешь включить:", reply_markup=kb)


@dp.callback_query(F.data.startswith("enable:"))
async def cb_enable_server(callback: CallbackQuery):
    parts = callback.data.split(":", 1)
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer("❌ Некорректные данные.", show_alert=True)
        return

    server_id = int(parts[1])
    server = await db.get_server_by_id(server_id)

    if not server or server["owner_id"] != callback.from_user.id:
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return

    await db.set_server_online(server_id)
    await callback.message.edit_text(
        f"🟢 <b>Сервер «{e(server['name'])}» включён!</b>\n"
        f"Он будет отображаться онлайн в течение <b>1 часа</b>.",
        parse_mode="HTML",
    )
    await callback.answer()


# ──────────────────────────────────────────
# /админ — панель модерации (только для ADMIN_ID)
# ──────────────────────────────────────────
@dp.message(Command("админ"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У тебя нет прав для этой команды.")
        return

    servers = await db.get_pending_servers()
    if not servers:
        await message.answer("✅ Нет серверов на модерации.")
        return

    await message.answer(f"🔍 <b>Серверы на модерации: {len(servers)}</b>", parse_mode="HTML")

    for s in servers:
        text = (
            f"📛 <b>{e(s['name'])}</b>\n"
            f"📝 {e(s['description'])}\n"
            f"🌐 <code>{e(s['ip'])}:{e(str(s['port']))}</code>\n"
            f"🔑 Пароль: <code>{e(s['password']) if s['password'] else 'нет'}</code>\n"
            f"👤 Владелец: <code>{s['owner_id']}</code>\n"
            f"🕐 Создан: {s['created_at']}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить", callback_data=f"mod:approve:{s['id']}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"mod:reject:{s['id']}"
                ),
            ]
        ])
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


@dp.callback_query(F.data.startswith("mod:"))
async def cb_moderate(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 3 or parts[1] not in ("approve", "reject") or not parts[2].isdigit():
        await callback.answer("❌ Некорректные данные.", show_alert=True)
        return

    action = parts[1]
    server_id = int(parts[2])
    server = await db.get_server_by_id(server_id)

    if not server:
        await callback.answer("Сервер не найден.", show_alert=True)
        return

    if action == "approve":
        await db.set_server_status(server_id, "approved")
        result_text = f"✅ Сервер <b>«{e(server['name'])}»</b> одобрен."
        owner_text = (
            f"✅ <b>Ваш сервер «{e(server['name'])}» одобрен!</b>\n"
            f"Теперь он виден в списке /серверы\n"
            f"Включите его командой /включить"
        )
    else:
        await db.set_server_status(server_id, "rejected")
        result_text = f"❌ Сервер <b>«{e(server['name'])}»</b> отклонён."
        owner_text = (
            f"❌ <b>Ваш сервер «{e(server['name'])}» отклонён.</b>\n"
            f"Вы можете создать новый сервер командой /создать"
        )

    await callback.message.edit_text(result_text, parse_mode="HTML")
    await callback.answer()

    await notify_owner(server["owner_id"], owner_text)


# ──────────────────────────────────────────
# /отмена — выход из FSM
# ──────────────────────────────────────────
@dp.message(Command("отмена"))
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer("Нечего отменять.")
        return
    await state.clear()
    await message.answer("🚫 Создание сервера отменено.")


# ──────────────────────────────────────────
# Запуск
# ──────────────────────────────────────────
async def main():
    await db.init_db()
    logger.info("🤖 LostMiner бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
