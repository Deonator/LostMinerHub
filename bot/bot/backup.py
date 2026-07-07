import asyncio
import shutil
import os
from datetime import datetime

DB = "bot/lostminer.db"
BACKUP_DIR = "bot/backups"


async def backup_loop():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    while True:
        try:
            if os.path.exists(DB):
                filename = datetime.now().strftime(
                    "backup_%Y-%m-%d_%H-%M-%S.db"
                )

                path = os.path.join(BACKUP_DIR, filename)

                shutil.copy2(DB, path)

                print(f"✅ Бэкап создан: {filename}")

                # удаляем старые (оставляем последние 20)
                backups = sorted(
                    os.listdir(BACKUP_DIR),
                    reverse=True
                )

                for old in backups[20:]:
                    os.remove(
                        os.path.join(BACKUP_DIR, old)
                    )

        except Exception as e:
            print("Ошибка backup:", e)

        await asyncio.sleep(120)
