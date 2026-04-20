import pytest
import respx
from httpx import Response

from app.core.config import settings
from app.services.openrouter_client import call_openrouter


@pytest.mark.asyncio
@respx.mock
async def test_call_openrouter_success(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(settings, "openrouter_base_url", "https://openrouter.ai/api/v1")
    monkeypatch.setattr(settings, "openrouter_model", "openrouter/auto")
    monkeypatch.setattr(settings, "openrouter_site_url", "https://example.com")
    monkeypatch.setattr(settings, "openrouter_app_name", "bot-service-test")

    route = respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Лев Толстой жил с 1828 по 1910 год."
                        }
                    }
                ]
            },
        )
    )

    result = await call_openrouter("Напиши годы жизни Толстого")

    assert route.called is True
    assert result == "Лев Толстой жил с 1828 по 1910 год."


@pytest.mark.asyncio
@respx.mock
async def test_call_openrouter_non_200(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(settings, "openrouter_base_url", "https://openrouter.ai/api/v1")
    monkeypatch.setattr(settings, "openrouter_model", "openrouter/auto")
    monkeypatch.setattr(settings, "openrouter_site_url", "https://example.com")
    monkeypatch.setattr(settings, "openrouter_app_name", "bot-service-test")

    respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(
            404,
            json={
                "error": {
                    "message": "Model not found",
                    "code": 404,
                }
            },
        )
    )

    with pytest.raises(RuntimeError, match="OpenRouter request failed"):
        await call_openrouter("Привет")