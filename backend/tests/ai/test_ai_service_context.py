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
from backend.app.analytics import (
    AnalyticsComparisonResult,
    AnalyticsResult,
    AnalyticsTrendResult,
)


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
    def __init__(
        self,
        intent: AIIntent = AIIntent.EVENTS,
    ) -> None:
        self.intent = intent
        self.received_message = None

    def detect(
        self,
        message: str,
    ) -> AIIntent:
        self.received_message = message
        return self.intent


class FakeAnalyticsEngine:
    def __init__(
        self,
        result: (
            AnalyticsResult
            | AnalyticsTrendResult
            | AnalyticsComparisonResult
            | None
        ),
    ) -> None:
        self.result = result
        self.received_query = None

    def analyze(
        self,
        query: str,
    ) -> (
        AnalyticsResult
        | AnalyticsTrendResult
        | AnalyticsComparisonResult
        | None
    ):
        self.received_query = query
        return self.result


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

    assert messages[0].role == "system"
    assert messages[0].content == KBR_SYSTEM_PROMPT

    assert messages[1].role == "user"
    assert messages[1].content == (
        "When is the next event?"
    )

    assert messages[2].role == "system"

    assert (
        "RETRIEVED KBR DATABASE CONTEXT"
        in messages[2].content
    )

    assert "KBR Tournament" in messages[2].content
    assert "September 10, 2026" in messages[2].content


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
    assert "KBR Tournament" in received.messages[2].content


@pytest.mark.asyncio
async def test_ai_service_routes_total_count_analytics():
    gateway = FakeGateway()

    analytics_engine = FakeAnalyticsEngine(
        AnalyticsResult(
            metric="total_events",
            value=12,
            label="Total number of KBR events.",
        ),
    )

    service = AIService(
        gateway=gateway,
        context_retriever=None,
        intent_detector=FakeIntentDetector(
            intent=AIIntent.ANALYTICS,
        ),
        analytics_engine=analytics_engine,
    )

    request = ModelRequest(
        messages=[
            ModelMessage(
                role="user",
                content="How many events does KBR have?",
            ),
        ],
    )

    await service.generate(request)

    assert analytics_engine.received_query == (
        "How many events does KBR have?"
    )

    received = gateway.received_request

    assert received is not None
    assert len(received.messages) == 3

    analytics_context = received.messages[2].content

    assert "ANALYTICS RESULT" in analytics_context
    assert "Metric: total_events" in analytics_context
    assert "Value: 12" in analytics_context
    assert "KBR PostgreSQL database" in analytics_context


@pytest.mark.asyncio
async def test_ai_service_routes_period_analytics():
    gateway = FakeGateway()

    analytics_engine = FakeAnalyticsEngine(
        AnalyticsResult(
            metric="events_created_in_period",
            value=7,
            label=(
                "Number of events created during "
                "the requested period."
            ),
            start_date=__import__(
                "datetime",
            ).date(
                2026,
                8,
                1,
            ),
            end_date=__import__(
                "datetime",
            ).date(
                2026,
                8,
                31,
            ),
        ),
    )

    service = AIService(
        gateway=gateway,
        context_retriever=None,
        intent_detector=FakeIntentDetector(
            intent=AIIntent.ANALYTICS,
        ),
        analytics_engine=analytics_engine,
    )

    request = ModelRequest(
        messages=[
            ModelMessage(
                role="user",
                content=(
                    "How many events were created "
                    "in August 2026?"
                ),
            ),
        ],
    )

    await service.generate(request)

    assert analytics_engine.received_query == (
        "How many events were created in August 2026?"
    )

    received = gateway.received_request

    assert received is not None

    analytics_context = received.messages[2].content

    assert "ANALYTICS RESULT" in analytics_context
    assert (
        "Metric: events_created_in_period"
        in analytics_context
    )
    assert "Value: 7" in analytics_context
    assert "Start date: 2026-08-01" in analytics_context
    assert "End date: 2026-08-31" in analytics_context


@pytest.mark.asyncio
async def test_ai_service_routes_trend_analytics():
    gateway = FakeGateway()

    analytics_engine = FakeAnalyticsEngine(
        AnalyticsTrendResult(
            metric="members_created_per_month",
            months=[
                ("2026-04", 2),
                ("2026-05", 4),
                ("2026-06", 7),
                ("2026-07", 5),
                ("2026-08", 9),
                ("2026-09", 11),
            ],
            label=(
                "Number of members created in each "
                "of the last six calendar months."
            ),
        ),
    )

    service = AIService(
        gateway=gateway,
        context_retriever=None,
        intent_detector=FakeIntentDetector(
            intent=AIIntent.ANALYTICS,
        ),
        analytics_engine=analytics_engine,
    )

    request = ModelRequest(
        messages=[
            ModelMessage(
                role="user",
                content="How has membership grown?",
            ),
        ],
    )

    await service.generate(request)

    assert analytics_engine.received_query == (
        "How has membership grown?"
    )

    received = gateway.received_request

    assert received is not None

    analytics_context = received.messages[2].content

    assert "ANALYTICS TREND RESULT" in analytics_context
    assert (
        "Metric: members_created_per_month"
        in analytics_context
    )
    assert "2026-04: 2" in analytics_context
    assert "2026-09: 11" in analytics_context


@pytest.mark.asyncio
async def test_ai_service_routes_comparison_analytics():
    gateway = FakeGateway()

    analytics_engine = FakeAnalyticsEngine(
        AnalyticsComparisonResult(
            metric="events_created_comparison",
            first_period_label="June 2026",
            first_value=4,
            second_period_label="September 2026",
            second_value=10,
            difference=6,
            percentage_change=150.0,
            label=(
                "Comparison of events created "
                "between the requested months."
            ),
        ),
    )

    service = AIService(
        gateway=gateway,
        context_retriever=None,
        intent_detector=FakeIntentDetector(
            intent=AIIntent.ANALYTICS,
        ),
        analytics_engine=analytics_engine,
    )

    request = ModelRequest(
        messages=[
            ModelMessage(
                role="user",
                content=(
                    "Compare events between "
                    "June and September."
                ),
            ),
        ],
    )

    await service.generate(request)

    assert analytics_engine.received_query == (
        "Compare events between June and September."
    )

    received = gateway.received_request

    assert received is not None

    analytics_context = received.messages[2].content

    assert (
        "ANALYTICS COMPARISON RESULT"
        in analytics_context
    )
    assert "June 2026: 4" in analytics_context
    assert "September 2026: 10" in analytics_context
    assert "Difference: 6" in analytics_context
    assert "Percentage change: 150.00%" in analytics_context


@pytest.mark.asyncio
async def test_ai_service_does_not_hallucinate_unsupported_analytics():
    gateway = FakeGateway()

    analytics_engine = FakeAnalyticsEngine(
        None,
    )

    service = AIService(
        gateway=gateway,
        context_retriever=None,
        intent_detector=FakeIntentDetector(
            intent=AIIntent.ANALYTICS,
        ),
        analytics_engine=analytics_engine,
    )

    request = ModelRequest(
        messages=[
            ModelMessage(
                role="user",
                content=(
                    "What is the average age "
                    "of KBR members?"
                ),
            ),
        ],
    )

    await service.generate(request)

    assert analytics_engine.received_query == (
        "What is the average age of KBR members?"
    )

    received = gateway.received_request

    assert received is not None

    analytics_context = received.messages[2].content

    assert "ANALYTICS REQUEST" in analytics_context
    assert "not currently supported" in analytics_context
    assert "Do not invent" in analytics_context


@pytest.mark.asyncio
async def test_ai_service_analytics_does_not_require_context_retriever():
    gateway = FakeGateway()

    analytics_engine = FakeAnalyticsEngine(
        AnalyticsResult(
            metric="total_events",
            value=12,
            label="Total number of KBR events.",
        ),
    )

    service = AIService(
        gateway=gateway,
        context_retriever=None,
        intent_detector=FakeIntentDetector(
            intent=AIIntent.ANALYTICS,
        ),
        analytics_engine=analytics_engine,
    )

    request = ModelRequest(
        messages=[
            ModelMessage(
                role="user",
                content="How many events does KBR have?",
            ),
        ],
    )

    await service.generate(request)

    received = gateway.received_request

    assert received is not None
    assert len(received.messages) == 3

    assert (
        "Metric: total_events"
        in received.messages[2].content
    )

    assert "Value: 12" in received.messages[2].content