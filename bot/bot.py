import asyncio
import html
import logging
from datetime import datetime, timezone
from backup import download_backup, backup_loop
from typing import Any, Awaitable, Callable
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
from translator import t
from aiohttp import web
import asyncio
import os
import asyncio

from backup import (
    download_backup,
    backup_loop
)

async def health(request):
    return web.Response(text="Bot is alive")


async def start_web():
    app = web.Application()
    app.router.add_get("/", health)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 10000))

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()
    print(f"Web server started on port {port}")
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


class EditServer(StatesGroup):
    waiting = State()   # ввод нового значения name/description/ip, поле хранится в state.data["field"]


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
            lang = await db.get_language(user.id)
            if isinstance(event, CallbackQuery):
                try:
                    await event.answer(t("banned_alert", lang), show_alert=True)
                except Exception:
                    pass
            elif isinstance(event, Message):
                try:
                    await event.answer(t("banned_message", lang))
                except Exception:
                    pass
            return  # не передаём дальше
        return await handler(event, data)


# ──────────────────────────────────────────
# Утилиты
# ──────────────────────────────────────────
def e(text: str) -> str:
    return html.escape(str(text))


def status_badge(online: int, lang: str) -> str:
    return t("status_online", lang) if online else t("status_offline", lang)


def status_label(status: str, lang: str) -> str:
    return {
        "pending":  t("status_pending", lang),
        "approved": t("status_approved", lang),
        "rejected": t("status_rejected", lang),
    }.get(status, status)


def privacy_badge(is_private: int, lang: str) -> str:
    return t("privacy_private", lang) if is_private else t("privacy_public", lang)


async def notify_user(user_id: int, text: str, reply_markup=None):
    try:
        await bot.send_message(user_id, text, parse_mode="HTML", reply_markup=reply_markup)
    except Exception as exc:
        logger.warning("Не удалось уведомить %s: %s", user_id, exc)


def time_left(expires_at: str | None, lang: str) -> str:
    if not expires_at:
        return ""
    try:
        exp   = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc)
        now   = datetime.now(timezone.utc)
        total = int((exp - now).total_seconds())
        if total <= 0:
            return t("time_less_than_minute", lang)
        h, rem = divmod(total, 3600)
        m, s   = divmod(rem, 60)
        parts  = []
        if h: parts.append(f"{h} {t('time_unit_hour', lang)}")
        if m: parts.append(f"{m} {t('time_unit_minute', lang)}")
        if s and not h: parts.append(f"{s} {t('time_unit_second', lang)}")
        return " ".join(parts)
    except Exception:
        return ""


def _avatar_status_line(s, lang: str) -> str:
    keys = s.keys()
    pending = s["avatar_pending_file_id"] if "avatar_pending_file_id" in keys else None
    approved = s["avatar_file_id"] if "avatar_file_id" in keys else None
    if pending:
        return t("avatar_status_pending", lang)
    if approved:
        return t("avatar_status_approved", lang)
    return t("avatar_status_none", lang)


def server_card(s, lang: str) -> str:
    """Карточка сервера для владельца (пароль виден)."""
    online_line = status_badge(s["online"], lang)
    if s["online"] and s["expires_at"]:
        left = time_left(s["expires_at"], lang)
        if left:
            online_line += t("time_remaining_suffix", lang).format(time=left)
    is_private = s["is_private"] if "is_private" in s.keys() else 0
    return t("server_card_template", lang).strip().format(
        name=e(s['name']),
        description=e(s['description']),
        ip=e(s['ip']),
        password=e(s['password']) if s['password'] else t("value_none", lang),
        status_label=status_label(s['status'], lang),
        privacy_badge=privacy_badge(is_private, lang),
        avatar_line=_avatar_status_line(s, lang)
                    + (f"\n{t('edit_pending_line', lang)}" if db.has_pending_edit(s) else ""),
        online_line=online_line,
    )


def public_server_card(s, page: int, total: int, lang: str) -> str:
    """Публичная карточка сервера (пароль скрыт) + счётчик страниц."""
    is_private = s["is_private"] if "is_private" in s.keys() else 0
    if is_private:
        pwd_line = t("pwd_hidden_requires_approval", lang)
    else:
        pwd_line = t("pwd_hidden", lang) if s["password"] else t("value_none", lang)
    return t("public_server_card_template", lang).strip().format(
        page=page + 1,
        total=total,
        name=e(s['name']),
        privacy_badge=privacy_badge(is_private, lang),
        description=e(s['description']),
        ip=e(s['ip']),
        pwd_line=pwd_line,
        status_badge=status_badge(s['online'], lang),
    )


# ──────────────────────────────────────────
# Reply-клавиатура (постоянные кнопки)
# ──────────────────────────────────────────
def main_keyboard(lang: str, is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=t("btn_servers", lang)),       KeyboardButton(text=t("btn_my_server", lang))],
        [KeyboardButton(text=t("btn_create_server", lang)), KeyboardButton(text=t("btn_cancel", lang))],
    ]
    if is_admin:
        rows.append([KeyboardButton(text=t("btn_admin", lang)),   KeyboardButton(text=t("btn_logs", lang))])
        rows.append([KeyboardButton(text=t("btn_global_ban", lang)),    KeyboardButton(text=t("btn_global_unban", lang)),
                     KeyboardButton(text=t("btn_banlist", lang))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# ──────────────────────────────────────────
# Inline-клавиатуры
# ──────────────────────────────────────────

def srvlist_keyboard(
    lang: str,
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
        InlineKeyboardButton(text=t("nav_prev", lang),      callback_data=left_cb),
        InlineKeyboardButton(text=f"{page + 1} / {total}", callback_data="srvpage:noop"),
        InlineKeyboardButton(text=t("nav_next", lang),      callback_data=right_cb),
    ]

    rows = [nav_row]

    if is_owner:
        rows.append([InlineKeyboardButton(text=t("btn_manage", lang), callback_data=f"myserver:{server_id}")])
    else:
        sub_text = t("btn_unsubscribe", lang) if subscribed else t("btn_subscribe", lang)
        rows.append([InlineKeyboardButton(text=sub_text, callback_data=f"sub:{server_id}")])
        if has_password:
            pwd_label = t("btn_request_password", lang) if is_private else t("btn_view_password", lang)
            rows.append([InlineKeyboardButton(text=pwd_label, callback_data=f"getpwd:{server_id}")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def manage_keyboard(
    lang: str,
    server_id: int,
    online: int,
    is_private: int,
    avatar_file_id: str | None = None,
    avatar_pending_file_id: str | None = None,
    edit_pending: bool = False,
) -> InlineKeyboardMarkup:
    toggle_text  = t("btn_turn_off", lang)    if online     else t("btn_turn_on", lang)
    toggle_cb    = f"srv:off:{server_id}" if online else f"srv:on:{server_id}"
    privacy_text = t("btn_make_public", lang) if is_private else t("btn_make_private", lang)
    if avatar_pending_file_id:
        avatar_text = t("btn_avatar_pending", lang)
    elif avatar_file_id:
        avatar_text = t("btn_avatar_change", lang)
    else:
        avatar_text = t("btn_avatar_upload", lang)
    edit_text = t("btn_edit_pending", lang) if edit_pending else t("btn_edit_server", lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=edit_text,               callback_data=f"srv:edit:{server_id}")],
        [InlineKeyboardButton(text=t("btn_change_password", lang),  callback_data=f"srv:pwd:{server_id}")],
        [InlineKeyboardButton(text=toggle_text,            callback_data=toggle_cb)],
        [InlineKeyboardButton(text=privacy_text,           callback_data=f"srv:toggleprivate:{server_id}")],
        [InlineKeyboardButton(text=avatar_text,            callback_data=f"srv:avatar:{server_id}")],
        [InlineKeyboardButton(text=t("btn_server_banlist", lang), callback_data=f"srv:banlist:{server_id}")],
        [InlineKeyboardButton(text=t("btn_delete_server", lang),    callback_data=f"srv:del:{server_id}")],
    ])


def delete_keyboard(lang: str, server_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("btn_confirm_delete", lang), callback_data=f"srv:delconfirm:{server_id}"),
        InlineKeyboardButton(text=t("btn_cancel", lang),         callback_data=f"srv:delcancel:{server_id}"),
    ]])


def rejected_keyboard(lang: str, server_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_delete_server", lang), callback_data=f"srv:del:{server_id}")],
    ])


def pwd_request_keyboard(lang: str, request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("btn_grant_password", lang), callback_data=f"pwdreq:approve:{request_id}"),
        InlineKeyboardButton(text=t("btn_reject_password", lang), callback_data=f"pwdreq:reject:{request_id}"),
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
    lang       = await db.get_language(uid)
    total      = len(servers)
    page       = max(0, min(page, total - 1))
    s          = servers[page]
    is_owner   = s["owner_id"] == uid
    is_private = s["is_private"] if "is_private" in s.keys() else 0
    subscribed = False if is_owner else await db.is_subscribed(uid, s["id"])
    has_pwd    = bool(s["password"])
    avatar_fid = s["avatar_file_id"] if "avatar_file_id" in s.keys() else None

    text = public_server_card(s, page, total, lang)
    kb   = srvlist_keyboard(lang, page, total, s["id"], subscribed, has_pwd, is_private, is_owner)

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

    await db.register_user(
        message.from_user.id,
        message.from_user.username
    )

    # Получаем язык пользователя
    lang = await db.get_language(message.from_user.id)

    # Автоопределение языка Telegram при первом входе
    telegram_lang = message.from_user.language_code

    if telegram_lang == "pt":
        telegram_lang = "pt_br"

    if telegram_lang in ["ru", "en", "es", "pt_br"]:
        await db.set_language(
            message.from_user.id,
            telegram_lang
        )
        lang = telegram_lang


    is_admin = message.from_user.id == ADMIN_ID

    admin_block = (
        "\n🔐 <b>" + t("administration", lang) + "</b>\n"
        "/админ — " + t("admin_servers", lang) + "\n"
        "/логи — " + t("logs", lang) + "\n"
    ) if is_admin else ""


    await message.answer(
        t("welcome", lang)
        + "\n\n"
        + t("commands", lang)
        + "\n\n"
        + t("servers_command", lang)
        + "\n\n"
        + t("my_server_command", lang)
        + "\n\n"
        + t("other_command", lang)
        + admin_block
        + "\n<i>"
        + t("buttons_hint", lang)
        + "</i>",
        
        parse_mode="HTML",
        reply_markup=main_keyboard(lang, is_admin),
    )

# ──────────────────────────────────────────
# /серверы — список одобренных серверов (пагинация)
# ──────────────────────────────────────────
async def _cmd_servers_logic(message: Message):
    lang    = await db.get_language(message.from_user.id)
    servers = await db.get_approved_servers()
    if not servers:
        await message.answer(t("no_approved_servers", lang))
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
    lang     = await db.get_language(callback.from_user.id)
    page_str = callback.data.split(":", 1)[1]
    if page_str == "noop":
        await callback.answer()
        return

    if not page_str.lstrip("-").isdigit():
        await callback.answer(t("invalid_data", lang), show_alert=True)
        return

    page    = int(page_str)
    servers = await db.get_approved_servers()
    if not servers:
        await callback.answer(t("no_servers", lang), show_alert=True)
        return

    await callback.answer()
    await _show_server_page(callback.from_user.id, servers, page, callback=callback)


# ──────────────────────────────────────────
# Callback: кнопка «Управление» из списка серверов
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("myserver:"))
async def cb_myserver_shortcut(callback: CallbackQuery):
    lang = await db.get_language(callback.from_user.id)
    await callback.answer()
    await callback.message.answer(t("manage_hint", lang))


# ──────────────────────────────────────────
# Callback: подписка/отписка (sub:<server_id>)
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("sub:"))
async def cb_subscribe(callback: CallbackQuery):
    lang  = await db.get_language(callback.from_user.id)
    parts = callback.data.split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer(t("invalid_data", lang), show_alert=True)
        return

    server_id  = int(parts[1])
    server     = await db.get_server_by_id(server_id)
    if not server or server["status"] != "approved":
        await callback.answer(t("server_not_found", lang), show_alert=True)
        return

    uid = callback.from_user.id
    if server["owner_id"] == uid:
        await callback.answer(t("cant_subscribe_own", lang), show_alert=True)
        return

    currently = await db.is_subscribed(uid, server_id)
    if currently:
        await db.unsubscribe(uid, server_id)
        await db.add_log("unsubscribed", uid, server_id,
                         f"@{callback.from_user.username or uid} отписался от «{server['name']}»")
        await callback.answer(t("unsubscribed", lang))
        subscribed = False
    else:
        await db.subscribe(uid, server_id)
        await db.add_log("subscribed", uid, server_id,
                         f"@{callback.from_user.username or uid} подписался на «{server['name']}»")
        await callback.answer(t("subscribed", lang))
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
    lang  = await db.get_language(callback.from_user.id)
    parts = callback.data.split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer(t("invalid_data", lang), show_alert=True)
        return

    server_id = int(parts[1])
    server    = await db.get_server_by_id(server_id)
    if not server or server["status"] != "approved":
        await callback.answer(t("server_not_found", lang), show_alert=True)
        return

    if not server["password"]:
        await callback.answer(t("no_password", lang), show_alert=True)
        return

    uid        = callback.from_user.id
    uname      = f"@{callback.from_user.username}" if callback.from_user.username else f"id:{uid}"
    is_private = server["is_private"] if "is_private" in server.keys() else 0

    # ── Проверка серверного бана ──
    if await db.is_server_banned(server_id, uid):
        await callback.answer(t("banned_by_owner", lang), show_alert=True)
        return

    # ── Открытый сервер: сразу отправляем пароль ──
    if not is_private:
        try:
            await bot.send_message(
                uid,
                t("password_message", lang).strip().format(
                    name=e(server['name']),
                    password=e(server['password']),
                ),
                parse_mode="HTML",
            )
            await callback.answer(t("password_sent", lang))
        except Exception:
            await callback.answer(
                t("password_send_failed", lang),
                show_alert=True,
            )
            return

        owner_lang = await db.get_language(server["owner_id"])
        await notify_user(
            server["owner_id"],
            t("owner_password_requested", owner_lang).strip().format(
                name=e(server['name']),
                username=e(uname),
                user_id=uid,
            ),
        )
        await db.add_log("password_requested", uid, server_id,
                         f"{uname} получил пароль сервера «{server['name']}»")
        return

    # ── Закрытый сервер: создаём запрос ──
    existing = await db.get_pending_pwd_request(server_id, uid)
    if existing:
        await callback.answer(
            t("request_already_sent", lang),
            show_alert=True,
        )
        return

    req_id = await db.create_pwd_request(server_id, uid)
    await callback.answer(t("request_sent", lang))

    owner_lang = await db.get_language(server["owner_id"])
    await notify_user(
        server["owner_id"],
        t("owner_private_password_requested", owner_lang).strip().format(
            name=e(server['name']),
            username=e(uname),
            user_id=uid,
        ),
        reply_markup=pwd_request_keyboard(owner_lang, req_id),
    )
    await db.add_log("pwd_request_sent", uid, server_id,
                     f"{uname} запросил пароль закрытого сервера «{server['name']}»")


# ──────────────────────────────────────────
# Callback: владелец одобряет/отклоняет запрос пароля
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("pwdreq:"))
async def cb_pwd_request(callback: CallbackQuery):
    lang  = await db.get_language(callback.from_user.id)
    parts = callback.data.split(":")
    if len(parts) != 3 or parts[1] not in ("approve", "reject") or not parts[2].isdigit():
        await callback.answer(t("invalid_data", lang), show_alert=True)
        return

    action     = parts[1]
    request_id = int(parts[2])
    req        = await db.get_pwd_request(request_id)

    if not req:
        await callback.answer(t("request_not_found", lang), show_alert=True)
        return
    if req["status"] != "pending":
        await callback.answer(t("request_already_processed", lang), show_alert=True)
        return

    server = await db.get_server_by_id(req["server_id"])
    if not server or server["owner_id"] != callback.from_user.id:
        await callback.answer(t("no_access", lang), show_alert=True)
        return

    requester_id   = req["requester_id"]
    requester_lang = await db.get_language(requester_id)

    if action == "approve":
        # Сначала доставляем пароль — только при успехе меняем статус
        try:
            await bot.send_message(
                requester_id,
                t("password_granted_message", requester_lang).strip().format(
                    name=e(server['name']),
                    password=e(server['password']),
                ),
                parse_mode="HTML",
            )
        except Exception:
            await callback.message.edit_text(
                t("password_delivery_failed", lang).strip().format(user_id=requester_id),
                parse_mode="HTML",
                reply_markup=pwd_request_keyboard(lang, request_id),
            )
            await callback.answer(t("password_delivery_failed_alert", lang), show_alert=True)
            return

        await db.resolve_pwd_request(request_id, "approved")
        await db.add_log("pwd_request_approved", callback.from_user.id, server["id"],
                         f"Запрос пароля #{request_id} для сервера «{server['name']}» одобрен")
        await callback.message.edit_text(
            t("password_granted_edit", lang).format(user_id=requester_id),
            parse_mode="HTML",
        )
        await callback.answer(t("password_granted_alert", lang))

    else:  # reject
        await db.resolve_pwd_request(request_id, "rejected")
        await db.add_log("pwd_request_rejected", callback.from_user.id, server["id"],
                         f"Запрос пароля #{request_id} для сервера «{server['name']}» отклонён")
        await notify_user(
            requester_id,
            t("password_request_rejected_notify", requester_lang).strip().format(
                name=e(server['name']),
            ),
        )
        await callback.message.edit_text(
            t("password_request_rejected_edit", lang).format(user_id=requester_id),
            parse_mode="HTML",
        )
        await callback.answer(t("password_request_rejected_alert", lang))


# ──────────────────────────────────────────
# /создать — пошаговое создание сервера
# ──────────────────────────────────────────
async def _cmd_create_logic(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    await db.register_user(message.from_user.id, message.from_user.username)

    existing = await db.get_active_server_by_owner(message.from_user.id)
    if existing:
        await message.answer(t("already_has_server", lang).strip())
        return

    await db.delete_rejected_servers(message.from_user.id)
    await state.set_state(CreateServer.name)
    await message.answer(
        t("create_step1", lang).strip(),
        parse_mode="HTML",
    )


@dp.message(Command("создать"))
async def cmd_create(message: Message, state: FSMContext):
    await _cmd_create_logic(message, state)


@dp.message(CreateServer.name)
async def create_name(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    if not message.text:
        await message.answer(t("please_send_text", lang))
        return
    if len(message.text) > 64:
        await message.answer(t("name_too_long", lang))
        return
    await state.update_data(name=message.text)
    await state.set_state(CreateServer.description)
    await message.answer(t("create_step2", lang), parse_mode="HTML")


@dp.message(CreateServer.description)
async def create_description(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    if not message.text:
        await message.answer(t("please_send_text", lang))
        return
    if len(message.text) > 512:
        await message.answer(t("description_too_long", lang))
        return
    await state.update_data(description=message.text)
    await state.set_state(CreateServer.ip)
    await message.answer(t("create_step3", lang), parse_mode="HTML")


@dp.message(CreateServer.ip)
async def create_ip(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    if not message.text:
        await message.answer(t("please_send_text", lang))
        return
    await state.update_data(ip=message.text.strip())
    await state.set_state(CreateServer.password)
    await message.answer(
        t("create_step4", lang).strip(),
        parse_mode="HTML",
    )


@dp.message(CreateServer.password)
async def create_password_step(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    if not message.text:
        await message.answer(t("please_send_text", lang))
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
        t("server_submitted", lang).strip().format(
            name=e(data['name']),
            ip=e(data['ip']),
        ),
        parse_mode="HTML",
    )
    admin_lang = await db.get_language(ADMIN_ID)
    await notify_user(
        ADMIN_ID,
        t("admin_new_server", admin_lang).strip().format(
            name=e(data['name']),
            ip=e(data['ip']),
        ),
    )


# ──────────────────────────────────────────
# /мой_сервер — управление своим сервером
# ──────────────────────────────────────────
async def _cmd_my_server_logic(message: Message):
    lang   = await db.get_language(message.from_user.id)
    server = await db.get_any_server_by_owner(message.from_user.id)
    if not server:
        await message.answer(t("no_own_server", lang))
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
                                 caption=t("avatar_caption", lang), parse_mode="HTML")
        except Exception:
            pass

    text = server_card(server, lang)
    if server["status"] == "approved":
        kb = manage_keyboard(lang, server["id"], server["online"], is_private, avatar_fid, avatar_pid,
                             db.has_pending_edit(server))
    elif server["status"] == "rejected":
        kb = rejected_keyboard(lang, server["id"])
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
    lang  = await db.get_language(callback.from_user.id)
    parts = callback.data.split(":")
    if len(parts) != 3 or not parts[2].isdigit():
        await callback.answer(t("invalid_data", lang), show_alert=True)
        return

    action    = parts[1]
    server_id = int(parts[2])
    server    = await db.get_server_by_id(server_id)

    if not server or server["owner_id"] != callback.from_user.id:
        await callback.answer(t("no_access", lang), show_alert=True)
        return

    keys       = server.keys()
    is_private = server["is_private"] if "is_private" in keys else 0
    avatar_fid = server["avatar_file_id"] if "avatar_file_id" in keys else None
    avatar_pid = server["avatar_pending_file_id"] if "avatar_pending_file_id" in keys else None

    def _mkb(srv):
        k = srv.keys()
        return manage_keyboard(
            lang,
            srv["id"], srv["online"],
            srv["is_private"] if "is_private" in k else 0,
            srv["avatar_file_id"] if "avatar_file_id" in k else None,
            srv["avatar_pending_file_id"] if "avatar_pending_file_id" in k else None,
            db.has_pending_edit(srv),
        )

    # ── Включить ──
    if action == "on":
        await db.set_server_online(server_id)
        server = await db.get_server_by_id(server_id)
        await callback.message.edit_text(
            server_card(server, lang), parse_mode="HTML", reply_markup=_mkb(server),
        )
        await callback.answer(t("server_turned_on_alert", lang))
        await db.add_log("server_online", callback.from_user.id, server_id,
                         f"Сервер «{server['name']}» включён владельцем")

        is_private = server["is_private"] if "is_private" in server.keys() else 0
        subscribers = await db.get_subscribers(server_id)
        if subscribers:
            for uid in subscribers:
                sub_lang = await db.get_language(uid)
                if is_private:
                    pwd_hint = t("pwd_hint_request", sub_lang)
                elif server["password"]:
                    pwd_hint = t("pwd_hint_hidden", sub_lang)
                else:
                    pwd_hint = t("value_none", sub_lang)
                notify_text = t("subscriber_notify", sub_lang).strip().format(
                    name=e(server['name']),
                    ip=e(server['ip']),
                    pwd_hint=pwd_hint,
                )
                await notify_user(uid, notify_text)

    # ── Выключить ──
    elif action == "off":
        await db.set_server_offline(server_id)
        server = await db.get_server_by_id(server_id)
        await callback.message.edit_text(
            server_card(server, lang), parse_mode="HTML", reply_markup=_mkb(server),
        )
        await callback.answer(t("server_turned_off_alert", lang))
        await db.add_log("server_offline", callback.from_user.id, server_id,
                         f"Сервер «{server['name']}» выключен владельцем")

    # ── Меню редактирования данных (название/описание/IP) ──
    elif action == "edit":
        if db.has_pending_edit(server):
            await callback.answer(t("edit_already_pending", lang), show_alert=True)
            return
        rows = [
            [InlineKeyboardButton(text=t("btn_edit_name", lang),        callback_data=f"srvedit:name:{server_id}")],
            [InlineKeyboardButton(text=t("btn_edit_description", lang), callback_data=f"srvedit:description:{server_id}")],
            [InlineKeyboardButton(text=t("btn_edit_ip", lang),          callback_data=f"srvedit:ip:{server_id}")],
            [InlineKeyboardButton(text=t("btn_back", lang),             callback_data=f"srv:back:{server_id}")],
        ]
        await callback.message.edit_text(
            t("edit_menu", lang).strip().format(name=e(server['name'])),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )
        await callback.answer()

    # ── Изменить пароль ──
    elif action == "pwd":
        await state.update_data(manage_server_id=server_id)
        await state.set_state(ChangePassword.waiting)
        await callback.message.answer(
            t("change_password_prompt", lang).strip(),
            parse_mode="HTML",
        )
        await callback.answer()

    # ── Переключить тип (открытый/закрытый) ──
    elif action == "toggleprivate":
        new_private = await db.toggle_server_private(server_id)
        server      = await db.get_server_by_id(server_id)
        label       = t("label_private", lang) if new_private else t("label_public", lang)
        await callback.message.edit_text(
            server_card(server, lang), parse_mode="HTML", reply_markup=_mkb(server),
        )
        await callback.answer(t("server_type_changed_alert", lang).format(label=label))
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
                    text=t("btn_unban_user", lang).format(user_id=ban['banned_user_id'], date=dt),
                    callback_data=f"srvunban:{ban['id']}",
                )])
        rows.append([InlineKeyboardButton(
            text=t("btn_ban_by_id", lang),
            callback_data=f"srv:ban:{server_id}",
        )])
        rows.append([InlineKeyboardButton(
            text=t("btn_back", lang),
            callback_data=f"srv:back:{server_id}",
        )])
        header = t("banlist_header", lang).format(name=e(server['name']))
        if bans:
            header += t("banlist_count", lang).format(count=len(bans))
        else:
            header += t("banlist_empty", lang)
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
            t("ban_prompt", lang).strip().format(name=e(server['name'])),
            parse_mode="HTML",
        )
        await callback.answer()

    # ── Назад в главное меню управления ──
    elif action == "back":
        server = await db.get_server_by_id(server_id)
        await callback.message.edit_text(
            server_card(server, lang), parse_mode="HTML", reply_markup=_mkb(server),
        )
        await callback.answer()

    # ── Загрузить/изменить аватарку ──
    elif action == "avatar":
        # Блокируем повторную загрузку пока предыдущая на модерации
        if avatar_pid:
            await callback.answer(
                t("avatar_already_pending", lang),
                show_alert=True,
            )
            return
        await state.update_data(manage_server_id=server_id)
        await state.set_state(ChangeAvatar.waiting)
        await callback.message.answer(
            t("avatar_upload_prompt", lang).strip(),
            parse_mode="HTML",
        )
        await callback.answer()

    # ── Удалить: запрос подтверждения ──
    elif action == "del":
        await callback.message.edit_text(
            t("delete_confirm_prompt", lang).strip().format(name=e(server['name'])),
            parse_mode="HTML",
            reply_markup=delete_keyboard(lang, server_id),
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
                t("server_deleted_message", lang).strip().format(name=e(name)),
                parse_mode="HTML",
            )
            await callback.answer(t("server_deleted_alert", lang))
        else:
            await callback.answer(t("server_delete_failed", lang), show_alert=True)

    # ── Удалить: отмена ──
    elif action == "delcancel":
        if server["status"] == "approved":
            kb = _mkb(server)
        elif server["status"] == "rejected":
            kb = rejected_keyboard(lang, server_id)
        else:
            kb = None
        await callback.message.edit_text(server_card(server, lang), parse_mode="HTML", reply_markup=kb)
        await callback.answer(t("delete_cancelled_alert", lang))

    else:
        await callback.answer(t("unknown_action_alert", lang), show_alert=True)


# ──────────────────────────────────────────
# Callback: выбор конкретного поля для редактирования (srvedit:<field>:<server_id>)
# ──────────────────────────────────────────
_EDIT_FIELD_PROMPT_KEYS = {
    "name":        "edit_prompt_name",
    "description": "edit_prompt_description",
    "ip":          "edit_prompt_ip",
}


@dp.callback_query(F.data.startswith("srvedit:"))
async def cb_edit_field_choice(callback: CallbackQuery, state: FSMContext):
    lang  = await db.get_language(callback.from_user.id)
    parts = callback.data.split(":")
    if len(parts) != 3 or parts[1] not in _EDIT_FIELD_PROMPT_KEYS or not parts[2].isdigit():
        await callback.answer(t("invalid_data", lang), show_alert=True)
        return

    field     = parts[1]
    server_id = int(parts[2])
    server    = await db.get_server_by_id(server_id)

    if not server or server["owner_id"] != callback.from_user.id:
        await callback.answer(t("no_access", lang), show_alert=True)
        return

    if db.has_pending_edit(server):
        await callback.answer(t("edit_already_pending", lang), show_alert=True)
        return

    await state.update_data(manage_server_id=server_id, edit_field=field)
    await state.set_state(EditServer.waiting)
    await callback.message.answer(
        t(_EDIT_FIELD_PROMPT_KEYS[field], lang).strip(),
        parse_mode="HTML",
    )
    await callback.answer()


# ──────────────────────────────────────────
# FSM: ввод нового значения поля (EditServer.waiting)
# ──────────────────────────────────────────
@dp.message(EditServer.waiting)
async def edit_server_step(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    if not message.text:
        await message.answer(t("please_send_text", lang))
        return

    data      = await state.get_data()
    server_id = data.get("manage_server_id")
    field     = data.get("edit_field")
    if not server_id or field not in _EDIT_FIELD_PROMPT_KEYS:
        await state.clear()
        await message.answer(t("state_error", lang))
        return

    server = await db.get_server_by_id(server_id)
    if not server or server["owner_id"] != message.from_user.id:
        await state.clear()
        await message.answer(t("no_access", lang))
        return

    new_value = message.text.strip()

    if field == "name":
        if len(new_value) > 64:
            await message.answer(t("name_too_long", lang))
            return
    elif field == "description":
        if len(new_value) > 512:
            await message.answer(t("description_too_long", lang))
            return

    await db.request_server_edit(server_id, field, new_value)
    await state.clear()

    old_value = server[field]

    await db.add_log(
        "edit_requested", message.from_user.id, server_id,
        f"@{message.from_user.username or message.from_user.id} предложил новое значение поля «{field}» для сервера «{server['name']}»",
    )

    await message.answer(
        t("edit_submitted", lang).strip(),
        parse_mode="HTML",
    )

    admin_lang = await db.get_language(ADMIN_ID)
    diff = t("edit_diff_line", admin_lang).format(
        field=t(f"field_{field}", admin_lang),
        old=e(old_value),
        new=e(new_value),
    )
    await notify_user(
        ADMIN_ID,
        t("admin_new_edit", admin_lang).strip().format(
            name=e(server['name']),
            owner_id=server['owner_id'],
            diff=diff,
        ),
    )


@dp.message(ChangePassword.waiting)
async def change_password_step(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    if not message.text:
        await message.answer(t("please_send_text", lang))
        return

    data      = await state.get_data()
    server_id = data.get("manage_server_id")
    if not server_id:
        await state.clear()
        await message.answer(t("state_error", lang))
        return

    server = await db.get_server_by_id(server_id)
    if not server or server["owner_id"] != message.from_user.id:
        await state.clear()
        await message.answer(t("no_access", lang))
        return

    new_password = message.text.strip()
    if new_password.lower() == "нет":
        new_password = ""

    await db.update_server_password(server_id, new_password)
    await db.add_log("password_changed", message.from_user.id, server_id,
                     f"Пароль сервера «{server['name']}» изменён")
    await state.clear()

    display = f"<code>{e(new_password)}</code>" if new_password else t("value_none", lang)
    await message.answer(
        t("password_updated", lang).format(password=display),
        parse_mode="HTML",
    )


# ──────────────────────────────────────────
# FSM: бан пользователя на сервере (ServerBan.waiting)
# ──────────────────────────────────────────
@dp.message(ServerBan.waiting)
async def server_ban_step(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    if not message.text or not message.text.strip().lstrip("-").isdigit():
        await message.answer(t("enter_numeric_id_retry", lang))
        return

    target_id = int(message.text.strip())
    data      = await state.get_data()
    server_id = data.get("manage_server_id")
    if not server_id:
        await state.clear()
        await message.answer(t("state_error", lang))
        return

    server = await db.get_server_by_id(server_id)
    if not server or server["owner_id"] != message.from_user.id:
        await state.clear()
        await message.answer(t("no_access", lang))
        return

    if target_id == message.from_user.id:
        await message.answer(t("cant_ban_self", lang))
        return
    if target_id == ADMIN_ID:
        await message.answer(t("cant_ban_admin", lang))
        return

    ok = await db.ban_server_user(server_id, target_id)
    await state.clear()
    if ok:
        await db.add_log("server_ban", message.from_user.id, server_id,
                         f"Пользователь {target_id} забанен на сервере «{server['name']}»")
        await message.answer(
            t("server_ban_success", lang).strip().format(user_id=target_id, name=e(server['name'])),
            parse_mode="HTML",
        )
        # Уведомляем забаненного
        target_lang = await db.get_language(target_id)
        await notify_user(
            target_id,
            t("server_ban_notify", target_lang).strip().format(name=e(server['name'])),
        )
    else:
        await message.answer(t("already_banned", lang).format(user_id=target_id),
                             parse_mode="HTML")


# ──────────────────────────────────────────
# Callback: разбан пользователя на сервере (srvunban:<ban_id>)
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("srvunban:"))
async def cb_srv_unban(callback: CallbackQuery):
    lang  = await db.get_language(callback.from_user.id)
    parts = callback.data.split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer(t("invalid_data", lang), show_alert=True)
        return

    ban_id = int(parts[1])
    ban    = await db.get_server_ban_by_id(ban_id)
    if not ban:
        await callback.answer(t("ban_record_not_found", lang), show_alert=True)
        return

    server = await db.get_server_by_id(ban["server_id"])
    if not server or server["owner_id"] != callback.from_user.id:
        await callback.answer(t("no_access", lang), show_alert=True)
        return

    result = await db.unban_server_user_by_ban_id(ban_id)
    if result:
        server_id, user_id = result
        await db.add_log("server_unban", callback.from_user.id, server_id,
                         f"Пользователь {user_id} разбанен на сервере «{server['name']}»")
        user_lang = await db.get_language(user_id)
        await notify_user(
            user_id,
            t("server_unban_notify", user_lang).strip().format(name=e(server['name'])),
        )

    # Перерисовываем бан-лист
    bans = await db.get_server_bans(server["id"])
    rows = []
    for b in bans:
        dt = str(b["created_at"])[:10]
        rows.append([InlineKeyboardButton(
            text=t("btn_unban_user", lang).format(user_id=b['banned_user_id'], date=dt),
            callback_data=f"srvunban:{b['id']}",
        )])
    rows.append([InlineKeyboardButton(text=t("btn_ban_by_id", lang),
                                      callback_data=f"srv:ban:{server['id']}")])
    rows.append([InlineKeyboardButton(text=t("btn_back", lang),
                                      callback_data=f"srv:back:{server['id']}")])
    header = t("banlist_header", lang).format(name=e(server['name']))
    header += t("banlist_count", lang).format(count=len(bans)) if bans else t("banlist_empty", lang)
    try:
        await callback.message.edit_text(
            header, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )
    except Exception:
        pass
    await callback.answer(t("unbanned_alert", lang))


# ──────────────────────────────────────────
# FSM: загрузка аватарки (ChangeAvatar.waiting)
# ──────────────────────────────────────────
@dp.message(ChangeAvatar.waiting)
async def change_avatar_step(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    # Принимаем только фото
    if not message.photo:
        await message.answer(
            t("avatar_not_photo", lang),
            parse_mode="HTML",
        )
        return

    data      = await state.get_data()
    server_id = data.get("manage_server_id")
    if not server_id:
        await state.clear()
        await message.answer(t("state_error", lang))
        return

    server = await db.get_server_by_id(server_id)
    if not server or server["owner_id"] != message.from_user.id:
        await state.clear()
        await message.answer(t("no_access", lang))
        return

    # Берём наибольшее разрешение
    file_id = message.photo[-1].file_id
    await db.set_avatar_pending(server_id, file_id)
    await db.add_log("avatar_uploaded", message.from_user.id, server_id,
                     f"Аватарка сервера «{server['name']}» отправлена на модерацию")
    await state.clear()

    await message.answer(
        t("avatar_submitted", lang),
        parse_mode="HTML",
    )

    # Уведомляем админа с предпросмотром
    admin_lang = await db.get_language(ADMIN_ID)
    try:
        await bot.send_photo(
            ADMIN_ID,
            file_id,
            caption=t("admin_new_avatar", admin_lang).strip().format(
                name=e(server['name']),
                owner_id=server['owner_id'],
            ),
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.warning("Не удалось уведомить админа об аватарке: %s", exc)


# ──────────────────────────────────────────
# /админ — панель модерации
# ──────────────────────────────────────────
async def _cmd_admin_logic(message: Message):
    lang = await db.get_language(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("no_permission", lang))
        return

    pending_servers  = await db.get_pending_servers()
    pending_avatars  = await db.get_servers_with_pending_avatars()
    pending_edits    = await db.get_servers_with_pending_edits()
    has_anything     = bool(pending_servers or pending_avatars or pending_edits)

    if not has_anything:
        await message.answer(t("no_pending_moderation", lang))
        return

    # ── Серверы ──
    if pending_servers:
        await message.answer(
            t("pending_servers_count", lang).format(count=len(pending_servers)), parse_mode="HTML"
        )
        for s in pending_servers:
            text = t("admin_server_card", lang).strip().format(
                name=e(s['name']),
                description=e(s['description']),
                ip=e(s['ip']),
                password=e(s['password']) if s['password'] else t("value_none", lang),
                owner_id=s['owner_id'],
                created_at=s['created_at'],
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("btn_approve", lang),  callback_data=f"mod:approve:{s['id']}"),
                InlineKeyboardButton(text=t("btn_reject", lang), callback_data=f"mod:reject:{s['id']}"),
            ]])
            await message.answer(text, parse_mode="HTML", reply_markup=kb)

    # ── Аватарки ──
    if pending_avatars:
        await message.answer(
            t("pending_avatars_count", lang).format(count=len(pending_avatars)), parse_mode="HTML"
        )
        for s in pending_avatars:
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("btn_approve", lang),  callback_data=f"avatarmod:approve:{s['id']}"),
                InlineKeyboardButton(text=t("btn_reject", lang), callback_data=f"avatarmod:reject:{s['id']}"),
            ]])
            try:
                await bot.send_photo(
                    message.chat.id,
                    s["avatar_pending_file_id"],
                    caption=t("avatar_moderation_caption", lang).strip().format(
                        name=e(s['name']),
                        owner_id=s['owner_id'],
                    ),
                    parse_mode="HTML",
                    reply_markup=kb,
                )
            except Exception:
                await message.answer(
                    t("avatar_upload_failed", lang).format(name=e(s['name'])),
                    parse_mode="HTML",
                    reply_markup=kb,
                )

    # ── Правки данных (название/описание/IP) ──
    if pending_edits:
        await message.answer(
            t("pending_edits_count", lang).format(count=len(pending_edits)), parse_mode="HTML"
        )
        for s in pending_edits:
            diff_lines = []
            for field in ("name", "description", "ip"):
                pending_value = s[f"pending_{field}"]
                if pending_value:
                    diff_lines.append(t("edit_diff_line", lang).format(
                        field=t(f"field_{field}", lang),
                        old=e(s[field]),
                        new=e(pending_value),
                    ))
            text = t("admin_edit_card", lang).strip().format(
                name=e(s['name']),
                owner_id=s['owner_id'],
                diff="\n\n".join(diff_lines),
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("btn_approve", lang),  callback_data=f"editmod:approve:{s['id']}"),
                InlineKeyboardButton(text=t("btn_reject", lang), callback_data=f"editmod:reject:{s['id']}"),
            ]])
            await message.answer(text, parse_mode="HTML", reply_markup=kb)


@dp.message(Command("админ"))
async def cmd_admin(message: Message):
    await _cmd_admin_logic(message)


@dp.callback_query(F.data.startswith("mod:"))
async def cb_moderate(callback: CallbackQuery):
    lang = await db.get_language(callback.from_user.id)
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(t("no_access", lang), show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 3 or parts[1] not in ("approve", "reject") or not parts[2].isdigit():
        await callback.answer(t("invalid_data", lang), show_alert=True)
        return

    action    = parts[1]
    server_id = int(parts[2])
    server    = await db.get_server_by_id(server_id)

    if not server:
        await callback.answer(t("server_not_found", lang), show_alert=True)
        return

    owner_lang = await db.get_language(server["owner_id"])

    if action == "approve":
        await db.set_server_status(server_id, "approved")
        await db.add_log("server_approved", callback.from_user.id, server_id,
                         f"Сервер «{server['name']}» одобрен администратором")
        await callback.message.edit_text(
            t("server_approved_edit", lang).format(name=e(server['name'])), parse_mode="HTML"
        )
        await callback.answer()
        await notify_user(
            server["owner_id"],
            t("server_approved_notify", owner_lang).strip().format(name=e(server['name'])),
        )
    else:
        await db.set_server_status(server_id, "rejected")
        await db.add_log("server_rejected", callback.from_user.id, server_id,
                         f"Сервер «{server['name']}» отклонён администратором")
        await callback.message.edit_text(
            t("server_rejected_edit", lang).format(name=e(server['name'])), parse_mode="HTML"
        )
        await callback.answer()
        await notify_user(
            server["owner_id"],
            t("server_rejected_notify", owner_lang).strip().format(name=e(server['name'])),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("btn_delete_server", owner_lang),
                                      callback_data=f"srv:del:{server_id}")],
            ]),
        )


# ──────────────────────────────────────────
# Callback: модерация аватарок (avatarmod:approve/reject:<server_id>)
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("avatarmod:"))
async def cb_avatar_moderate(callback: CallbackQuery):
    lang = await db.get_language(callback.from_user.id)
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(t("no_access", lang), show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 3 or parts[1] not in ("approve", "reject") or not parts[2].isdigit():
        await callback.answer(t("invalid_data", lang), show_alert=True)
        return

    action    = parts[1]
    server_id = int(parts[2])
    server    = await db.get_server_by_id(server_id)

    if not server:
        await callback.answer(t("server_not_found", lang), show_alert=True)
        return

    keys       = server.keys()
    avatar_pid = server["avatar_pending_file_id"] if "avatar_pending_file_id" in keys else None
    if not avatar_pid:
        await callback.answer(t("avatar_already_processed", lang), show_alert=True)
        return

    owner_lang = await db.get_language(server["owner_id"])

    if action == "approve":
        await db.approve_avatar(server_id)
        await db.add_log("avatar_approved", callback.from_user.id, server_id,
                         f"Аватарка сервера «{server['name']}» одобрена")
        try:
            await callback.message.edit_caption(
                caption=t("avatar_approved_edit", lang).format(name=e(server['name'])),
                parse_mode="HTML",
            )
        except Exception:
            pass
        await callback.answer(t("avatar_approved_alert", lang))
        await notify_user(
            server["owner_id"],
            t("avatar_approved_notify", owner_lang).strip().format(name=e(server['name'])),
        )

    else:  # reject
        await db.reject_avatar(server_id)
        await db.add_log("avatar_rejected", callback.from_user.id, server_id,
                         f"Аватарка сервера «{server['name']}» отклонена")
        try:
            await callback.message.edit_caption(
                caption=t("avatar_rejected_edit", lang).format(name=e(server['name'])),
                parse_mode="HTML",
            )
        except Exception:
            pass
        await callback.answer(t("avatar_rejected_alert", lang))
        await notify_user(
            server["owner_id"],
            t("avatar_rejected_notify", owner_lang).strip().format(name=e(server['name'])),
        )


# ──────────────────────────────────────────
# Callback: модерация правок название/описание/IP (editmod:approve/reject:<server_id>)
# ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("editmod:"))
async def cb_edit_moderate(callback: CallbackQuery):
    lang = await db.get_language(callback.from_user.id)
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(t("no_access", lang), show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 3 or parts[1] not in ("approve", "reject") or not parts[2].isdigit():
        await callback.answer(t("invalid_data", lang), show_alert=True)
        return

    action    = parts[1]
    server_id = int(parts[2])
    server    = await db.get_server_by_id(server_id)

    if not server:
        await callback.answer(t("server_not_found", lang), show_alert=True)
        return

    if not db.has_pending_edit(server):
        await callback.answer(t("edit_already_processed", lang), show_alert=True)
        return

    owner_lang = await db.get_language(server["owner_id"])

    if action == "approve":
        await db.approve_server_edit(server_id)
        await db.add_log("edit_approved", callback.from_user.id, server_id,
                         f"Правка сервера «{server['name']}» одобрена")
        try:
            await callback.message.edit_text(
                t("edit_approved_edit", lang).format(name=e(server['name'])),
                parse_mode="HTML",
            )
        except Exception:
            pass
        await callback.answer(t("edit_approved_alert", lang))
        await notify_user(
            server["owner_id"],
            t("edit_approved_notify", owner_lang).strip().format(name=e(server['name'])),
        )

    else:  # reject
        await db.reject_server_edit(server_id)
        await db.add_log("edit_rejected", callback.from_user.id, server_id,
                         f"Правка сервера «{server['name']}» отклонена")
        try:
            await callback.message.edit_text(
                t("edit_rejected_edit", lang).format(name=e(server['name'])),
                parse_mode="HTML",
            )
        except Exception:
            pass
        await callback.answer(t("edit_rejected_alert", lang))
        await notify_user(
            server["owner_id"],
            t("edit_rejected_notify", owner_lang).strip().format(name=e(server['name'])),
        )


# ──────────────────────────────────────────
# Команды глобального бана (только ADMIN_ID)
# ──────────────────────────────────────────
async def _do_global_ban(message: Message, state: FSMContext, target_id: int):
    lang = await db.get_language(message.from_user.id)
    if target_id == ADMIN_ID:
        await message.answer(t("cant_ban_admin", lang))
        return
    ok = await db.ban_user_globally(target_id)
    await state.clear()
    if ok:
        await db.add_log("global_ban", message.from_user.id, None,
                         f"Пользователь {target_id} глобально забанен")
        await message.answer(t("global_ban_success", lang).format(user_id=target_id),
                             parse_mode="HTML")
        target_lang = await db.get_language(target_id)
        await notify_user(target_id, t("global_ban_notify", target_lang))
    else:
        await message.answer(t("already_globally_banned", lang).format(user_id=target_id),
                             parse_mode="HTML")


async def _do_global_unban(message: Message, state: FSMContext, target_id: int):
    lang = await db.get_language(message.from_user.id)
    ok = await db.unban_user_globally(target_id)
    await state.clear()
    if ok:
        await db.add_log("global_unban", message.from_user.id, None,
                         f"Пользователь {target_id} глобально разбанен")
        await message.answer(t("global_unban_success", lang).format(user_id=target_id),
                             parse_mode="HTML")
        target_lang = await db.get_language(target_id)
        await notify_user(target_id, t("global_unban_notify", target_lang))
    else:
        await message.answer(t("not_globally_banned", lang).format(user_id=target_id),
                             parse_mode="HTML")


@dp.message(Command("бан"))
async def cmd_ban(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("no_permission", lang))
        return
    # /бан 123456 — с аргументом
    args = message.text.split(maxsplit=1)
    if len(args) == 2 and args[1].lstrip("-").isdigit():
        await _do_global_ban(message, state, int(args[1]))
    else:
        await state.set_state(GlobalBan.ban_id)
        await message.answer(
            t("global_ban_prompt", lang),
            parse_mode="HTML",
        )


@dp.message(Command("разбан"))
async def cmd_unban(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("no_permission", lang))
        return
    args = message.text.split(maxsplit=1)
    if len(args) == 2 and args[1].lstrip("-").isdigit():
        await _do_global_unban(message, state, int(args[1]))
    else:
        await state.set_state(GlobalBan.unban_id)
        await message.answer(
            t("global_unban_prompt", lang),
            parse_mode="HTML",
        )


@dp.message(Command("банлист"))
async def cmd_banlist(message: Message):
    lang = await db.get_language(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("no_permission", lang))
        return
    await _show_global_banlist(message)


async def _show_global_banlist(message: Message):
    lang = await db.get_language(message.from_user.id)
    bans = await db.get_global_bans()
    if not bans:
        await message.answer(t("global_banlist_empty", lang))
        return
    lines = [t("global_banlist_header", lang).format(count=len(bans))]
    for b in bans:
        dt = str(b["created_at"])[:10]
        lines.append(t("global_banlist_entry", lang).format(user_id=b['user_id'], date=dt))
    await message.answer("\n".join(lines), parse_mode="HTML")


# ── FSM: ввод ID для глобального бана/разбана ──
@dp.message(GlobalBan.ban_id)
async def global_ban_id_step(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    if not message.text or not message.text.strip().lstrip("-").isdigit():
        await message.answer(t("enter_numeric_id", lang))
        return
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    await _do_global_ban(message, state, int(message.text.strip()))


@dp.message(GlobalBan.unban_id)
async def global_unban_id_step(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    if not message.text or not message.text.strip().lstrip("-").isdigit():
        await message.answer(t("enter_numeric_id", lang))
        return
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    await _do_global_unban(message, state, int(message.text.strip()))


# ──────────────────────────────────────────
# /логи — журнал событий
# ──────────────────────────────────────────
async def _cmd_logs_logic(message: Message):
    lang = await db.get_language(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("no_permission", lang))
        return

    logs = await db.get_logs(40)
    if not logs:
        await message.answer(t("logs_empty", lang))
        return

    lines = [t("logs_header", lang)]
    for log in logs:
        label  = db.LOG_LABELS.get(log["event"], log["event"])
        dt     = str(log["created_at"])[:16]
        actor  = f"id:{log['actor_id']}" if log["actor_id"] else "—"
        srv    = f" | сервер #{log['server_id']}" if log["server_id"] else ""
        detail = f"\n   └ {e(log['details'])}" if log["details"] else ""
        lines.append(t("logs_entry", lang).format(datetime=dt, label=label, actor=actor, server=srv, details=detail))

    text = "\n\n".join(lines)
    if len(text) > 4000:
        text = text[:3990] + t("logs_truncated", lang)

    await message.answer(text, parse_mode="HTML")


@dp.message(Command("логи"))
async def cmd_logs(message: Message):
    await _cmd_logs_logic(message)


# ──────────────────────────────────────────
# /отмена — выход из любого FSM
# ──────────────────────────────────────────
@dp.message(Command("отмена"))
async def cmd_cancel(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    current = await state.get_state()
    if current is None:
        await message.answer(t("nothing_to_cancel", lang))
        return
    await state.clear()
    await message.answer(t("action_cancelled", lang))


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
    lang = await db.get_language(message.from_user.id)
    current = await state.get_state()
    if current is None:
        await message.answer(t("nothing_to_cancel", lang))
    else:
        await state.clear()
        await message.answer(t("action_cancelled", lang))


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
    lang = await db.get_language(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await state.set_state(GlobalBan.ban_id)
    await message.answer(
        t("global_ban_prompt_btn", lang),
        parse_mode="HTML",
    )


@dp.message(F.text == "✅ Г-разбан", StateFilter("*"))
async def btn_global_unban(message: Message, state: FSMContext):
    lang = await db.get_language(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await state.set_state(GlobalBan.unban_id)
    await message.answer(
        t("global_unban_prompt_btn", lang),
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

from backup import download_backup, backup_loop


async def main():

    # Сначала восстанавливаем базу из GitHub
    await download_backup()

    # Инициализируем SQLite
    await db.init_db()


    # Запускаем веб-сервер для Render
    asyncio.create_task(start_web())


    # Запускаем автоматические резервные копии
    asyncio.create_task(
        backup_loop()
    )


    # Middleware
    dp.message.outer_middleware(
        GlobalBanMiddleware()
    )

    dp.callback_query.outer_middleware(
        GlobalBanMiddleware()
    )


    await bot.delete_webhook(
        drop_pending_updates=True
    )


    logger.info(
        "🤖 LostMiner бот запущен!"
    )


    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())
