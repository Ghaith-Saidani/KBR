import json

import httpx
import pytest

from backend.app.ai.providers.gemini import GeminiProvider
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
        "ai_provider": "gemini",
        "ai_api_key": "test-gemini-api-key",
        "gemini_model": "gemini-2.5-flash",
        "gemini_base_url": (
            "https://generativelanguage.googleapis.com/v1beta"
        ),
        "ai_timeout_seconds": 30,
        "ai_temperature": 0.2,
    }

    values.update(overrides)

    return Settings(**values)


@pytest.mark.asyncio
async def test_gemini_provider_sends_generate_content_request():
    settings = create_settings()

    captured = {}

    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["json"] = json.loads(
            request.content
        )

        return httpx.Response(
            status_code=200,
            json={
                "modelVersion": "gemini-2.5-flash",
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [
                                {
                                    "text": (
                                        "Hello from Gemini."
                                    )
                                }
                            ],
                        },
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 10,
                    "candidatesTokenCount": 5,
                    "totalTokenCount": 15,
                },
            },
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
    ) as client:
        provider = GeminiProvider(
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
        == (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-2.5-flash:generateContent"
        )
    )

    assert (
        captured["headers"]["x-goog-api-key"]
        == "test-gemini-api-key"
    )

    assert (
        captured["json"]["contents"]
        == [
            {
                "role": "user",
                "parts": [
                    {
                        "text": "Hello",
                    }
                ],
            }
        ]
    )

    assert (
        captured["json"]["generationConfig"]
        ["temperature"]
        == 0.2
    )

    assert (
        response.content
        == "Hello from Gemini."
    )

    assert response.provider == "gemini"

    assert (
        response.model
        == "gemini-2.5-flash"
    )

    assert response.finish_reason == "STOP"

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
async def test_gemini_provider_uses_request_model():
    settings = create_settings(
        gemini_model="default-model",
    )

    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert (
            str(request.url)
            == (
                "https://generativelanguage.googleapis.com/"
                "v1beta/models/request-model:generateContent"
            )
        )

        return httpx.Response(
            status_code=200,
            json={
                "modelVersion": "request-model",
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": (
                                        "Custom model response."
                                    )
                                }
                            ]
                        }
                    }
                ],
            },
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
    ) as client:
        provider = GeminiProvider(
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
async def test_gemini_provider_uses_system_instruction():
    settings = create_settings()

    captured = {}

    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        captured["json"] = json.loads(
            request.content
        )

        return httpx.Response(
            status_code=200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "Hello."
                                }
                            ]
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
    ) as client:
        provider = GeminiProvider(
            settings=settings,
            client=client,
        )

        request = ModelRequest(
            messages=[
                ModelMessage(
                    role="system",
                    content=(
                        "You are the KBR assistant."
                    ),
                ),
                ModelMessage(
                    role="user",
                    content="Hello",
                ),
            ],
        )

        await provider.generate(
            request,
        )

    assert (
        captured["json"]["systemInstruction"]
        == {
            "parts": [
                {
                    "text": (
                        "You are the KBR assistant."
                    )
                }
            ]
        }
    )


@pytest.mark.asyncio
async def test_gemini_provider_maps_assistant_to_model():
    settings = create_settings()

    captured = {}

    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        captured["json"] = json.loads(
            request.content
        )

        return httpx.Response(
            status_code=200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "Follow-up."
                                }
                            ]
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
    ) as client:
        provider = GeminiProvider(
            settings=settings,
            client=client,
        )

        request = ModelRequest(
            messages=[
                ModelMessage(
                    role="user",
                    content="Hello",
                ),
                ModelMessage(
                    role="assistant",
                    content="Hi there.",
                ),
                ModelMessage(
                    role="user",
                    content="Continue.",
                ),
            ],
        )

        await provider.generate(
            request,
        )

    assert (
        captured["json"]["contents"][1]["role"]
        == "model"
    )


@pytest.mark.asyncio
async def test_gemini_provider_requires_api_key():
    settings = create_settings(
        ai_api_key=None,
        gemini_api_key=None,
    )

    provider = GeminiProvider(
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
        match="GEMINI_API_KEY is not configured",
    ):
        await provider.generate(
            request,
        )


@pytest.mark.asyncio
async def test_gemini_provider_accepts_gemini_specific_api_key():
    settings = create_settings(
        ai_api_key=None,
        gemini_api_key="gemini-specific-key",
    )

    captured = {}

    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        captured["key"] = request.headers[
            "x-goog-api-key"
        ]

        return httpx.Response(
            status_code=200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "Hello."
                                }
                            ]
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
    ) as client:
        provider = GeminiProvider(
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

        await provider.generate(
            request,
        )

    assert (
        captured["key"]
        == "gemini-specific-key"
    )


@pytest.mark.asyncio
async def test_gemini_provider_raises_for_http_errors():
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
        provider = GeminiProvider(
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


def test_gemini_provider_maps_assistant_role():
    assert (
        GeminiProvider._normalize_role(
            "assistant"
        )
        == "model"
    )


def test_gemini_provider_keeps_user_role():
    assert (
        GeminiProvider._normalize_role(
            "user"
        )
        == "user"
    )