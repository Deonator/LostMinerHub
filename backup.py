import os
import base64
import aiohttp
import asyncio
import logging

DB_PATH = "bot/lostminer.db"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv(
    "GITHUB_REPO",
    "Deonator/LostMinerBackup"
)

FILE_PATH = "lostminer.db"

API_URL = (
    f"https://api.github.com/repos/"
    f"{GITHUB_REPO}/contents/{FILE_PATH}"
)


backup_lock = asyncio.Lock()


async def github_request(method, url, **kwargs):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    async with aiohttp.ClientSession(
        headers=headers
    ) as session:

        async with session.request(
            method,
            url,
            **kwargs
        ) as response:

            if response.status >= 400:
                text = await response.text()
                raise Exception(
                    f"GitHub error {response.status}: {text}"
                )

            return await response.json()



# =========================
# СКАЧИВАНИЕ БАЗЫ
# =========================

async def download_backup():

    try:

        async with backup_lock:

            data = await github_request(
                "GET",
                API_URL
            )


            content = data["content"]

            decoded = base64.b64decode(
                content
            )


            os.makedirs(
                "bot",
                exist_ok=True
            )


            with open(
                DB_PATH,
                "wb"
            ) as file:

                file.write(decoded)


            logging.info(
                "База восстановлена из GitHub"
            )


    except Exception as e:

        logging.warning(
            f"Не удалось скачать backup: {e}"
        )



# =========================
# ЗАГРУЗКА БАЗЫ
# =========================

async def upload_backup():

    try:

        async with backup_lock:

            with open(
                DB_PATH,
                "rb"
            ) as file:

                content = base64.b64encode(
                    file.read()
                ).decode()



            # Получаем SHA старого файла

            try:

                old = await github_request(
                    "GET",
                    API_URL
                )

                sha = old["sha"]


            except:

                sha = None



            body = {
                "message":
                    "Auto backup lostminer.db",

                "content":
                    content
            }


            if sha:
                body["sha"] = sha



            await github_request(
                "PUT",
                API_URL,
                json=body
            )


            logging.info(
                "Backup отправлен"
            )


    except Exception as e:

        logging.error(
            f"Ошибка backup: {e}"
        )



# =========================
# ЦИКЛ BACKUP
# =========================

async def backup_loop():

    while True:

        await asyncio.sleep(120)

        await upload_backup()
