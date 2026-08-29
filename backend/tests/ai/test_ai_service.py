import pytest

from backend.app.ai.gateway import ModelGateway
from backend.app.ai.schemas import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
)
from backend.app.ai.services import AIService


class FakeGateway:
    def __init__(self) -> None:
        self.received_request = None

    async def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        self.received_request = request

        return ModelResponse(
            content="Hello from AI service.",
            model="test-model",
            provider="fake",
        )


@pytest.mark.asyncio
async def test_ai_service_delegates_to_gateway():
    gateway = FakeGateway()

    service = AIService(
        gateway=gateway,
    )

    request = ModelRequest(
        messages=[
            ModelMessage(
                role="user",
                content="Hello",
            ),
        ],
    )

    response = await service.generate(
        request,
    )

    assert response.content == "Hello from AI service."

    assert response.model == "test-model"

    assert response.provider == "fake"

    assert gateway.received_request is request