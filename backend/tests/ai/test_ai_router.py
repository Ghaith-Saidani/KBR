import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.app.ai.dependencies import get_ai_service
from backend.app.ai.router import router
from backend.app.ai.schemas import ModelRequest, ModelResponse


class FakeAIService:
    async def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        return ModelResponse(
            content="KBR AI test response.",
            model="test-model",
            provider="fake",
        )


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    app.include_router(
        router,
    )

    app.dependency_overrides[
        get_ai_service
    ] = lambda: FakeAIService()

    return app


@pytest.mark.asyncio
async def test_ai_chat_endpoint(app: FastAPI):
    transport = ASGITransport(
        app=app,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/ai/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello KBR AI",
                    }
                ]
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["content"] == "KBR AI test response."
    assert data["model"] == "test-model"
    assert data["provider"] == "fake"


@pytest.mark.asyncio
async def test_ai_chat_endpoint_requires_messages(
    app: FastAPI,
):
    transport = ASGITransport(
        app=app,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/ai/chat",
            json={},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ai_chat_endpoint_rejects_client_model(
    app: FastAPI,
):
    transport = ASGITransport(
        app=app,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/ai/chat",
            json={
                "model": "custom-model",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello",
                    }
                ],
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ai_chat_endpoint_accepts_temperature(
    app: FastAPI,
):
    received_request: ModelRequest | None = None

    class TemperatureService:
        async def generate(
            self,
            request: ModelRequest,
        ) -> ModelResponse:
            nonlocal received_request

            received_request = request

            return ModelResponse(
                content="Temperature test.",
                model="test-model",
                provider="fake",
            )

    app.dependency_overrides[
        get_ai_service
    ] = lambda: TemperatureService()

    transport = ASGITransport(
        app=app,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/ai/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello",
                    }
                ],
                "temperature": 0.7,
            },
        )

    assert response.status_code == 200

    assert received_request is not None
    assert received_request.temperature == 0.7


@pytest.mark.asyncio
async def test_ai_chat_endpoint_accepts_max_tokens(
    app: FastAPI,
):
    received_request: ModelRequest | None = None

    class MaxTokensService:
        async def generate(
            self,
            request: ModelRequest,
        ) -> ModelResponse:
            nonlocal received_request

            received_request = request

            return ModelResponse(
                content="Max tokens test.",
                model="test-model",
                provider="fake",
            )

    app.dependency_overrides[
        get_ai_service
    ] = lambda: MaxTokensService()

    transport = ASGITransport(
        app=app,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/ai/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello",
                    }
                ],
                "max_tokens": 100,
            },
        )

    assert response.status_code == 200

    assert received_request is not None
    assert received_request.max_tokens == 100