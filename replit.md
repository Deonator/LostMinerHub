# LostMiner Bot

Telegram-бот — каталог игровых серверов для LostMiner. Пользователи регистрируются, создают серверы, проходят модерацию и включают их онлайн на 1 час.

## Run & Operate

- `python bot/bot.py` — запустить бота
- Бот хранит данные в `bot/lostminer.db` (SQLite, создаётся автоматически)

## Настройка перед запуском

1. Открой `bot/config.py`
2. Замени `BOT_TOKEN` на токен от @BotFather
3. Замени `ADMIN_ID` на свой Telegram ID (узнать у @userinfobot)
4. Запусти воркфлоу **LostMiner Bot**

## Stack

- Python 3.13
- aiogram 3.14 (Telegram Bot framework)
- aiosqlite (асинхронный SQLite)

## Where things live

- `bot/bot.py` — основной файл бота, все хендлеры
- `bot/database.py` — все операции с БД
- `bot/config.py` — токен бота и ID администратора
- `bot/lostminer.db` — база данных SQLite (создаётся при первом запуске)

## Architecture decisions

- FSM (Finite State Machine) через aiogram для пошагового создания сервера
- Inline-кнопки для модерации и выбора сервера
- Онлайн-статус автоматически снимается при запросе списка (без фонового планировщика)
- Один файл бота — чистый MVP без лишних слоёв абстракции

## Product

- `/start` — регистрация
- `/создать` — пошаговое создание сервера (5 шагов: название, описание, IP, порт, пароль)
- `/серверы` — список одобренных серверов с онлайн-статусом
- `/включить` — включить свой сервер на 1 час
- `/админ` — панель модерации для ADMIN_ID (одобрить/отклонить)
- `/отмена` — отменить текущее действие

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- Перед запуском обязательно заполнить `bot/config.py`
- При добавлении новых пакетов — `pip install -r bot/requirements.txt`
