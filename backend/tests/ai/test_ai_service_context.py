import pytest

from backend.app.ai.context import (
    AIIntent,
    KBRContext,
    ContextItem,
)
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

        return KBRContext(
            intent="events",
            items=[
                ContextItem(
                    type="event",
                    title="KBR Tournament",
                    content=(
                        "Description: A KBR esports tournament.\n"
                        "Location: Bizerte\n"
                        "Starts: September 10, 2026 at 18:00 UTC"
                    ),
                    relevance=10,
                ),
            ],
        )


class FakeIntentDetector:
    def detect(
        self,
        message: str,
    ) -> AIIntent:
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

    assert len(messages) == 3

    # Official KBR system instructions.
    assert messages[0].role == "system"
    assert messages[0].content == KBR_SYSTEM_PROMPT

    # Original user message.
    assert messages[1].role == "user"
    assert messages[1].content == (
        "When is the next event?"
    )

    # Retrieved database context.
    assert messages[2].role == "system"

    assert (
        "RETRIEVED KBR DATABASE CONTEXT"
        in messages[2].content
    )

    assert (
        "KBR Tournament"
        in messages[2].content
    )

    assert (
        "September 10, 2026"
        in messages[2].content
    )


@pytest.mark.asyncio
async def test_ai_service_context_is_added_after_system_prompt():
    gateway = FakeGateway()
    retriever = FakeRetriever()

    service = AIService(
        gateway=gateway,
        context_retriever=retriever,
        intent_detector=FakeIntentDetector(),
    )

    request = ModelRequest(
        messages=[
            ModelMessage(
                role="user",
                content="Tell me about the tournament.",
            ),
        ],
    )

    await service.generate(request)

    received = gateway.received_request

    assert received is not None

    assert received.messages[0].role == "system"
    assert received.messages[0].content == KBR_SYSTEM_PROMPT

    assert received.messages[1].role == "user"

    assert received.messages[2].role == "system"
    assert (
        "KBR Tournament"
        in received.messages[2].content
    )