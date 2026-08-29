import httpx
import pytest

from backend.app.ai.gateway import ModelGateway
from backend.app.ai.providers.gemini import GeminiProvider
from backend.app.ai.schemas import (
    ModelMessage,
    ModelRequest,
)
from backend.app.core.config import Settings


def create_settings() -> Settings:
    return Settings(
        postgres_password="test-password",
        jwt_secret_key=(
            "test-secret-key-that-is-long-enough"
        ),
        ai_provider="gemini",
        ai_api_key="test-gemini-api-key",
        gemini_model="gemini-2.5-flash",
    )


@pytest.mark.asyncio
async def test_gateway_can_use_gemini_provider():
    settings = create_settings()

    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
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
                                        "KBR Gemini is ready."
                                    )
                                }
                            ],
                        },
                        "finishReason": "STOP",
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

        gateway = ModelGateway(
            provider,
        )

        request = ModelRequest(
            messages=[
                ModelMessage(
                    role="user",
                    content="Are you ready?",
                ),
            ],
        )

        response = await gateway.generate(
            request,
        )

    assert (
        response.content
        == "KBR Gemini is ready."
    )

    assert response.provider == "gemini"

    assert (
        response.model
        == "gemini-2.5-flash"
    )