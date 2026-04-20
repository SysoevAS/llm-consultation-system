import pytest


@pytest.mark.asyncio
async def test_register_login_me_flow(client):
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "sysoev@email.com",
            "password": "strongpass123",
        },
    )

    assert register_response.status_code == 201
    register_data = register_response.json()

    assert register_data["email"] == "sysoev@email.com"
    assert register_data["role"] == "user"
    assert "id" in register_data
    assert "created_at" in register_data
    assert "password_hash" not in register_data

    login_response = await client.post(
        "/auth/login",
        data={
            "username": "sysoev@email.com",
            "password": "strongpass123",
        },
    )

    assert login_response.status_code == 200
    login_data = login_response.json()

    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"

    token = login_data["access_token"]

    me_response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    me_data = me_response.json()

    assert me_data["email"] == "sysoev@email.com"
    assert me_data["role"] == "user"
    assert "id" in me_data
    assert "created_at" in me_data


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    payload = {
        "email": "sysoev@email.com",
        "password": "strongpass123",
    }

    first_response = await client.post("/auth/register", json=payload)
    second_response = await client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client):
    await client.post(
        "/auth/register",
        json={
            "email": "sysoev@email.com",
            "password": "strongpass123",
        },
    )

    login_response = await client.post(
        "/auth/login",
        data={
            "username": "sysoev@email.com",
            "password": "wrongpass123",
        },
    )

    assert login_response.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client):
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code == 401