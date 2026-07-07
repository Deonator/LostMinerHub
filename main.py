def main():
    print("Hello from repl-nix-workspace!")


if __name__ == "__main__":
    main()
async def main():
    await init_db()

    asyncio.create_task(start_web())

    await dp.start_polling(bot)
