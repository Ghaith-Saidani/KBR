import pytest

from backend.app.ai.gateway.model_gateway import ModelGateway
from backend.app.ai.providers.base import ModelProvider
from backend.app.ai.schemas import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
)


class FakeModelProvider(ModelProvider):
    name = "fake"

    async def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        return ModelResponse(
            content="Hello from the fake provider.",
            model=request.model or "fake-model",
            provider=self.name,
        )


@pytest.mark.asyncio
async def test_model_gateway_delegates_to_provider():
    provider = FakeModelProvider()
    gateway = ModelGateway(provider)

    request = ModelRequest(
        messages=[
            ModelMessage(
                role="user",
                content="Hello",
            ),
        ],
    )

    response = await gateway.generate(request)

    assert response.content == "Hello from the fake provider."
    assert response.provider == "fake"
    assert response.model == "fake-model"