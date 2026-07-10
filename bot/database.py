import aiosqlite
import os
import asyncio

backup_needed = False


def mark_backup():

    global backup_needed

    backup_needed = True
DB_PATH = os.path.join(os.path.dirname(__file__), "lostminer.db")

CONNECT_KWARGS = {"timeout": 10}


async def init_db():
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                ip TEXT NOT NULL,
                password TEXT,
                status TEXT DEFAULT 'pending',
                online INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                is_private INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(telegram_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                server_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, server_id),
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                FOREIGN KEY (server_id) REFERENCES servers(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                actor_id INTEGER,
                server_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS password_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER NOT NULL,
                requester_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (server_id) REFERENCES servers(id),
                FOREIGN KEY (requester_id) REFERENCES users(telegram_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS server_bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER NOT NULL,
                banned_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(server_id, banned_user_id),
                FOREIGN KEY (server_id) REFERENCES servers(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
        mark_backup()
        # Миграции: добавляем колонки если их ещё нет
        for col_sql in [
            "ALTER TABLE servers ADD COLUMN is_private INTEGER DEFAULT 0",
            "ALTER TABLE servers ADD COLUMN avatar_file_id TEXT",
            "ALTER TABLE servers ADD COLUMN avatar_pending_file_id TEXT",
            "ALTER TABLE servers ADD COLUMN pending_name TEXT",
            "ALTER TABLE servers ADD COLUMN pending_description TEXT",
            "ALTER TABLE servers ADD COLUMN pending_ip TEXT",
        ]:
            try:
                await db.execute(col_sql)
                await db.commit()
                mark_backup()
            except Exception:
                pass  # Колонка уже есть
        try:
            await db.execute(
                "ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'ru'"
            )
            await db.commit()
        except Exception:
            pass


# ── Пользователи ──────────────────────────────────────────────────────────────

async def register_user(telegram_id: int, username: str | None):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username),
        )
        await db.commit()
        mark_backup()
        
async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            return await cursor.fetchone()


# ── Серверы ───────────────────────────────────────────────────────────────────

async def get_any_server_by_owner(owner_id: int):
    """Любой сервер пользователя (любой статус). Для /мой_сервер."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM servers WHERE owner_id = ? ORDER BY created_at DESC LIMIT 1",
            (owner_id,),
        ) as cursor:
            return await cursor.fetchone()


async def get_active_server_by_owner(owner_id: int):
    """Активный сервер (pending или approved). Для блокировки повторного создания."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM servers WHERE owner_id = ? AND status IN ('pending', 'approved') LIMIT 1",
            (owner_id,),
        ) as cursor:
            return await cursor.fetchone()


async def create_server(owner_id: int, name: str, description: str, ip: str, password: str):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        cursor = await db.execute(
            """INSERT INTO servers
               (owner_id, name, description, ip, password, status, is_private)
               VALUES (?, ?, ?, ?, ?, 'pending', 0)""",
            (owner_id, name, description, ip, password),
        )
        await db.commit()
        mark_backup()
        return cursor.lastrowid


async def get_pending_servers():
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM servers WHERE status = 'pending'"
        ) as cursor:
            return await cursor.fetchall()


async def get_approved_servers():
    """Возвращает одобренные серверы, попутно снимая офлайн у просроченных."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            """UPDATE servers SET online = 0, expires_at = NULL
               WHERE online = 1
                 AND expires_at IS NOT NULL
                 AND expires_at <= datetime('now')"""
        )
        await db.commit()
        

        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM servers WHERE status = 'approved' ORDER BY online DESC, created_at DESC"
        ) as cursor:
            return await cursor.fetchall()


async def set_server_status(server_id: int, status: str):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "UPDATE servers SET status = ? WHERE id = ?",
            (status, server_id),
        )
        await db.commit()
        mark_backup()

async def set_server_online(server_id: int):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            """UPDATE servers SET online = 1,
               expires_at = datetime('now', '+1 hour')
               WHERE id = ?""",
            (server_id,),
        )
        await db.commit()
        mark_backup()

async def set_server_offline(server_id: int):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "UPDATE servers SET online = 0, expires_at = NULL WHERE id = ?",
            (server_id,),
        )
        await db.commit()
        mark_backup()

async def toggle_server_private(server_id: int) -> int:
    """Переключает тип сервера. Возвращает новое значение is_private."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "UPDATE servers SET is_private = CASE WHEN is_private = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (server_id,),
        )
        
        await db.commit()
        mark_backup()
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT is_private FROM servers WHERE id = ?", (server_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["is_private"] if row else 0


async def update_server_password(server_id: int, password: str):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "UPDATE servers SET password = ? WHERE id = ?",
            (password, server_id),
        )
        await db.commit()
        mark_backup()

async def get_server_by_id(server_id: int):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM servers WHERE id = ?", (server_id,)
        ) as cursor:
            return await cursor.fetchone()


async def delete_server(server_id: int, owner_id: int) -> bool:
    """Удаляет сервер. Возвращает True если строка была удалена."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("DELETE FROM subscriptions WHERE server_id = ?", (server_id,))
        await db.execute("DELETE FROM password_requests WHERE server_id = ?", (server_id,))
        await db.execute("DELETE FROM server_bans WHERE server_id = ?", (server_id,))
        cursor = await db.execute(
            "DELETE FROM servers WHERE id = ? AND owner_id = ?",
            (server_id, owner_id),
        )
        await db.commit()
        mark_backup()
        return cursor.rowcount > 0


async def delete_rejected_servers(owner_id: int):
    """Удаляет все отклонённые серверы пользователя (перед созданием нового)."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        async with db.execute(
            "SELECT id FROM servers WHERE owner_id = ? AND status = 'rejected'",
            (owner_id,),
        ) as cur:
            rows = await cur.fetchall()
        for row in rows:
            await db.execute("DELETE FROM subscriptions WHERE server_id = ?", (row[0],))
            await db.execute("DELETE FROM password_requests WHERE server_id = ?", (row[0],))
            await db.execute("DELETE FROM server_bans WHERE server_id = ?", (row[0],))
        await db.execute(
            "DELETE FROM servers WHERE owner_id = ? AND status = 'rejected'",
            (owner_id,),
        )
        await db.commit()
        mark_backup()


# ── Редактирование данных сервера (название / описание / IP) ──────────────────
# Правки уходят на модерацию так же, как аватарка: сохраняются в pending_*
# колонках, реальные данные меняются только после approve_server_edit().

async def request_server_edit(server_id: int, field: str, new_value: str):
    """Сохраняет предложенное значение поля (name/description/ip) как ожидающее модерации."""
    column = {
        "name": "pending_name",
        "description": "pending_description",
        "ip": "pending_ip",
    }[field]
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            f"UPDATE servers SET {column} = ? WHERE id = ?",
            (new_value, server_id),
        )
        await db.commit()
        mark_backup()


def has_pending_edit(server_row) -> bool:
    """Проверяет, есть ли у уже загруженной строки сервера ожидающая правка.
    Синхронная функция — просто читает поля из уже полученной строки,
    в БД не ходит."""
    keys = server_row.keys()
    return any(
        server_row[col] for col in ("pending_name", "pending_description", "pending_ip")
        if col in keys
    )


async def get_servers_with_pending_edits():
    """Серверы, у которых есть хотя бы одно поле на модерации."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM servers
               WHERE pending_name IS NOT NULL
                  OR pending_description IS NOT NULL
                  OR pending_ip IS NOT NULL"""
        ) as cursor:
            return await cursor.fetchall()


async def approve_server_edit(server_id: int):
    """Переносит все pending_* значения в реальные колонки и очищает pending_*."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            """UPDATE servers SET
                   name        = COALESCE(pending_name, name),
                   description = COALESCE(pending_description, description),
                   ip          = COALESCE(pending_ip, ip),
                   pending_name = NULL,
                   pending_description = NULL,
                   pending_ip = NULL
               WHERE id = ?""",
            (server_id,),
        )
        await db.commit()
        mark_backup()


async def reject_server_edit(server_id: int):
    """Отклоняет правку: просто очищает pending_* колонки, реальные данные не трогает."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            """UPDATE servers SET
                   pending_name = NULL,
                   pending_description = NULL,
                   pending_ip = NULL
               WHERE id = ?""",
            (server_id,),
        )
        await db.commit()
        mark_backup()


# ── Подписки ──────────────────────────────────────────────────────────────────

async def subscribe(user_id: int, server_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        try:
            await db.execute(
                "INSERT INTO subscriptions (user_id, server_id) VALUES (?, ?)",
                (user_id, server_id),
            )
            await db.commit()
            mark_backup()
            return True
        except aiosqlite.IntegrityError:
            return False


async def unsubscribe(user_id: int, server_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        cursor = await db.execute(
            "DELETE FROM subscriptions WHERE user_id = ? AND server_id = ?",
            (user_id, server_id),
        )
        await db.commit()
        mark_backup()
        return cursor.rowcount > 0


async def is_subscribed(user_id: int, server_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        async with db.execute(
            "SELECT 1 FROM subscriptions WHERE user_id = ? AND server_id = ?",
            (user_id, server_id),
        ) as cursor:
            return await cursor.fetchone() is not None


async def get_subscribers(server_id: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        async with db.execute(
            "SELECT user_id FROM subscriptions WHERE server_id = ?",
            (server_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


# ── Аватарки серверов ─────────────────────────────────────────────────────────

async def set_avatar_pending(server_id: int, file_id: str):
    """Сохраняет file_id как ожидающую модерации аватарку."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "UPDATE servers SET avatar_pending_file_id = ? WHERE id = ?",
            (file_id, server_id),
        )
        await db.commit()
        mark_backup()


async def approve_avatar(server_id: int):
    """Одобряет аватарку: pending → approved, очищает pending."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            """UPDATE servers
               SET avatar_file_id = avatar_pending_file_id,
                   avatar_pending_file_id = NULL
               WHERE id = ?""",
            (server_id,),
        )
        await db.commit()
        mark_backup()


async def reject_avatar(server_id: int):
    """Отклоняет аватарку: очищает pending, approved остаётся."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "UPDATE servers SET avatar_pending_file_id = NULL WHERE id = ?",
            (server_id,),
        )
        await db.commit()
        mark_backup()


async def delete_avatar(server_id: int):
    """Полностью удаляет аватарку (approved + pending)."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "UPDATE servers SET avatar_file_id = NULL, avatar_pending_file_id = NULL WHERE id = ?",
            (server_id,),
        )
        await db.commit()
        mark_backup()


async def get_servers_with_pending_avatars():
    """Серверы с аватаркой, ожидающей модерации."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM servers WHERE avatar_pending_file_id IS NOT NULL"
        ) as cursor:
            return await cursor.fetchall()


# ── Запросы пароля ────────────────────────────────────────────────────────────

async def create_pwd_request(server_id: int, requester_id: int) -> int:
    """Создаёт запрос пароля. Возвращает id записи."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        cursor = await db.execute(
            "INSERT INTO password_requests (server_id, requester_id, status) VALUES (?, ?, 'pending')",
            (server_id, requester_id),
        )
        await db.commit()
        mark_backup()
        return cursor.lastrowid


async def get_pwd_request(request_id: int):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM password_requests WHERE id = ?", (request_id,)
        ) as cursor:
            return await cursor.fetchone()


async def get_pending_pwd_request(server_id: int, requester_id: int):
    """Ищет ожидающий запрос от этого пользователя на этот сервер."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM password_requests
               WHERE server_id = ? AND requester_id = ? AND status = 'pending'
               ORDER BY created_at DESC LIMIT 1""",
            (server_id, requester_id),
        ) as cursor:
            return await cursor.fetchone()


async def resolve_pwd_request(request_id: int, status: str):
    """Меняет статус запроса на 'approved' или 'rejected'."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "UPDATE password_requests SET status = ? WHERE id = ?",
            (status, request_id),
        )
        await db.commit()
        mark_backup()


# ── Серверные баны ────────────────────────────────────────────────────────────

async def ban_server_user(server_id: int, user_id: int) -> bool:
    """Банит пользователя на сервере. False если уже забанен."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        try:
            await db.execute(
                "INSERT INTO server_bans (server_id, banned_user_id) VALUES (?, ?)",
                (server_id, user_id),
            )
            await db.commit()
            mark_backup()
            return True
        except aiosqlite.IntegrityError:
            return False


async def unban_server_user(server_id: int, user_id: int) -> bool:
    """Разбанивает пользователя на сервере. False если не был забанен."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        cursor = await db.execute(
            "DELETE FROM server_bans WHERE server_id = ? AND banned_user_id = ?",
            (server_id, user_id),
        )
        await db.commit()
        mark_backup()
        return cursor.rowcount > 0


async def unban_server_user_by_ban_id(ban_id: int) -> tuple[int, int] | None:
    """Разбанивает по ID записи. Возвращает (server_id, user_id) или None."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT server_id, banned_user_id FROM server_bans WHERE id = ?", (ban_id,)
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return None
        await db.execute("DELETE FROM server_bans WHERE id = ?", (ban_id,))
        await db.commit()
        mark_backup()
        return row["server_id"], row["banned_user_id"]


async def is_server_banned(server_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        async with db.execute(
            "SELECT 1 FROM server_bans WHERE server_id = ? AND banned_user_id = ?",
            (server_id, user_id),
        ) as cur:
            return await cur.fetchone() is not None


async def get_server_bans(server_id: int) -> list:
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM server_bans WHERE server_id = ? ORDER BY created_at DESC",
            (server_id,),
        ) as cur:
            return await cur.fetchall()


async def get_server_ban_by_id(ban_id: int):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM server_bans WHERE id = ?", (ban_id,)
        ) as cur:
            return await cur.fetchone()


# ── Глобальные баны (бот) ──────────────────────────────────────────────────────

async def ban_user_globally(user_id: int) -> bool:
    """Глобально банит пользователя. False если уже забанен."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        try:
            await db.execute(
                "INSERT INTO bot_bans (user_id) VALUES (?)", (user_id,)
            )
            await db.commit()
            mark_backup()
            return True
        except aiosqlite.IntegrityError:
            return False


async def unban_user_globally(user_id: int) -> bool:
    """Снимает глобальный бан. False если не был забанен."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        cursor = await db.execute(
            "DELETE FROM bot_bans WHERE user_id = ?", (user_id,)
        )
        await db.commit()
        mark_backup()
        return cursor.rowcount > 0


async def is_globally_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        async with db.execute(
            "SELECT 1 FROM bot_bans WHERE user_id = ?", (user_id,)
        ) as cur:
            return await cur.fetchone() is not None


async def get_global_bans() -> list:
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM bot_bans ORDER BY created_at DESC"
        ) as cur:
            return await cur.fetchall()


# ── Логи ──────────────────────────────────────────────────────────────────────

LOG_LABELS = {
    "server_created":           "📝 Сервер создан",
    "server_approved":          "✅ Сервер одобрен",
    "server_rejected":          "❌ Сервер отклонён",
    "server_deleted":           "🗑 Сервер удалён",
    "server_online":            "🟢 Сервер включён",
    "server_offline":           "⚫ Сервер выключен",
    "server_type_changed":      "🔒 Тип сервера изменён",
    "password_changed":         "🔑 Пароль изменён",
    "password_requested":       "🔐 Пароль запрошен (открытый)",
    "pwd_request_sent":         "📨 Запрос пароля отправлен",
    "pwd_request_approved":     "✅ Запрос пароля одобрен",
    "pwd_request_rejected":     "❌ Запрос пароля отклонён",
    "subscribed":               "🔔 Подписка",
    "unsubscribed":             "🔕 Отписка",
    "avatar_uploaded":          "🖼 Аватарка загружена",
    "avatar_approved":          "✅ Аватарка одобрена",
    "avatar_rejected":          "❌ Аватарка отклонена",
    "server_ban":               "🚫 Серверный бан",
    "server_unban":             "✅ Серверный разбан",
    "global_ban":               "🚫 Глобальный бан",
    "global_unban":             "✅ Глобальный разбан",
    "edit_requested":           "✏️ Правка отправлена на модерацию",
    "edit_approved":            "✅ Правка одобрена",
    "edit_rejected":            "❌ Правка отклонена",
}


async def add_log(event: str, actor_id: int | None = None,
                  server_id: int | None = None, details: str | None = None):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "INSERT INTO admin_logs (event, actor_id, server_id, details) VALUES (?, ?, ?, ?)",
            (event, actor_id, server_id, details),
        )
        await db.commit()
        mark_backup()


async def get_logs(limit: int = 40):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT ?", (limit,)
        ) as cursor:
            return await cursor.fetchall()

async def set_language(telegram_id: int, language: str):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute(
            "UPDATE users SET language = ? WHERE telegram_id = ?",
            (language, telegram_id),
        )
        await db.commit()
        mark_backup()

async def get_language(telegram_id: int) -> str:
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        async with db.execute(
            "SELECT language FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ) as cursor:
            row = await cursor.fetchone()

            if row and row[0]:
                return row[0]

            return "ru"
async def get_server_by_name(name: str):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")

        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT * FROM servers WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))",
            (name,),
        ) as cursor:
            return await cursor.fetchone()
