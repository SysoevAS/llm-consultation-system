from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.filters import CommandObject
from jose import jwt

from app.bot.handlers import cmd_token, handle_user_text
from app.core.config import settings


def build_valid_token() -> str:
    return jwt.encode(
        {
            "sub": "1",
            "role": "user",
            "iat": 1776700000,
            "exp": 2776700000,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )


def build_fake_message(
    *,
    text: str,
    user_id: int = 12345,
    chat_id: int = 999,
):
    return SimpleNamespace(
        text=text,
        from_user=SimpleNamespace(id=user_id),
        chat=SimpleNamespace(id=chat_id),
        answer=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_cmd_token_saves_token_in_redis(fake_redis, mocker):
    token = build_valid_token()
    message = build_fake_message(text=f"/token {token}")

    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)

    command = CommandObject(
        prefix="/",
        command="token",
        mention=None,
        args=token,
    )

    await cmd_token(message, command)

    saved_token = await fake_redis.get(f"token:{message.from_user.id}")
    assert saved_token == token

    message.answer.assert_awaited_once_with(
        "Токен сохранён. Теперь можно отправлять запросы модели."
    )


@pytest.mark.asyncio
async def test_handle_user_text_without_token(fake_redis, mocker):
    message = build_fake_message(text="Привет, бот")

    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")

    await handle_user_text(message)

    delay_mock.assert_not_called()
    message.answer.assert_awaited_once()

    answer_text = message.answer.await_args.args[0]
    assert "Нет JWT-токена" in answer_text


@pytest.mark.asyncio
async def test_handle_user_text_with_valid_token_calls_celery(fake_redis, mocker):
    token = build_valid_token()
    message = build_fake_message(text="Напиши годы жизни Толстого")

    await fake_redis.set(f"token:{message.from_user.id}", token)

    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")

    await handle_user_text(message)

    delay_mock.assert_called_once_with(
        tg_chat_id=message.chat.id,
        prompt=message.text,
    )
    message.answer.assert_awaited_once_with(
        "Запрос принят. Ответ придёт следующим сообщением."
    )


@pytest.mark.asyncio
async def test_handle_user_text_with_invalid_token_deletes_it(fake_redis, mocker):
    message = build_fake_message(text="Что-нибудь")
    await fake_redis.set(f"token:{message.from_user.id}", "bad.token.value")

    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")

    await handle_user_text(message)

    delay_mock.assert_not_called()
    assert await fake_redis.get(f"token:{message.from_user.id}") is None

    message.answer.assert_awaited_once()
    answer_text = message.answer.await_args.args[0]
    assert "Токен невалиден или истёк" in answer_text