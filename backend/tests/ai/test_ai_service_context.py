import pytest

from backend.app.ai.context import (
    AIIntent,
    ContextItem,
    KBRContext,
)
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
            content="Grounded response.",
            model="test-model",
            provider="fake",
        )


class FakeRetriever:
    def __init__(self) -> None:
        self.received_intent = None
        self.received_query = None

    def retrieve(
        self,
        *,
        intent: AIIntent,
        query: str,
    ) -> KBRContext:
        self.received_intent = intent
        self.received_query = query

        assert query == "When is the next event?"
        assert intent == AIIntent.EVENTS

        return KBRContext(
            intent=AIIntent.EVENTS.value,
            items=[
                ContextItem(
                    type="event",
                    title="KBR Tournament",
                    content=(
                        "Description: A KBR esports tournament.\n"
                        "Location: Bizerte\n"
                        "Starts: September 10, 2026 at 18:00 UTC"
                    ),
                ),
            ],
        )


class FakeIntentDetector:
    def detect(
        self,
        message: str,
    ) -> AIIntent:
        assert message == "When is the next event?"

        return AIIntent.EVENTS


@pytest.mark.asyncio
async def test_ai_service_retrieves_context_before_generation():
    gateway = FakeGateway()
    retriever = FakeRetriever()
    intent_detector = FakeIntentDetector()

    service = AIService(
        gateway=gateway,
        context_retriever=retriever,
        intent_detector=intent_detector,
    )

    request = ModelRequest(
        messages=[
            ModelMessage(
                role="user",
                content="When is the next event?",
            ),
        ],
    )

    response = await service.generate(
        request,
    )

    assert response.content == "Grounded response."

    assert retriever.received_query == (
        "When is the next event?"
    )

    assert retriever.received_intent == AIIntent.EVENTS

    assert gateway.received_request is not None

    messages = gateway.received_request.messages

    assert len(messages) == 2

    context_message = messages[0]

    assert context_message.role == "system"
    assert "KBR Tournament" in context_message.content
    assert "September 10" in context_message.content
    assert "Bizerte" in context_message.content