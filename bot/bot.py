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
# FSM
# ──────────────────────────────────────────
class CreateServer(StatesGroup):
    name = State()
    description = State()
    ip = State()
    password = State()


class ChangePassword(StatesGroup):
    waiting = State()


# ──────────────────────────────────────────
# Утилиты
# ──────────────────────────────────────────
def e(text: str) -> str:
    return html.escape(str(text))


def status_badge(online: int) -> str:
    return "🟢 Онлайн" if online else "⚫ Оффлайн"


def status_label(status: str) -> str:
    return {"pending": "⏳ На модерации", "approved": "✅ Одобрен", "rejected": "❌ Отклонён"}.get(status, status)


async def notify_owner(owner_id: int, text: str):
    try:
        await bot.send_message(owner_id, text, parse_mode="HTML")
    except Exception as exc:
        logger.warning("Не удалось уведомить %s: %s", owner_id, exc)


def server_card(s) -> str:
    """Форматирует карточку сервера для показа владельцу."""
    return (
        f"🖥 <b>{e(s['name'])}</b>\n"
        f"📝 {e(s['description'])}\n"
        f"🌐 <code>{e(s['ip'])}</code>\n"
        f"🔑 Пароль: <code>{e(s['password']) if s['password'] else 'нет'}</code>\n"
        f"📋 Статус: {status_label(s['status'])}\n"
        f"📶 {status_badge(s['online'])}"
    )


def manage_keyboard(server_id: int, online: int) -> InlineKeyboardMarkup:
    """Клавиатура управления сервером."""
    toggle_text = "⚫ Выключить" if online else "🟢 Включить на 1 час"
    toggle_cb = f"srv:off:{server_id}" if online else f"srv:on:{server_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Изменить пароль", callback_data=f"srv:pwd:{server_id}")],
        [InlineKeyboardButton(text=toggle_text, callback_data=toggle_cb)],
    ])


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
        "/мой_сервер — управление своим сервером\n\n"
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
            f"🌐 <code>{e(s['ip'])}</code>\n"
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

    existing = await db.get_any_server_by_owner(message.from_user.id)
    if existing:
        await message.answer(
            "❌ У тебя уже есть сервер. Создать можно только один.\n\n"
            "Управляй им через /мой_сервер"
        )
        return

    await state.set_state(CreateServer.name)
    await message.answer(
        "🛠 <b>Создание сервера</b>\n\n"
        "Шаг 1/4 — Введи <b>название</b> сервера:\n"
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
    await message.answer("Шаг 2/4 — Введи <b>описание</b> сервера:", parse_mode="HTML")


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
    await message.answer("Шаг 3/4 — Введи <b>IP-адрес</b> сервера:", parse_mode="HTML")


@dp.message(CreateServer.ip)
async def create_ip(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текст.")
        return
    await state.update_data(ip=message.text.strip())
    await state.set_state(CreateServer.password)
    await message.answer(
        "Шаг 4/4 — Введи <b>пароль</b> для входа на сервер\n"
        "(или напиши <code>нет</code>, если пароля нет):",
        parse_mode="HTML",
    )


@dp.message(CreateServer.password)
async def create_password_step(message: Message, state: FSMContext):
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
        password=password,
    )
    await state.clear()

    await message.answer(
        "✅ <b>Сервер отправлен на модерацию!</b>\n\n"
        f"📛 Название: {e(data['name'])}\n"
        f"🌐 Адрес: <code>{e(data['ip'])}</code>\n\n"
        "Ожидайте одобрения администратора.",
        parse_mode="HTML",
    )

    await notify_owner(
        ADMIN_ID,
        f"🔔 <b>Новый сервер на модерации!</b>\n\n"
        f"📛 {e(data['name'])}\n"
        f"🌐 <code>{e(data['ip'])}</code>\n\n"
        "Используй /админ для проверки.",
    )


# ──────────────────────────────────────────
# /мой_сервер — управление своим сервером
# ──────────────────────────────────────────
@dp.message(Command("мой_сервер"))
async def cmd_my_server(message: Message):
    server = await db.get_any_server_by_owner(message.from_user.id)
    if not server:
        await message.answer(
            "❌ У тебя нет сервера.\n"
            "Создай его командой /создать"
        )
        return

    # Актуализируем онлайн-статус через approved-запрос (он сбрасывает просроченные)
    await db.get_approved_servers()
    server = await db.get_server_by_id(server["id"])

    text = server_card(server)

    # Кнопки управления показываем только для одобренных серверов
    if server["status"] == "approved":
        kb = manage_keyboard(server["id"], server["online"])
        await message.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="HTML")


# ──────────────────────────────────────────
# Callback: управление сервером (srv:*)
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("srv:"))
async def cb_manage_server(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    if len(parts) != 3 or not parts[2].isdigit():
        await callback.answer("❌ Некорректные данные.", show_alert=True)
        return

    action = parts[1]
    server_id = int(parts[2])
    server = await db.get_server_by_id(server_id)

    if not server or server["owner_id"] != callback.from_user.id:
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return

    # ── Включить ──
    if action == "on":
        await db.set_server_online(server_id)
        server = await db.get_server_by_id(server_id)
        await callback.message.edit_text(
            server_card(server),
            parse_mode="HTML",
            reply_markup=manage_keyboard(server_id, 1),
        )
        await callback.answer("🟢 Сервер включён на 1 час!")

    # ── Выключить ──
    elif action == "off":
        await db.set_server_offline(server_id)
        server = await db.get_server_by_id(server_id)
        await callback.message.edit_text(
            server_card(server),
            parse_mode="HTML",
            reply_markup=manage_keyboard(server_id, 0),
        )
        await callback.answer("⚫ Сервер выключен.")

    # ── Изменить пароль ──
    elif action == "pwd":
        await state.update_data(manage_server_id=server_id)
        await state.set_state(ChangePassword.waiting)
        await callback.message.answer(
            "🔑 Введи новый пароль для сервера\n"
            "(или напиши <code>нет</code>, чтобы убрать пароль):\n\n"
            "<i>Для отмены напиши /отмена</i>",
            parse_mode="HTML",
        )
        await callback.answer()

    else:
        await callback.answer("❌ Неизвестное действие.", show_alert=True)


@dp.message(ChangePassword.waiting)
async def change_password_step(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текст.")
        return

    data = await state.get_data()
    server_id = data.get("manage_server_id")
    if not server_id:
        await state.clear()
        await message.answer("❌ Что-то пошло не так. Попробуй снова через /мой_сервер")
        return

    server = await db.get_server_by_id(server_id)
    if not server or server["owner_id"] != message.from_user.id:
        await state.clear()
        await message.answer("❌ Нет доступа.")
        return

    new_password = message.text.strip()
    if new_password.lower() == "нет":
        new_password = ""

    await db.update_server_password(server_id, new_password)
    await state.clear()

    display = f"<code>{e(new_password)}</code>" if new_password else "нет"
    await message.answer(
        f"✅ Пароль обновлён: {display}\n\n"
        "Управление сервером: /мой_сервер",
        parse_mode="HTML",
    )


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
            f"🌐 <code>{e(s['ip'])}</code>\n"
            f"🔑 Пароль: <code>{e(s['password']) if s['password'] else 'нет'}</code>\n"
            f"👤 Владелец: <code>{s['owner_id']}</code>\n"
            f"🕐 Создан: {s['created_at']}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"mod:approve:{s['id']}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod:reject:{s['id']}"),
        ]])
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
            f"Управляйте им через /мой_сервер"
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
# /отмена — выход из любого FSM
# ──────────────────────────────────────────
@dp.message(Command("отмена"))
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer("Нечего отменять.")
        return
    await state.clear()
    await message.answer("🚫 Действие отменено.")


# ──────────────────────────────────────────
# Запуск
# ──────────────────────────────────────────
async def main():
    await db.init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 LostMiner бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
