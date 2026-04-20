from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from app.core.jwt import decode_and_validate
from app.infra.redis import get_redis
from app.tasks.llm_tasks import llm_request

router = Router()


def build_token_key(tg_user_id: int) -> str:
    return f"token:{tg_user_id}"


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет.\n"
        "Сначала отправь JWT командой:\n"
        "/token <jwt>\n\n"
        "После этого просто отправь вопрос, и я передам его модели."
    )


@router.message(Command("token"))
async def cmd_token(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return

    token = (command.args or "").strip()

    if not token:
        await message.answer("Нужно прислать токен так: /token <jwt>")
        return

    try:
        decode_and_validate(token)
    except ValueError as exc:
        await message.answer(f"Токен не принят: {exc}")
        return

    redis = get_redis()
    await redis.set(build_token_key(message.from_user.id), token)

    await message.answer(
        "Токен сохранён. Теперь можно отправлять запросы модели."
    )


@router.message(F.text & ~F.text.startswith("/"))
async def handle_user_text(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    redis = get_redis()
    token_key = build_token_key(message.from_user.id)
    token = await redis.get(token_key)

    if not token:
        await message.answer(
            "Нет JWT-токена. Сначала получи токен в Auth Service и отправь:\n"
            "/token <jwt>"
        )
        return

    try:
        decode_and_validate(token)
    except ValueError:
        await redis.delete(token_key)
        await message.answer(
            "Токен невалиден или истёк. Отправь новый через /token <jwt>."
        )
        return

    llm_request.delay(
        tg_chat_id=message.chat.id,
        prompt=message.text,
    )

    await message.answer(
        "Запрос принят. Ответ придёт следующим сообщением."
    )