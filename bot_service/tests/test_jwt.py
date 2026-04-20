import pytest
from jose import jwt

from app.core.config import settings
from app.core.jwt import decode_and_validate


def test_decode_and_validate_valid_token():
    token = jwt.encode(
        {
            "sub": "123",
            "role": "user",
            "iat": 1776700000,
            "exp": 2776700000,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )

    payload = decode_and_validate(token)

    assert payload["sub"] == "123"
    assert payload["role"] == "user"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_and_validate_invalid_token():
    with pytest.raises(ValueError, match="Invalid token"):
        decode_and_validate("not.a.valid.token")


def test_decode_and_validate_without_sub():
    token = jwt.encode(
        {
            "role": "user",
            "iat": 1776700000,
            "exp": 2776700000,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )

    with pytest.raises(ValueError, match="sub"):
        decode_and_validate(token)