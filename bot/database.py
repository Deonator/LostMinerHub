import aiosqlite
import os

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(telegram_id)
            )
        """)
        await db.commit()


async def register_user(telegram_id: int, username: str | None):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username),
        )
        await db.commit()


async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            return await cursor.fetchone()


async def get_any_server_by_owner(owner_id: int):
    """Любой сервер пользователя (любой статус). Для проверки лимита 1 сервер на юзера."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM servers WHERE owner_id = ? ORDER BY created_at DESC LIMIT 1",
            (owner_id,),
        ) as cursor:
            return await cursor.fetchone()


async def create_server(
    owner_id: int,
    name: str,
    description: str,
    ip: str,
    password: str,
):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            """INSERT INTO servers
               (owner_id, name, description, ip, password, status)
               VALUES (?, ?, ?, ?, ?, 'pending')""",
            (owner_id, name, description, ip, password),
        )
        await db.commit()


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
            "SELECT * FROM servers WHERE status = 'approved' ORDER BY online DESC, name ASC"
        ) as cursor:
            return await cursor.fetchall()


async def get_owner_servers(owner_id: int):
    """Одобренные серверы конкретного владельца."""
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM servers WHERE owner_id = ? AND status = 'approved'",
            (owner_id,),
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


async def set_server_offline(server_id: int):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "UPDATE servers SET online = 0, expires_at = NULL WHERE id = ?",
            (server_id,),
        )
        await db.commit()


async def update_server_password(server_id: int, password: str):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            "UPDATE servers SET password = ? WHERE id = ?",
            (password, server_id),
        )
        await db.commit()


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
        cursor = await db.execute(
            "DELETE FROM servers WHERE id = ? AND owner_id = ?",
            (server_id, owner_id),
        )
        await db.commit()
        return cursor.rowcount > 0
