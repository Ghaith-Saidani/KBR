import httpx
import pytest

from backend.app.ai.gateway import ModelGateway
from backend.app.ai.providers.groq import GroqProvider
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
        ai_provider="groq",
        ai_api_key="test-api-key",
        ai_model="test-model",
    )


@pytest.mark.asyncio
async def test_gateway_can_use_groq_provider():
    settings = create_settings()

    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "model": "test-model",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                "KBR AI is ready."
                            ),
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
        == "KBR AI is ready."
    )

    assert response.provider == "groq"

    assert response.model == "test-model"