import pytest

from backend.app.ai.gateway import ModelGateway
from backend.app.ai.prompts import KBR_SYSTEM_PROMPT
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

    assert gateway.received_request is not request


@pytest.mark.asyncio
async def test_ai_service_injects_kbr_system_prompt():
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

    await service.generate(
        request,
    )

    received = gateway.received_request

    assert received is not None

    assert received.messages[0].role == "system"

    assert (
        received.messages[0].content
        == KBR_SYSTEM_PROMPT
    )

    assert received.messages[1].role == "user"

    assert received.messages[1].content == "Hello"


@pytest.mark.asyncio
async def test_ai_service_preserves_existing_messages():
    gateway = FakeGateway()

    service = AIService(
        gateway=gateway,
    )

    request = ModelRequest(
        messages=[
            ModelMessage(
                role="user",
                content="First message",
            ),
            ModelMessage(
                role="assistant",
                content="Previous response",
            ),
            ModelMessage(
                role="user",
                content="Second message",
            ),
        ],
    )

    await service.generate(
        request,
    )

    received = gateway.received_request

    assert received is not None

    assert len(received.messages) == 4

    assert received.messages[0].role == "system"
    assert (
        received.messages[0].content
        == KBR_SYSTEM_PROMPT
    )

    assert received.messages[1].content == "First message"
    assert received.messages[2].content == "Previous response"
    assert received.messages[3].content == "Second message"


@pytest.mark.asyncio
async def test_ai_service_does_not_mutate_original_request():
    gateway = FakeGateway()

    service = AIService(
        gateway=gateway,
    )

    original_messages = [
        ModelMessage(
            role="user",
            content="Hello",
        ),
    ]

    request = ModelRequest(
        messages=original_messages,
    )

    await service.generate(
        request,
    )

    assert request.messages == original_messages

    assert len(request.messages) == 1
    assert request.messages[0].content == "Hello"


@pytest.mark.asyncio
async def test_ai_service_preserves_request_configuration():
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
        model="test-model",
        temperature=0.7,
        max_tokens=250,
        metadata={
            "source": "test",
        },
    )

    await service.generate(
        request,
    )

    received = gateway.received_request

    assert received is not None

    assert received.model == "test-model"
    assert received.temperature == 0.7
    assert received.max_tokens == 250
    assert received.metadata == {
        "source": "test",
    }