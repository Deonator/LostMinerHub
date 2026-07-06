import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "lostminer.db")

# Параметры для повышения надёжности при параллельных запросах
CONNECT_KWARGS = {"timeout": 10}


async def _get_db():
    db = await aiosqlite.connect(DB_PATH, **CONNECT_KWARGS)
    await db.execute("PRAGMA journal_mode=WAL")
    db.row_factory = aiosqlite.Row
    return db


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
                port INTEGER NOT NULL,
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


async def create_server(
    owner_id: int,
    name: str,
    description: str,
    ip: str,
    port: int,
    password: str,
):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            """INSERT INTO servers
               (owner_id, name, description, ip, port, password, status)
               VALUES (?, ?, ?, ?, ?, ?, 'pending')""",
            (owner_id, name, description, ip, port, password),
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


async def get_server_by_id(server_id: int):
    async with aiosqlite.connect(DB_PATH, **CONNECT_KWARGS) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM servers WHERE id = ?", (server_id,)
        ) as cursor:
            return await cursor.fetchone()
