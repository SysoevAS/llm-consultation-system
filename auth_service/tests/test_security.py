from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_not_equal_to_source():
    password = "strongpass123"
    password_hash = hash_password(password)

    assert password_hash != password
    assert isinstance(password_hash, str)
    assert len(password_hash) > 0


def test_verify_password_success():
    password = "strongpass123"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_verify_password_fail():
    password_hash = hash_password("strongpass123")

    assert verify_password("wrongpass123", password_hash) is False


def test_create_and_decode_token():
    token = create_access_token(
        sub="123",
        role="user",
    )

    payload = decode_token(token)

    assert payload["sub"] == "123"
    assert payload["role"] == "user"
    assert "iat" in payload
    assert "exp" in payload