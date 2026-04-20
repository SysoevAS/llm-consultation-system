from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.core.config import settings


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp


def build_bot() -> Bot:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    return Bot(token=settings.telegram_bot_token)