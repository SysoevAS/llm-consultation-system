import asyncio

from app.bot.dispatcher import build_bot, build_dispatcher


async def main() -> None:
    bot = build_bot()
    dp = build_dispatcher()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())