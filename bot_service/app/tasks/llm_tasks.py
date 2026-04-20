import asyncio

from aiogram import Bot

from app.core.config import settings
from app.infra.celery_app import celery_app
from app.services.openrouter_client import call_openrouter


async def _send_telegram_message(chat_id: int, text: str) -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    bot = Bot(token=settings.telegram_bot_token)
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    finally:
        await bot.session.close()


async def _process_llm_request(tg_chat_id: int, prompt: str) -> dict:
    try:
        answer = await call_openrouter(prompt)
    except Exception as exc:
        answer = f"Не удалось получить ответ от LLM: {exc}"

    await _send_telegram_message(tg_chat_id, answer)

    return {
        "status": "done",
        "tg_chat_id": tg_chat_id,
        "prompt": prompt,
    }


@celery_app.task(name="app.tasks.llm_tasks.llm_request")
def llm_request(tg_chat_id: int, prompt: str) -> dict:
    return asyncio.run(_process_llm_request(tg_chat_id, prompt))