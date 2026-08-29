import httpx
import pytest
import json

from backend.app.ai.providers.groq import GroqProvider
from backend.app.ai.schemas import (
    ModelMessage,
    ModelRequest,
)
from backend.app.core.config import Settings


def create_settings(
    **overrides,
) -> Settings:
    values = {
        "postgres_password": "test-password",
        "jwt_secret_key": (
            "test-secret-key-that-is-long-enough"
        ),
        "ai_api_key": "test-api-key",
        "ai_model": "test-model",
        "ai_base_url": (
            "https://api.groq.com/openai/v1"
        ),
        "ai_timeout_seconds": 30,
        "ai_temperature": 0.2,
    }

    values.update(overrides)

    return Settings(**values)


@pytest.mark.asyncio
async def test_groq_provider_sends_chat_completion_request():
    settings = create_settings()

    captured = {}

    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["json"] = json.loads(request.content)

        return httpx.Response(
            status_code=200,
            json={
                "id": "test-completion",
                "object": "chat.completion",
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Hello from Groq.",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            },
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
    ) as client:
        provider = GroqProvider(
            settings=settings,
            client=client,
        )

        request = ModelRequest(
            messages=[
                ModelMessage(
                    role="user",
                    content="Hello",
                ),
            ],
        )

        response = await provider.generate(
            request,
        )

    assert captured["method"] == "POST"

    assert (
        captured["url"]
        == "https://api.groq.com/openai/v1/chat/completions"
    )

    assert (
        captured["headers"]["authorization"]
        == "Bearer test-api-key"
    )

    assert captured["json"]["model"] == "test-model"

    assert captured["json"]["messages"] == [
        {
            "role": "user",
            "content": "Hello",
        }
    ]

    assert (
        response.content
        == "Hello from Groq."
    )

    assert response.provider == "groq"

    assert response.model == "test-model"

    assert response.finish_reason == "stop"

    assert response.usage is not None

    assert (
        response.usage.prompt_tokens
        == 10
    )

    assert (
        response.usage.completion_tokens
        == 5
    )

    assert (
        response.usage.total_tokens
        == 15
    )


@pytest.mark.asyncio
async def test_groq_provider_uses_request_model_when_provided():
    settings = create_settings(
        ai_model="default-model",
    )

    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        body = json.loads(request.content)

        assert (
            body["model"]
            == "request-model"
        )

        return httpx.Response(
            status_code=200,
            json={
                "model": "request-model",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Custom model response.",
                        },
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
    ) as client:
        provider = GroqProvider(
            settings=settings,
            client=client,
        )

        request = ModelRequest(
            model="request-model",
            messages=[
                ModelMessage(
                    role="user",
                    content="Hello",
                ),
            ],
        )

        response = await provider.generate(
            request,
        )

    assert (
        response.model
        == "request-model"
    )


@pytest.mark.asyncio
async def test_groq_provider_uses_configured_model_by_default():
    settings = create_settings(
        ai_model="configured-model",
    )

    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        body = json.loads(request.content)

        assert (
            body["model"]
            == "configured-model"
        )

        return httpx.Response(
            status_code=200,
            json={
                "model": "configured-model",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Configured model response.",
                        },
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
    ) as client:
        provider = GroqProvider(
            settings=settings,
            client=client,
        )

        request = ModelRequest(
            messages=[
                ModelMessage(
                    role="user",
                    content="Hello",
                ),
            ],
        )

        response = await provider.generate(
            request,
        )

    assert (
        response.model
        == "configured-model"
    )


@pytest.mark.asyncio
async def test_groq_provider_requires_api_key():
    settings = create_settings(
        ai_api_key=None,
    )

    provider = GroqProvider(
        settings=settings,
    )

    request = ModelRequest(
        messages=[
            ModelMessage(
                role="user",
                content="Hello",
            ),
        ],
    )

    with pytest.raises(
        RuntimeError,
        match="AI_API_KEY is not configured",
    ):
        await provider.generate(
            request,
        )


@pytest.mark.asyncio
async def test_groq_provider_raises_for_http_errors():
    settings = create_settings()

    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=401,
            json={
                "error": {
                    "message": "Invalid API key",
                },
            },
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
    ) as client:
        provider = GroqProvider(
            settings=settings,
            client=client,
        )

        request = ModelRequest(
            messages=[
                ModelMessage(
                    role="user",
                    content="Hello",
                ),
            ],
        )

        with pytest.raises(
            httpx.HTTPStatusError,
        ):
            await provider.generate(
                request,
            )