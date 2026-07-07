import asyncio
import html
import logging
from datetime import datetime, timezone

from typing import Any, Awaitable, Callable
from backup import backup_loop
from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    TelegramObject,
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
    name        = State()
    description = State()
    ip          = State()
    password    = State()


class ChangePassword(StatesGroup):
    waiting = State()


class ChangeAvatar(StatesGroup):
    waiting = State()


class ServerBan(StatesGroup):
    waiting = State()   # ввод user_id для бана на сервере


class GlobalBan(StatesGroup):
    ban_id   = State()  # ввод user_id для глобального бана
    unban_id = State()  # ввод user_id для глобального разбана


# ──────────────────────────────────────────
# Middleware: глобальный бан
# ──────────────────────────────────────────
class GlobalBanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user and user.id != ADMIN_ID and await db.is_globally_banned(user.id):
            if isinstance(event, CallbackQuery):
                try:
                    await event.answer("🚫 Вы заблокированы в боте.", show_alert=True)
                except Exception:
                    pass
            elif isinstance(event, Message):
                try:
                    await event.answer("🚫 Вы заблокированы в боте администратором.")
                except Exception:
                    pass
            return  # не передаём дальше
        return await handler(event, data)


# ──────────────────────────────────────────
# Утилиты
# ──────────────────────────────────────────
def e(text: str) -> str:
    return html.escape(str(text))


def status_badge(online: int) -> str:
    return "🟢 Онлайн" if online else "⚫ Оффлайн"


def status_label(status: str) -> str:
    return {
        "pending":  "⏳ На модерации",
        "approved": "✅ Одобрен",
        "rejected": "❌ Отклонён",
    }.get(status, status)


def privacy_badge(is_private: int) -> str:
    return "🔒 Закрытый" if is_private else "🔓 Открытый"


async def notify_user(user_id: int, text: str, reply_markup=None):
    try:
        await bot.send_message(user_id, text, parse_mode="HTML", reply_markup=reply_markup)
    except Exception as exc:
        logger.warning("Не удалось уведомить %s: %s", user_id, exc)


def time_left(expires_at: str | None) -> str:
    if not expires_at:
        return ""
    try:
        exp   = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc)
        now   = datetime.now(timezone.utc)
        total = int((exp - now).total_seconds())
        if total <= 0:
            return "менее минуты"
        h, rem = divmod(total, 3600)
        m, s   = divmod(rem, 60)
        parts  = []
        if h: parts.append(f"{h} ч")
        if m: parts.append(f"{m} мин")
        if s and not h: parts.append(f"{s} сек")
        return " ".join(parts)
    except Exception:
        return ""


def _avatar_status_line(s) -> str:
    keys = s.keys()
    pending = s["avatar_pending_file_id"] if "avatar_pending_file_id" in keys else None
    approved = s["avatar_file_id"] if "avatar_file_id" in keys else None
    if pending:
        return "🖼 Аватарка: ⏳ на модерации"
    if approved:
        return "🖼 Аватарка: ✅ есть"
    return "🖼 Аватарка: нет"


def server_card(s) -> str:
    """Карточка сервера для владельца (пароль виден)."""
    online_line = status_badge(s["online"])
    if s["online"] and s["expires_at"]:
        left = time_left(s["expires_at"])
        if left:
            online_line += f"  ⏱ осталось: <b>{left}</b>"
    is_private = s["is_private"] if "is_private" in s.keys() else 0
    return (
        f"🖥 <b>{e(s['name'])}</b>\n"
        f"📝 {e(s['description'])}\n"
        f"🌐 <code>{e(s['ip'])}</code>\n"
        f"🔑 Пароль: <code>{e(s['password']) if s['password'] else 'нет'}</code>\n"
        f"📋 Статус: {status_label(s['status'])}\n"
        f"🔐 Тип: {privacy_badge(is_private)}\n"
        f"{_avatar_status_line(s)}\n"
        f"📶 {online_line}"
    )


def public_server_card(s, page: int, total: int) -> str:
    """Публичная карточка сервера (пароль скрыт) + счётчик страниц."""
    is_private = s["is_private"] if "is_private" in s.keys() else 0
    pwd_line   = "🔒 скрыт (требуется одобрение)" if is_private else ("🔒 скрыт" if s["password"] else "нет")
    return (
        f"🗂 <b>Серверы LostMiner</b>  <code>{page + 1} / {total}</code>\n\n"
        f"🖥 <b>{e(s['name'])}</b>  {privacy_badge(is_private)}\n"
        f"📝 {e(s['description'])}\n"
        f"🌐 <code>{e(s['ip'])}</code>\n"
        f"🔑 Пароль: {pwd_line}\n"
        f"📶 {status_badge(s['online'])}"
    )


# ──────────────────────────────────────────
# Reply-клавиатура (постоянные кнопки)
# ──────────────────────────────────────────
def main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🗂 Серверы"),       KeyboardButton(text="🛠 Мой сервер")],
        [KeyboardButton(text="➕ Создать сервер"), KeyboardButton(text="❌ Отмена")],
    ]
    if is_admin:
        rows.append([KeyboardButton(text="🔐 Админ"),   KeyboardButton(text="📋 Логи")])
        rows.append([KeyboardButton(text="🚫 Г-бан"),    KeyboardButton(text="✅ Г-разбан"),
                     KeyboardButton(text="📋 Бан-лист")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# ──────────────────────────────────────────
# Inline-клавиатуры
# ──────────────────────────────────────────

def srvlist_keyboard(
    page: int,
    total: int,
    server_id: int,
    subscribed: bool,
    has_password: bool,
    is_private: int,
    is_owner: bool,
) -> InlineKeyboardMarkup:
    """Клавиатура для списка серверов: навигация + действия."""
    # Навигационная строка
    left_cb  = f"srvpage:{page - 1}" if page > 0        else "srvpage:noop"
    right_cb = f"srvpage:{page + 1}" if page < total - 1 else "srvpage:noop"
    nav_row  = [
        InlineKeyboardButton(text="◀️",              callback_data=left_cb),
        InlineKeyboardButton(text=f"{page + 1} / {total}", callback_data="srvpage:noop"),
        InlineKeyboardButton(text="▶️",              callback_data=right_cb),
    ]

    rows = [nav_row]

    if is_owner:
        rows.append([InlineKeyboardButton(text="⚙️ Управление", callback_data=f"myserver:{server_id}")])
    else:
        sub_text = "🔕 Отписаться" if subscribed else "🔔 Подписаться"
        rows.append([InlineKeyboardButton(text=sub_text, callback_data=f"sub:{server_id}")])
        if has_password:
            pwd_label = "🔑 Запросить пароль" if is_private else "🔑 Узнать пароль"
            rows.append([InlineKeyboardButton(text=pwd_label, callback_data=f"getpwd:{server_id}")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def manage_keyboard(
    server_id: int,
    online: int,
    is_private: int,
    avatar_file_id: str | None = None,
    avatar_pending_file_id: str | None = None,
) -> InlineKeyboardMarkup:
    toggle_text  = "⚫ Выключить"    if online     else "🟢 Включить на 1 час"
    toggle_cb    = f"srv:off:{server_id}" if online else f"srv:on:{server_id}"
    privacy_text = "🔓 Сделать открытым" if is_private else "🔒 Закрыть сервер"
    if avatar_pending_file_id:
        avatar_text = "🖼 Аватарка (⏳ на модерации)"
    elif avatar_file_id:
        avatar_text = "🖼 Изменить аватарку"
    else:
        avatar_text = "🖼 Загрузить аватарку"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Изменить пароль",  callback_data=f"srv:pwd:{server_id}")],
        [InlineKeyboardButton(text=toggle_text,            callback_data=toggle_cb)],
        [InlineKeyboardButton(text=privacy_text,           callback_data=f"srv:toggleprivate:{server_id}")],
        [InlineKeyboardButton(text=avatar_text,            callback_data=f"srv:avatar:{server_id}")],
        [InlineKeyboardButton(text="🚫 Бан-лист сервера", callback_data=f"srv:banlist:{server_id}")],
        [InlineKeyboardButton(text="🗑 Удалить сервер",    callback_data=f"srv:del:{server_id}")],
    ])


def delete_keyboard(server_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"srv:delconfirm:{server_id}"),
        InlineKeyboardButton(text="❌ Отмена",       callback_data=f"srv:delcancel:{server_id}"),
    ]])


def rejected_keyboard(server_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Удалить сервер", callback_data=f"srv:del:{server_id}")],
    ])


def pwd_request_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Выдать пароль", callback_data=f"pwdreq:approve:{request_id}"),
        InlineKeyboardButton(text="❌ Отклонить",     callback_data=f"pwdreq:reject:{request_id}"),
    ]])


# ──────────────────────────────────────────
# Вспомогательная функция: отобразить страницу списка серверов
# ──────────────────────────────────────────
async def _show_server_page(
    uid: int,
    servers: list,
    page: int,
    message: Message | None = None,
    callback: CallbackQuery | None = None,
):
    """Отрисовать карточку сервера на странице page.
    message  — для нового сообщения (send)
    callback — для редактирования существующего (edit)
    """
    total      = len(servers)
    page       = max(0, min(page, total - 1))
    s          = servers[page]
    is_owner   = s["owner_id"] == uid
    is_private = s["is_private"] if "is_private" in s.keys() else 0
    subscribed = False if is_owner else await db.is_subscribed(uid, s["id"])
    has_pwd    = bool(s["password"])
    avatar_fid = s["avatar_file_id"] if "avatar_file_id" in s.keys() else None

    text = public_server_card(s, page, total)
    kb   = srvlist_keyboard(page, total, s["id"], subscribed, has_pwd, is_private, is_owner)

    if message:
        # Новое сообщение
        if avatar_fid:
            await message.answer_photo(avatar_fid, caption=text, parse_mode="HTML", reply_markup=kb)
        else:
            await message.answer(text, parse_mode="HTML", reply_markup=kb)
        return

    if not callback:
        return

    # Редактирование существующего сообщения
    cur_is_photo = bool(callback.message.photo)

    if avatar_fid:
        if cur_is_photo:
            # Меняем фото и подпись прямо в сообщении
            try:
                await callback.message.edit_media(
                    InputMediaPhoto(media=avatar_fid, caption=text, parse_mode="HTML"),
                    reply_markup=kb,
                )
            except Exception:
                pass
        else:
            # Было текстовое — удаляем и отправляем фото
            try:
                await callback.message.delete()
            except Exception:
                pass
            await bot.send_photo(
                callback.message.chat.id, avatar_fid,
                caption=text, parse_mode="HTML", reply_markup=kb,
            )
    else:
        if cur_is_photo:
            # Было фото — удаляем и отправляем текст
            try:
                await callback.message.delete()
            except Exception:
                pass
            await bot.send_message(
                callback.message.chat.id, text, parse_mode="HTML", reply_markup=kb,
            )
        else:
            # Оба текстовые — просто редактируем
            try:
                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
            except Exception:
                pass


# ──────────────────────────────────────────
# /start — регистрация
# ──────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await db.register_user(message.from_user.id, message.from_user.username)
    is_admin = message.from_user.id == ADMIN_ID
    admin_block = (
        "\n🔐 <b>Администрирование</b>\n"
        "/админ — модерация серверов\n"
        "/логи — журнал событий\n"
    ) if is_admin else ""
    await message.answer(
        "👋 Добро пожаловать в <b>LostMiner</b> — каталог игровых серверов!\n\n"
        "📋 <b>Команды:</b>\n\n"
        "🗂 <b>Серверы</b>\n"
        "/серверы — список всех одобренных серверов\n\n"
        "🛠 <b>Мой сервер</b>\n"
        "/создать — добавить свой сервер\n"
        "/мой_сервер — управление сервером (вкл/выкл, тип, пароль)\n\n"
        "🔧 <b>Прочее</b>\n"
        "/отмена — отменить текущее действие\n"
        + admin_block +
        "\n<i>Кнопки быстрого доступа появились внизу экрана.</i>",
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin),
    )


# ──────────────────────────────────────────
# /серверы — список одобренных серверов (пагинация)
# ──────────────────────────────────────────
async def _cmd_servers_logic(message: Message):
    servers = await db.get_approved_servers()
    if not servers:
        await message.answer("📭 Пока нет ни одного одобренного сервера.")
        return
    await _show_server_page(message.from_user.id, servers, 0, message=message)


@dp.message(Command("серверы"))
async def cmd_servers(message: Message):
    await _cmd_servers_logic(message)


# ──────────────────────────────────────────
# Callback: пагинация списка серверов (srvpage:<page>)
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("srvpage:"))
async def cb_srvpage(callback: CallbackQuery):
    page_str = callback.data.split(":", 1)[1]
    if page_str == "noop":
        await callback.answer()
        return

    if not page_str.lstrip("-").isdigit():
        await callback.answer("❌ Некорректные данные.", show_alert=True)
        return

    page    = int(page_str)
    servers = await db.get_approved_servers()
    if not servers:
        await callback.answer("📭 Серверов нет.", show_alert=True)
        return

    await callback.answer()
    await _show_server_page(callback.from_user.id, servers, page, callback=callback)


# ──────────────────────────────────────────
# Callback: кнопка «Управление» из списка серверов
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("myserver:"))
async def cb_myserver_shortcut(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("Управляй своим сервером через /мой_сервер")


# ──────────────────────────────────────────
# Callback: подписка/отписка (sub:<server_id>)
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("sub:"))
async def cb_subscribe(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer("❌ Некорректные данные.", show_alert=True)
        return

    server_id  = int(parts[1])
    server     = await db.get_server_by_id(server_id)
    if not server or server["status"] != "approved":
        await callback.answer("❌ Сервер не найден.", show_alert=True)
        return

    uid = callback.from_user.id
    if server["owner_id"] == uid:
        await callback.answer("❌ Нельзя подписаться на свой сервер.", show_alert=True)
        return

    currently = await db.is_subscribed(uid, server_id)
    if currently:
        await db.unsubscribe(uid, server_id)
        await db.add_log("unsubscribed", uid, server_id,
                         f"@{callback.from_user.username or uid} отписался от «{server['name']}»")
        await callback.answer("🔕 Вы отписались от сервера.")
        subscribed = False
    else:
        await db.subscribe(uid, server_id)
        await db.add_log("subscribed", uid, server_id,
                         f"@{callback.from_user.username or uid} подписался на «{server['name']}»")
        await callback.answer("🔔 Вы подписались! Получите уведомление когда сервер включится.")
        subscribed = True

    # Перерисовываем ту же страницу через список серверов
    servers = await db.get_approved_servers()
    if not servers:
        return
    # Найдём текущий индекс этого сервера
    ids    = [s["id"] for s in servers]
    page   = ids.index(server_id) if server_id in ids else 0
    await _show_server_page(uid, servers, page, callback=callback)


# ──────────────────────────────────────────
# Callback: получить / запросить пароль (getpwd:<server_id>)
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("getpwd:"))
async def cb_get_password(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer("❌ Некорректные данные.", show_alert=True)
        return

    server_id = int(parts[1])
    server    = await db.get_server_by_id(server_id)
    if not server or server["status"] != "approved":
        await callback.answer("❌ Сервер не найден.", show_alert=True)
        return

    if not server["password"]:
        await callback.answer("У этого сервера нет пароля.", show_alert=True)
        return

    uid        = callback.from_user.id
    uname      = f"@{callback.from_user.username}" if callback.from_user.username else f"id:{uid}"
    is_private = server["is_private"] if "is_private" in server.keys() else 0

    # ── Проверка серверного бана ──
    if await db.is_server_banned(server_id, uid):
        await callback.answer("🚫 Вы заблокированы владельцем этого сервера.", show_alert=True)
        return

    # ── Открытый сервер: сразу отправляем пароль ──
    if not is_private:
        try:
            await bot.send_message(
                uid,
                f"🔑 Пароль сервера <b>«{e(server['name'])}»</b>:\n"
                f"<code>{e(server['password'])}</code>\n\n"
                "<i>Рекомендуем удалить это сообщение после прочтения.</i>",
                parse_mode="HTML",
            )
            await callback.answer("✅ Пароль отправлен в личные сообщения.")
        except Exception:
            await callback.answer(
                "❌ Не удалось отправить пароль. Напишите боту в личку и попробуйте снова.",
                show_alert=True,
            )
            return

        await notify_user(
            server["owner_id"],
            f"🔐 <b>Кто-то запросил пароль вашего сервера!</b>\n\n"
            f"🖥 Сервер: <b>{e(server['name'])}</b>\n"
            f"👤 Пользователь: {e(uname)}\n"
            f"🆔 ID: <code>{uid}</code>",
        )
        await db.add_log("password_requested", uid, server_id,
                         f"{uname} получил пароль сервера «{server['name']}»")
        return

    # ── Закрытый сервер: создаём запрос ──
    existing = await db.get_pending_pwd_request(server_id, uid)
    if existing:
        await callback.answer(
            "⏳ Запрос уже отправлен. Ожидайте одобрения владельца.",
            show_alert=True,
        )
        return

    req_id = await db.create_pwd_request(server_id, uid)
    await callback.answer("📨 Запрос отправлен. Ожидайте одобрения владельца.")

    await notify_user(
        server["owner_id"],
        f"🔐 <b>Запрос пароля закрытого сервера!</b>\n\n"
        f"🖥 Сервер: <b>{e(server['name'])}</b>\n"
        f"👤 Пользователь: {e(uname)}\n"
        f"🆔 ID: <code>{uid}</code>\n\n"
        "Выдать пароль этому пользователю?",
        reply_markup=pwd_request_keyboard(req_id),
    )
    await db.add_log("pwd_request_sent", uid, server_id,
                     f"{uname} запросил пароль закрытого сервера «{server['name']}»")


# ──────────────────────────────────────────
# Callback: владелец одобряет/отклоняет запрос пароля
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("pwdreq:"))
async def cb_pwd_request(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 3 or parts[1] not in ("approve", "reject") or not parts[2].isdigit():
        await callback.answer("❌ Некорректные данные.", show_alert=True)
        return

    action     = parts[1]
    request_id = int(parts[2])
    req        = await db.get_pwd_request(request_id)

    if not req:
        await callback.answer("❌ Запрос не найден.", show_alert=True)
        return
    if req["status"] != "pending":
        await callback.answer("Этот запрос уже обработан.", show_alert=True)
        return

    server = await db.get_server_by_id(req["server_id"])
    if not server or server["owner_id"] != callback.from_user.id:
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return

    requester_id = req["requester_id"]

    if action == "approve":
        # Сначала доставляем пароль — только при успехе меняем статус
        try:
            await bot.send_message(
                requester_id,
                f"✅ <b>Владелец выдал вам пароль!</b>\n\n"
                f"🖥 Сервер: <b>{e(server['name'])}</b>\n"
                f"🔑 Пароль: <code>{e(server['password'])}</code>\n\n"
                "<i>Рекомендуем удалить это сообщение после прочтения.</i>",
                parse_mode="HTML",
            )
        except Exception:
            await callback.message.edit_text(
                f"⚠️ Не удалось доставить пароль пользователю <code>{requester_id}</code> — "
                f"возможно он заблокировал бота.\n\n"
                f"Запрос остаётся активным, попробуй выдать пароль снова.",
                parse_mode="HTML",
                reply_markup=pwd_request_keyboard(request_id),
            )
            await callback.answer("❌ Не удалось доставить пароль.", show_alert=True)
            return

        await db.resolve_pwd_request(request_id, "approved")
        await db.add_log("pwd_request_approved", callback.from_user.id, server["id"],
                         f"Запрос пароля #{request_id} для сервера «{server['name']}» одобрен")
        await callback.message.edit_text(
            f"✅ Пароль выдан пользователю <code>{requester_id}</code>.",
            parse_mode="HTML",
        )
        await callback.answer("✅ Пароль выдан.")

    else:  # reject
        await db.resolve_pwd_request(request_id, "rejected")
        await db.add_log("pwd_request_rejected", callback.from_user.id, server["id"],
                         f"Запрос пароля #{request_id} для сервера «{server['name']}» отклонён")
        await notify_user(
            requester_id,
            f"❌ <b>Владелец отклонил ваш запрос пароля.</b>\n\n"
            f"🖥 Сервер: <b>{e(server['name'])}</b>",
        )
        await callback.message.edit_text(
            f"❌ Запрос пароля от <code>{requester_id}</code> отклонён.",
            parse_mode="HTML",
        )
        await callback.answer("❌ Запрос отклонён.")


# ──────────────────────────────────────────
# /создать — пошаговое создание сервера
# ──────────────────────────────────────────
async def _cmd_create_logic(message: Message, state: FSMContext):
    await db.register_user(message.from_user.id, message.from_user.username)

    existing = await db.get_active_server_by_owner(message.from_user.id)
    if existing:
        await message.answer(
            "❌ У тебя уже есть активный сервер. Создать можно только один.\n\n"
            "Управляй им через /мой_сервер"
        )
        return

    await db.delete_rejected_servers(message.from_user.id)
    await state.set_state(CreateServer.name)
    await message.answer(
        "🛠 <b>Создание сервера</b>\n\n"
        "Шаг 1/4 — Введи <b>название</b> сервера:\n"
        "<i>Для отмены нажми кнопку ❌ Отмена или напиши /отмена</i>",
        parse_mode="HTML",
    )


@dp.message(Command("создать"))
async def cmd_create(message: Message, state: FSMContext):
    await _cmd_create_logic(message, state)


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

    data     = await state.get_data()
    password = message.text.strip()
    if password.lower() == "нет":
        password = ""

    server_id = await db.create_server(
        owner_id    = message.from_user.id,
        name        = data["name"],
        description = data["description"],
        ip          = data["ip"],
        password    = password,
    )
    await state.clear()

    await db.add_log(
        "server_created", message.from_user.id, server_id,
        f"@{message.from_user.username or message.from_user.id} создал сервер «{data['name']}»",
    )

    await message.answer(
        "✅ <b>Сервер отправлен на модерацию!</b>\n\n"
        f"📛 Название: {e(data['name'])}\n"
        f"🌐 Адрес: <code>{e(data['ip'])}</code>\n\n"
        "Ожидайте одобрения администратора.",
        parse_mode="HTML",
    )
    await notify_user(
        ADMIN_ID,
        f"🔔 <b>Новый сервер на модерации!</b>\n\n"
        f"📛 {e(data['name'])}\n"
        f"🌐 <code>{e(data['ip'])}</code>\n\n"
        "Используй /админ для проверки.",
    )


# ──────────────────────────────────────────
# /мой_сервер — управление своим сервером
# ──────────────────────────────────────────
async def _cmd_my_server_logic(message: Message):
    server = await db.get_any_server_by_owner(message.from_user.id)
    if not server:
        await message.answer("❌ У тебя нет сервера.\nСоздай его командой /создать")
        return

    server     = await db.get_server_by_id(server["id"])
    keys       = server.keys()
    is_private = server["is_private"] if "is_private" in keys else 0
    avatar_fid = server["avatar_file_id"] if "avatar_file_id" in keys else None
    avatar_pid = server["avatar_pending_file_id"] if "avatar_pending_file_id" in keys else None

    # Показываем одобренную аватарку отдельным фото выше карточки
    if avatar_fid:
        try:
            await bot.send_photo(message.chat.id, avatar_fid,
                                 caption="🖼 <b>Аватарка сервера</b>", parse_mode="HTML")
        except Exception:
            pass

    text = server_card(server)
    if server["status"] == "approved":
        kb = manage_keyboard(server["id"], server["online"], is_private, avatar_fid, avatar_pid)
    elif server["status"] == "rejected":
        kb = rejected_keyboard(server["id"])
    else:
        kb = None

    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@dp.message(Command("мой_сервер"))
async def cmd_my_server(message: Message):
    await _cmd_my_server_logic(message)


# ──────────────────────────────────────────
# Callback: управление сервером (srv:*)  — только для владельца
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("srv:"))
async def cb_manage_server(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    if len(parts) != 3 or not parts[2].isdigit():
        await callback.answer("❌ Некорректные данные.", show_alert=True)
        return

    action    = parts[1]
    server_id = int(parts[2])
    server    = await db.get_server_by_id(server_id)

    if not server or server["owner_id"] != callback.from_user.id:
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return

    keys       = server.keys()
    is_private = server["is_private"] if "is_private" in keys else 0
    avatar_fid = server["avatar_file_id"] if "avatar_file_id" in keys else None
    avatar_pid = server["avatar_pending_file_id"] if "avatar_pending_file_id" in keys else None

    def _mkb(srv):
        k = srv.keys()
        return manage_keyboard(
            srv["id"], srv["online"],
            srv["is_private"] if "is_private" in k else 0,
            srv["avatar_file_id"] if "avatar_file_id" in k else None,
            srv["avatar_pending_file_id"] if "avatar_pending_file_id" in k else None,
        )

    # ── Включить ──
    if action == "on":
        await db.set_server_online(server_id)
        server = await db.get_server_by_id(server_id)
        await callback.message.edit_text(
            server_card(server), parse_mode="HTML", reply_markup=_mkb(server),
        )
        await callback.answer("🟢 Сервер включён на 1 час!")
        await db.add_log("server_online", callback.from_user.id, server_id,
                         f"Сервер «{server['name']}» включён владельцем")

        is_private = server["is_private"] if "is_private" in server.keys() else 0
        subscribers = await db.get_subscribers(server_id)
        if subscribers:
            pwd_hint = "🔑 Запросить пароль — кнопка в /серверы" if is_private \
                       else ("🔒 скрыт — кнопка в /серверы" if server["password"] else "нет")
            notify_text = (
                f"🟢 <b>Сервер «{e(server['name'])}» сейчас онлайн!</b>\n\n"
                f"🌐 <code>{e(server['ip'])}</code>\n"
                f"🔑 Пароль: {pwd_hint}\n\n"
                f"⏱ Будет онлайн ещё 1 час."
            )
            for uid in subscribers:
                await notify_user(uid, notify_text)

    # ── Выключить ──
    elif action == "off":
        await db.set_server_offline(server_id)
        server = await db.get_server_by_id(server_id)
        await callback.message.edit_text(
            server_card(server), parse_mode="HTML", reply_markup=_mkb(server),
        )
        await callback.answer("⚫ Сервер выключен.")
        await db.add_log("server_offline", callback.from_user.id, server_id,
                         f"Сервер «{server['name']}» выключен владельцем")

    # ── Изменить пароль ──
    elif action == "pwd":
        await state.update_data(manage_server_id=server_id)
        await state.set_state(ChangePassword.waiting)
        await callback.message.answer(
            "🔑 Введи новый пароль для сервера\n"
            "(или напиши <code>нет</code>, чтобы убрать пароль):\n\n"
            "<i>Для отмены нажми кнопку ❌ Отмена или напиши /отмена</i>",
            parse_mode="HTML",
        )
        await callback.answer()

    # ── Переключить тип (открытый/закрытый) ──
    elif action == "toggleprivate":
        new_private = await db.toggle_server_private(server_id)
        server      = await db.get_server_by_id(server_id)
        label       = "закрытым 🔒" if new_private else "открытым 🔓"
        await callback.message.edit_text(
            server_card(server), parse_mode="HTML", reply_markup=_mkb(server),
        )
        await callback.answer(f"Сервер теперь {label}.")
        await db.add_log("server_type_changed", callback.from_user.id, server_id,
                         f"Сервер «{server['name']}» стал {'закрытым' if new_private else 'открытым'}")

    # ── Бан-лист сервера ──
    elif action == "banlist":
        bans = await db.get_server_bans(server_id)
        rows = []
        if bans:
            for ban in bans:
                dt = str(ban["created_at"])[:10]
                rows.append([InlineKeyboardButton(
                    text=f"🔓 Разбанить {ban['banned_user_id']}  ({dt})",
                    callback_data=f"srvunban:{ban['id']}",
                )])
        rows.append([InlineKeyboardButton(
            text="➕ Забанить по ID",
            callback_data=f"srv:ban:{server_id}",
        )])
        rows.append([InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"srv:back:{server_id}",
        )])
        header = f"🚫 <b>Бан-лист сервера «{e(server['name'])}»</b>\n\n"
        if bans:
            header += f"Забанено пользователей: <b>{len(bans)}</b>"
        else:
            header += "Забаненных нет."
        await callback.message.edit_text(
            header, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )
        await callback.answer()

    # ── Забанить по ID ──
    elif action == "ban":
        await state.update_data(manage_server_id=server_id)
        await state.set_state(ServerBan.waiting)
        await callback.message.answer(
            f"🚫 <b>Бан пользователя на сервере «{e(server['name'])}»</b>\n\n"
            "Отправь <b>Telegram ID</b> пользователя которого хочешь забанить:\n"
            "<i>Для отмены нажми ❌ Отмена или /отмена</i>",
            parse_mode="HTML",
        )
        await callback.answer()

    # ── Назад в главное меню управления ──
    elif action == "back":
        server = await db.get_server_by_id(server_id)
        await callback.message.edit_text(
            server_card(server), parse_mode="HTML", reply_markup=_mkb(server),
        )
        await callback.answer()

    # ── Загрузить/изменить аватарку ──
    elif action == "avatar":
        # Блокируем повторную загрузку пока предыдущая на модерации
        if avatar_pid:
            await callback.answer(
                "⏳ Аватарка уже на модерации. Дождись решения администратора.",
                show_alert=True,
            )
            return
        await state.update_data(manage_server_id=server_id)
        await state.set_state(ChangeAvatar.waiting)
        await callback.message.answer(
            "🖼 <b>Загрузка аватарки</b>\n\n"
            "Отправь фотографию — она будет отправлена на модерацию.\n"
            "После одобрения аватарка появится на карточке сервера.\n\n"
            "<i>Для отмены нажми кнопку ❌ Отмена или напиши /отмена</i>",
            parse_mode="HTML",
        )
        await callback.answer()

    # ── Удалить: запрос подтверждения ──
    elif action == "del":
        await callback.message.edit_text(
            f"🗑 <b>Удалить сервер «{e(server['name'])}»?</b>\n\n"
            "Это действие необратимо. Все подписчики и запросы пароля будут удалены.",
            parse_mode="HTML",
            reply_markup=delete_keyboard(server_id),
        )
        await callback.answer()

    # ── Удалить: подтверждение ──
    elif action == "delconfirm":
        name    = server["name"]
        deleted = await db.delete_server(server_id, callback.from_user.id)
        if deleted:
            await db.add_log("server_deleted", callback.from_user.id, server_id,
                             f"Сервер «{name}» удалён владельцем")
            await callback.message.edit_text(
                f"🗑 Сервер <b>«{e(name)}»</b> удалён.\n\n"
                "Ты можешь создать новый сервер командой /создать",
                parse_mode="HTML",
            )
            await callback.answer("✅ Сервер удалён.")
        else:
            await callback.answer("❌ Не удалось удалить сервер.", show_alert=True)

    # ── Удалить: отмена ──
    elif action == "delcancel":
        if server["status"] == "approved":
            kb = _mkb(server)
        elif server["status"] == "rejected":
            kb = rejected_keyboard(server_id)
        else:
            kb = None
        await callback.message.edit_text(server_card(server), parse_mode="HTML", reply_markup=kb)
        await callback.answer("Удаление отменено.")

    else:
        await callback.answer("❌ Неизвестное действие.", show_alert=True)


@dp.message(ChangePassword.waiting)
async def change_password_step(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текст.")
        return

    data      = await state.get_data()
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
    await db.add_log("password_changed", message.from_user.id, server_id,
                     f"Пароль сервера «{server['name']}» изменён")
    await state.clear()

    display = f"<code>{e(new_password)}</code>" if new_password else "нет"
    await message.answer(
        f"✅ Пароль обновлён: {display}\n\n"
        "Управление сервером: /мой_сервер",
        parse_mode="HTML",
    )


# ──────────────────────────────────────────
# FSM: бан пользователя на сервере (ServerBan.waiting)
# ──────────────────────────────────────────
@dp.message(ServerBan.waiting)
async def server_ban_step(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().lstrip("-").isdigit():
        await message.answer("❌ Введи числовой Telegram ID. Попробуй ещё раз:")
        return

    target_id = int(message.text.strip())
    data      = await state.get_data()
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

    if target_id == message.from_user.id:
        await message.answer("❌ Нельзя забанить самого себя.")
        return
    if target_id == ADMIN_ID:
        await message.answer("❌ Нельзя забанить администратора.")
        return

    ok = await db.ban_server_user(server_id, target_id)
    await state.clear()
    if ok:
        await db.add_log("server_ban", message.from_user.id, server_id,
                         f"Пользователь {target_id} забанен на сервере «{server['name']}»")
        await message.answer(
            f"🚫 Пользователь <code>{target_id}</code> забанен на сервере <b>«{e(server['name'])}»</b>.\n"
            "Он не сможет запрашивать пароль.\n\n"
            "Бан-лист: /мой_сервер → 🚫 Бан-лист сервера",
            parse_mode="HTML",
        )
        # Уведомляем забаненного
        await notify_user(
            target_id,
            f"🚫 Вы были заблокированы на сервере <b>«{e(server['name'])}»</b>.\n"
            "Вы больше не можете запрашивать пароль этого сервера.",
        )
    else:
        await message.answer(f"⚠️ Пользователь <code>{target_id}</code> уже забанен на этом сервере.",
                             parse_mode="HTML")


# ──────────────────────────────────────────
# Callback: разбан пользователя на сервере (srvunban:<ban_id>)
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("srvunban:"))
async def cb_srv_unban(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer("❌ Некорректные данные.", show_alert=True)
        return

    ban_id = int(parts[1])
    ban    = await db.get_server_ban_by_id(ban_id)
    if not ban:
        await callback.answer("Запись не найдена.", show_alert=True)
        return

    server = await db.get_server_by_id(ban["server_id"])
    if not server or server["owner_id"] != callback.from_user.id:
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return

    result = await db.unban_server_user_by_ban_id(ban_id)
    if result:
        server_id, user_id = result
        await db.add_log("server_unban", callback.from_user.id, server_id,
                         f"Пользователь {user_id} разбанен на сервере «{server['name']}»")
        await notify_user(
            user_id,
            f"✅ Вы были разблокированы на сервере <b>«{e(server['name'])}»</b>.\n"
            "Теперь вы снова можете запрашивать пароль.",
        )

    # Перерисовываем бан-лист
    bans = await db.get_server_bans(server["id"])
    rows = []
    for b in bans:
        dt = str(b["created_at"])[:10]
        rows.append([InlineKeyboardButton(
            text=f"🔓 Разбанить {b['banned_user_id']}  ({dt})",
            callback_data=f"srvunban:{b['id']}",
        )])
    rows.append([InlineKeyboardButton(text="➕ Забанить по ID",
                                      callback_data=f"srv:ban:{server['id']}")])
    rows.append([InlineKeyboardButton(text="◀️ Назад",
                                      callback_data=f"srv:back:{server['id']}")])
    header = f"🚫 <b>Бан-лист сервера «{e(server['name'])}»</b>\n\n"
    header += f"Забанено пользователей: <b>{len(bans)}</b>" if bans else "Забаненных нет."
    try:
        await callback.message.edit_text(
            header, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )
    except Exception:
        pass
    await callback.answer("✅ Разбанен.")


# ──────────────────────────────────────────
# FSM: загрузка аватарки (ChangeAvatar.waiting)
# ──────────────────────────────────────────
@dp.message(ChangeAvatar.waiting)
async def change_avatar_step(message: Message, state: FSMContext):
    # Принимаем только фото
    if not message.photo:
        await message.answer(
            "❌ Пожалуйста, отправь именно <b>фотографию</b> (не файл).\n"
            "Для отмены нажми ❌ Отмена.",
            parse_mode="HTML",
        )
        return

    data      = await state.get_data()
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

    # Берём наибольшее разрешение
    file_id = message.photo[-1].file_id
    await db.set_avatar_pending(server_id, file_id)
    await db.add_log("avatar_uploaded", message.from_user.id, server_id,
                     f"Аватарка сервера «{server['name']}» отправлена на модерацию")
    await state.clear()

    await message.answer(
        "📨 <b>Аватарка отправлена на модерацию!</b>\n\n"
        "После одобрения администратором она появится на карточке сервера.",
        parse_mode="HTML",
    )

    # Уведомляем админа с предпросмотром
    try:
        await bot.send_photo(
            ADMIN_ID,
            file_id,
            caption=(
                f"🖼 <b>Новая аватарка на модерации!</b>\n\n"
                f"🖥 Сервер: <b>{e(server['name'])}</b>\n"
                f"👤 Владелец: <code>{server['owner_id']}</code>\n\n"
                "Используй /админ для проверки."
            ),
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.warning("Не удалось уведомить админа об аватарке: %s", exc)


# ──────────────────────────────────────────
# /админ — панель модерации
# ──────────────────────────────────────────
async def _cmd_admin_logic(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У тебя нет прав для этой команды.")
        return

    pending_servers  = await db.get_pending_servers()
    pending_avatars  = await db.get_servers_with_pending_avatars()
    has_anything     = bool(pending_servers or pending_avatars)

    if not has_anything:
        await message.answer("✅ Нет заявок на модерации.")
        return

    # ── Серверы ──
    if pending_servers:
        await message.answer(
            f"🔍 <b>Серверы на модерации: {len(pending_servers)}</b>", parse_mode="HTML"
        )
        for s in pending_servers:
            text = (
                f"📛 <b>{e(s['name'])}</b>\n"
                f"📝 {e(s['description'])}\n"
                f"🌐 <code>{e(s['ip'])}</code>\n"
                f"🔑 Пароль: <code>{e(s['password']) if s['password'] else 'нет'}</code>\n"
                f"👤 Владелец: <code>{s['owner_id']}</code>\n"
                f"🕐 Создан: {s['created_at']}"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✅ Одобрить",  callback_data=f"mod:approve:{s['id']}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod:reject:{s['id']}"),
            ]])
            await message.answer(text, parse_mode="HTML", reply_markup=kb)

    # ── Аватарки ──
    if pending_avatars:
        await message.answer(
            f"🖼 <b>Аватарки на модерации: {len(pending_avatars)}</b>", parse_mode="HTML"
        )
        for s in pending_avatars:
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✅ Одобрить",  callback_data=f"avatarmod:approve:{s['id']}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"avatarmod:reject:{s['id']}"),
            ]])
            try:
                await bot.send_photo(
                    message.chat.id,
                    s["avatar_pending_file_id"],
                    caption=(
                        f"🖼 Аватарка сервера <b>«{e(s['name'])}»</b>\n"
                        f"👤 Владелец: <code>{s['owner_id']}</code>"
                    ),
                    parse_mode="HTML",
                    reply_markup=kb,
                )
            except Exception:
                await message.answer(
                    f"⚠️ Не удалось загрузить аватарку сервера «{e(s['name'])}».",
                    parse_mode="HTML",
                    reply_markup=kb,
                )


@dp.message(Command("админ"))
async def cmd_admin(message: Message):
    await _cmd_admin_logic(message)


@dp.callback_query(F.data.startswith("mod:"))
async def cb_moderate(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 3 or parts[1] not in ("approve", "reject") or not parts[2].isdigit():
        await callback.answer("❌ Некорректные данные.", show_alert=True)
        return

    action    = parts[1]
    server_id = int(parts[2])
    server    = await db.get_server_by_id(server_id)

    if not server:
        await callback.answer("Сервер не найден.", show_alert=True)
        return

    if action == "approve":
        await db.set_server_status(server_id, "approved")
        await db.add_log("server_approved", callback.from_user.id, server_id,
                         f"Сервер «{server['name']}» одобрен администратором")
        await callback.message.edit_text(
            f"✅ Сервер <b>«{e(server['name'])}»</b> одобрен.", parse_mode="HTML"
        )
        await callback.answer()
        await notify_user(
            server["owner_id"],
            f"✅ <b>Ваш сервер «{e(server['name'])}» одобрен!</b>\n"
            f"Теперь он виден в списке /серверы\n"
            f"Управляйте им через /мой_сервер",
        )
    else:
        await db.set_server_status(server_id, "rejected")
        await db.add_log("server_rejected", callback.from_user.id, server_id,
                         f"Сервер «{server['name']}» отклонён администратором")
        await callback.message.edit_text(
            f"❌ Сервер <b>«{e(server['name'])}»</b> отклонён.", parse_mode="HTML"
        )
        await callback.answer()
        await notify_user(
            server["owner_id"],
            f"❌ <b>Ваш сервер «{e(server['name'])}» отклонён.</b>\n\n"
            f"Удали его и создай новый командой /создать",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🗑 Удалить сервер",
                                      callback_data=f"srv:del:{server_id}")],
            ]),
        )


# ──────────────────────────────────────────
# Callback: модерация аватарок (avatarmod:approve/reject:<server_id>)
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("avatarmod:"))
async def cb_avatar_moderate(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 3 or parts[1] not in ("approve", "reject") or not parts[2].isdigit():
        await callback.answer("❌ Некорректные данные.", show_alert=True)
        return

    action    = parts[1]
    server_id = int(parts[2])
    server    = await db.get_server_by_id(server_id)

    if not server:
        await callback.answer("Сервер не найден.", show_alert=True)
        return

    keys       = server.keys()
    avatar_pid = server["avatar_pending_file_id"] if "avatar_pending_file_id" in keys else None
    if not avatar_pid:
        await callback.answer("Аватарка уже обработана.", show_alert=True)
        return

    if action == "approve":
        await db.approve_avatar(server_id)
        await db.add_log("avatar_approved", callback.from_user.id, server_id,
                         f"Аватарка сервера «{server['name']}» одобрена")
        try:
            await callback.message.edit_caption(
                caption=f"✅ Аватарка сервера <b>«{e(server['name'])}»</b> одобрена.",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await callback.answer("✅ Аватарка одобрена.")
        await notify_user(
            server["owner_id"],
            f"✅ <b>Аватарка вашего сервера одобрена!</b>\n\n"
            f"🖥 Сервер: <b>{e(server['name'])}</b>\n"
            "Она теперь отображается в /мой_сервер.",
        )

    else:  # reject
        await db.reject_avatar(server_id)
        await db.add_log("avatar_rejected", callback.from_user.id, server_id,
                         f"Аватарка сервера «{server['name']}» отклонена")
        try:
            await callback.message.edit_caption(
                caption=f"❌ Аватарка сервера <b>«{e(server['name'])}»</b> отклонена.",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await callback.answer("❌ Аватарка отклонена.")
        await notify_user(
            server["owner_id"],
            f"❌ <b>Аватарка вашего сервера отклонена.</b>\n\n"
            f"🖥 Сервер: <b>{e(server['name'])}</b>\n"
            "Ты можешь загрузить другую через /мой_сервер.",
        )


# ──────────────────────────────────────────
# Команды глобального бана (только ADMIN_ID)
# ──────────────────────────────────────────
async def _do_global_ban(message: Message, state: FSMContext, target_id: int):
    if target_id == ADMIN_ID:
        await message.answer("❌ Нельзя забанить администратора.")
        return
    ok = await db.ban_user_globally(target_id)
    await state.clear()
    if ok:
        await db.add_log("global_ban", message.from_user.id, None,
                         f"Пользователь {target_id} глобально забанен")
        await message.answer(f"🚫 Пользователь <code>{target_id}</code> глобально забанен.",
                             parse_mode="HTML")
        await notify_user(target_id, "🚫 <b>Вы заблокированы в боте администратором.</b>")
    else:
        await message.answer(f"⚠️ Пользователь <code>{target_id}</code> уже заблокирован.",
                             parse_mode="HTML")


async def _do_global_unban(message: Message, state: FSMContext, target_id: int):
    ok = await db.unban_user_globally(target_id)
    await state.clear()
    if ok:
        await db.add_log("global_unban", message.from_user.id, None,
                         f"Пользователь {target_id} глобально разбанен")
        await message.answer(f"✅ Пользователь <code>{target_id}</code> разбанен.",
                             parse_mode="HTML")
        await notify_user(target_id, "✅ <b>Ваш бан снят. Вы снова можете пользоваться ботом.</b>")
    else:
        await message.answer(f"⚠️ Пользователь <code>{target_id}</code> не был заблокирован.",
                             parse_mode="HTML")


@dp.message(Command("бан"))
async def cmd_ban(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У тебя нет прав для этой команды.")
        return
    # /бан 123456 — с аргументом
    args = message.text.split(maxsplit=1)
    if len(args) == 2 and args[1].lstrip("-").isdigit():
        await _do_global_ban(message, state, int(args[1]))
    else:
        await state.set_state(GlobalBan.ban_id)
        await message.answer(
            "🚫 <b>Глобальный бан</b>\n\nВведи Telegram ID пользователя:\n"
            "<i>Для отмены: /отмена</i>",
            parse_mode="HTML",
        )


@dp.message(Command("разбан"))
async def cmd_unban(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У тебя нет прав для этой команды.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) == 2 and args[1].lstrip("-").isdigit():
        await _do_global_unban(message, state, int(args[1]))
    else:
        await state.set_state(GlobalBan.unban_id)
        await message.answer(
            "✅ <b>Глобальный разбан</b>\n\nВведи Telegram ID пользователя:\n"
            "<i>Для отмены: /отмена</i>",
            parse_mode="HTML",
        )


@dp.message(Command("банлист"))
async def cmd_banlist(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У тебя нет прав для этой команды.")
        return
    await _show_global_banlist(message)


async def _show_global_banlist(message: Message):
    bans = await db.get_global_bans()
    if not bans:
        await message.answer("✅ Глобальный бан-лист пуст.")
        return
    lines = [f"🚫 <b>Глобальный бан-лист ({len(bans)}):</b>\n"]
    for b in bans:
        dt = str(b["created_at"])[:10]
        lines.append(f"• <code>{b['user_id']}</code>  с {dt}")
    await message.answer("\n".join(lines), parse_mode="HTML")


# ── FSM: ввод ID для глобального бана/разбана ──
@dp.message(GlobalBan.ban_id)
async def global_ban_id_step(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().lstrip("-").isdigit():
        await message.answer("❌ Введи числовой Telegram ID:")
        return
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    await _do_global_ban(message, state, int(message.text.strip()))


@dp.message(GlobalBan.unban_id)
async def global_unban_id_step(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().lstrip("-").isdigit():
        await message.answer("❌ Введи числовой Telegram ID:")
        return
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    await _do_global_unban(message, state, int(message.text.strip()))


# ──────────────────────────────────────────
# /логи — журнал событий
# ──────────────────────────────────────────
async def _cmd_logs_logic(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У тебя нет прав для этой команды.")
        return

    logs = await db.get_logs(40)
    if not logs:
        await message.answer("📋 Журнал пуст.")
        return

    lines = ["📋 <b>Журнал событий (последние 40):</b>\n"]
    for log in logs:
        label  = db.LOG_LABELS.get(log["event"], log["event"])
        dt     = str(log["created_at"])[:16]
        actor  = f"id:{log['actor_id']}" if log["actor_id"] else "—"
        srv    = f" | сервер #{log['server_id']}" if log["server_id"] else ""
        detail = f"\n   └ {e(log['details'])}" if log["details"] else ""
        lines.append(f"<code>{dt}</code> {label}\n   👤 {actor}{srv}{detail}")

    text = "\n\n".join(lines)
    if len(text) > 4000:
        text = text[:3990] + "\n\n<i>...обрезано</i>"

    await message.answer(text, parse_mode="HTML")


@dp.message(Command("логи"))
async def cmd_logs(message: Message):
    await _cmd_logs_logic(message)


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
# Обработчики кнопок reply-клавиатуры
# Работают в любом FSM-состоянии (StateFilter("*"))
# При нажатии во время FSM — отменяют текущий шаг и выполняют действие
# ──────────────────────────────────────────
@dp.message(F.text == "🗂 Серверы", StateFilter("*"))
async def btn_servers(message: Message, state: FSMContext):
    await state.clear()
    await _cmd_servers_logic(message)


@dp.message(F.text == "🛠 Мой сервер", StateFilter("*"))
async def btn_my_server(message: Message, state: FSMContext):
    await state.clear()
    await _cmd_my_server_logic(message)


@dp.message(F.text == "➕ Создать сервер", StateFilter("*"))
async def btn_create(message: Message, state: FSMContext):
    await state.clear()
    await _cmd_create_logic(message, state)


@dp.message(F.text == "❌ Отмена", StateFilter("*"))
async def btn_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer("Нечего отменять.")
    else:
        await state.clear()
        await message.answer("🚫 Действие отменено.")


@dp.message(F.text == "🔐 Админ", StateFilter("*"))
async def btn_admin(message: Message, state: FSMContext):
    await state.clear()
    await _cmd_admin_logic(message)


@dp.message(F.text == "📋 Логи", StateFilter("*"))
async def btn_logs(message: Message, state: FSMContext):
    await state.clear()
    await _cmd_logs_logic(message)


@dp.message(F.text == "🚫 Г-бан", StateFilter("*"))
async def btn_global_ban(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await state.set_state(GlobalBan.ban_id)
    await message.answer(
        "🚫 <b>Глобальный бан</b>\n\nВведи Telegram ID пользователя:\n"
        "<i>Для отмены: /отмена или ❌ Отмена</i>",
        parse_mode="HTML",
    )


@dp.message(F.text == "✅ Г-разбан", StateFilter("*"))
async def btn_global_unban(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await state.set_state(GlobalBan.unban_id)
    await message.answer(
        "✅ <b>Глобальный разбан</b>\n\nВведи Telegram ID пользователя:\n"
        "<i>Для отмены: /отмена или ❌ Отмена</i>",
        parse_mode="HTML",
    )


@dp.message(F.text == "📋 Бан-лист", StateFilter("*"))
async def btn_banlist(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await _show_global_banlist(message)


# ──────────────────────────────────────────
# Запуск
# ──────────────────────────────────────────
async def main():
    asyncio.create_task(backup_loop())
    await db.init_db()
    # Middleware: блокировка глобально забаненных пользователей
    dp.message.outer_middleware(GlobalBanMiddleware())
    dp.callback_query.outer_middleware(GlobalBanMiddleware())
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 LostMiner бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
