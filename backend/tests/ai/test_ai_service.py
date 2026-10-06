from __future__ import annotations

from dataclasses import dataclass

import pytest

from backend.app.ai.context import AIIntent
from backend.app.ai.schemas import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
)
from backend.app.ai.services.ai_service import AIService
from backend.app.analytics import (
    AnalyticsComparisonResult,
    AnalyticsDistributionResult,
    AnalyticsGrowthResult,
    AnalyticsRankingResult,
    AnalyticsResult,
    AnalyticsTrendResult,
)


@dataclass
class FakeGateway:
    received_request: ModelRequest | None = None

    async def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        self.received_request = request

        return ModelResponse(
            content="Fake response",
            model="fake-model",
            provider="fake-provider",
        )


@dataclass
class FakeContextRetriever:
    received_intent: AIIntent | None = None
    received_query: str | None = None

    def retrieve(
        self,
        *,
        intent: AIIntent,
        query: str,
    ):
        self.received_intent = intent
        self.received_query = query

        return None


@dataclass
class FakeIntentDetector:
    intent: AIIntent

    def detect(
        self,
        message: str,
    ) -> AIIntent:
        return self.intent


@dataclass
class FakeAnalyticsEngine:
    result: object | None
    received_query: str | None = None

    def analyze(
        self,
        query: str,
    ):
        self.received_query = query

        return self.result


def build_request(
    *messages: ModelMessage,
) -> ModelRequest:
    return ModelRequest(
        messages=list(messages),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "result",
    [
        AnalyticsResult(
            metric="total_events",
            value=26,
            label="Nombre total d'événements.",
        ),
        AnalyticsTrendResult(
            metric="events_created_per_month",
            months=[
                ("2026-07", 2),
                ("2026-08", 7),
                ("2026-09", 3),
            ],
            label="Évolution mensuelle des événements.",
        ),
        AnalyticsComparisonResult(
            metric="events_created_comparison",
            first_period_label="juin 2026",
            first_value=2,
            second_period_label="septembre 2026",
            second_value=3,
            difference=1,
            percentage_change=50.0,
            label="Comparaison des événements créés.",
        ),
        AnalyticsDistributionResult(
            metric="members_by_status",
            categories=[
                ("active", 10),
                ("pending", 3),
                ("inactive", 2),
            ],
            label="Répartition des membres par statut.",
        ),
        AnalyticsGrowthResult(
            metric="members_month_over_month_growth",
            current_period_label="septembre 2026",
            current_value=5,
            previous_period_label="août 2026",
            previous_value=10,
            difference=-5,
            percentage_change=-50.0,
            label="Évolution mensuelle des membres.",
        ),
        AnalyticsRankingResult(
            metric="events_created_monthly_ranking",
            period_label="2026",
            rank=1,
            value=7,
            direction="desc",
            label="Classement mensuel des événements.",
        ),
    ],
)
async def test_ai_service_injects_all_analytics_result_types(
    result,
):
    gateway = FakeGateway()

    analytics_engine = FakeAnalyticsEngine(
        result=result,
    )

    service = AIService(
        gateway=gateway,
        analytics_engine=analytics_engine,
    )

    query = "Give me the requested KBR analytics."

    request = build_request(
        ModelMessage(
            role="user",
            content=query,
        ),
    )

    await service.generate(
        request,
    )

    assert analytics_engine.received_query == query

    received = gateway.received_request

    assert received is not None

    analytics_message = received.messages[-1]

    assert analytics_message.role == "system"

    assert "ANALYTICS EXPLANATION MODE" in analytics_message.content
    assert "USER QUESTION" in analytics_message.content
    assert query in analytics_message.content
    assert "VERIFIED ANALYTICS RESULT" in analytics_message.content

    verified_result = result.to_prompt()

    assert verified_result in analytics_message.content


@pytest.mark.asyncio
async def test_ai_service_reports_unsupported_analytics_without_inventing():
    gateway = FakeGateway()

    analytics_engine = FakeAnalyticsEngine(
        result=None,
    )

    service = AIService(
        gateway=gateway,
        analytics_engine=analytics_engine,
    )

    query = "What is the average age of KBR members?"

    request = build_request(
        ModelMessage(
            role="user",
            content=query,
        ),
    )

    await service.generate(
        request,
    )

    received = gateway.received_request

    assert received is not None

    analytics_message = received.messages[-1]

    assert analytics_message.role == "system"
    assert "ANALYTICS EXPLANATION MODE" in analytics_message.content
    assert "VERIFIED ANALYTICS RESULT" in analytics_message.content
    assert query in analytics_message.content
    assert "ANALYTICS EXPLANATION MODE" in analytics_message.content
    assert "Do not invent" in analytics_message.content


@pytest.mark.asyncio
async def test_ai_service_reports_missing_analytics_engine():
    gateway = FakeGateway()

    service = AIService(
        gateway=gateway,
    )

    query = "How many events does KBR have?"

    request = build_request(
        ModelMessage(
            role="user",
            content=query,
        ),
    )

    await service.generate(
        request,
    )

    received = gateway.received_request

    assert received is not None

    analytics_message = received.messages[-1]

    assert analytics_message.role == "system"
    assert "ANALYTICS EXPLANATION MODE" in analytics_message.content
    assert "analytics are temporarily unavailable" in (
        analytics_message.content.lower()
    )
    assert "Do not invent" in analytics_message.content


@pytest.mark.asyncio
async def test_ai_service_passes_analytics_query_to_engine():
    gateway = FakeGateway()

    result = AnalyticsGrowthResult(
        metric="members_month_over_month_growth",
        current_period_label="septembre 2026",
        current_value=5,
        previous_period_label="août 2026",
        previous_value=10,
        difference=-5,
        percentage_change=-50.0,
        label="Évolution mensuelle des membres.",
    )

    analytics_engine = FakeAnalyticsEngine(
        result=result,
    )

    service = AIService(
        gateway=gateway,
        analytics_engine=analytics_engine,
    )

    query = "How did membership change last month?"

    request = build_request(
        ModelMessage(
            role="user",
            content=query,
        ),
    )

    await service.generate(
        request,
    )

    assert analytics_engine.received_query == query


@pytest.mark.asyncio
async def test_ai_service_uses_latest_user_message_for_analytics():
    gateway = FakeGateway()

    result = AnalyticsDistributionResult(
        metric="members_by_status",
        categories=[
            ("active", 10),
            ("pending", 3),
        ],
        label="Répartition des membres par statut.",
    )

    analytics_engine = FakeAnalyticsEngine(
        result=result,
    )

    service = AIService(
        gateway=gateway,
        analytics_engine=analytics_engine,
    )

    request = build_request(
        ModelMessage(
            role="user",
            content="How many events?",
        ),
        ModelMessage(
            role="assistant",
            content="There are several events.",
        ),
        ModelMessage(
            role="user",
            content="Show member status distribution.",
        ),
    )

    await service.generate(
        request,
    )

    assert (
        analytics_engine.received_query
        == "Show member status distribution."
    )


@pytest.mark.asyncio
async def test_ai_service_does_not_use_analytics_for_knowledge_questions():
    gateway = FakeGateway()

    analytics_engine = FakeAnalyticsEngine(
        result=AnalyticsResult(
            metric="total_events",
            value=26,
            label="Nombre total d'événements.",
        ),
    )

    context_retriever = FakeContextRetriever()

    intent_detector = FakeIntentDetector(
        intent=AIIntent.GENERAL,
    )

    service = AIService(
        gateway=gateway,
        context_retriever=context_retriever,
        intent_detector=intent_detector,
        analytics_engine=analytics_engine,
    )

    query = "Tell me about KBR."

    request = build_request(
        ModelMessage(
            role="user",
            content=query,
        ),
    )

    await service.generate(
        request,
    )

    assert analytics_engine.received_query is None
    assert context_retriever.received_query == query
    assert context_retriever.received_intent == AIIntent.GENERAL


@pytest.mark.asyncio
async def test_ai_service_preserves_latest_user_message():
    gateway = FakeGateway()

    analytics_engine = FakeAnalyticsEngine(
        result=AnalyticsResult(
            metric="total_events",
            value=26,
            label="Nombre total d'événements.",
        ),
    )

    service = AIService(
        gateway=gateway,
        analytics_engine=analytics_engine,
    )

    query = "How many events does KBR have?"

    request = build_request(
        ModelMessage(
            role="user",
            content=query,
        ),
    )

    await service.generate(
        request,
    )

    received = gateway.received_request

    assert received is not None

    user_messages = [
        message
        for message in received.messages
        if message.role == "user"
    ]

    assert user_messages
    assert user_messages[-1].content == query


@pytest.mark.asyncio
async def test_ai_service_analytics_context_contains_anti_hallucination_rules():
    gateway = FakeGateway()

    result = AnalyticsResult(
        metric="total_events",
        value=26,
        label="Nombre total d'événements.",
    )

    analytics_engine = FakeAnalyticsEngine(
        result=result,
    )

    service = AIService(
        gateway=gateway,
        analytics_engine=analytics_engine,
    )

    request = build_request(
        ModelMessage(
            role="user",
            content="How many events does KBR have?",
        ),
    )

    await service.generate(
        request,
    )

    received = gateway.received_request

    assert received is not None

    analytics_message = received.messages[-1]

    assert "Never invent, estimate, recalculate" in (
        analytics_message.content
    )
    assert "only source of truth" in analytics_message.content
    assert "KBR database" in analytics_message.content
    assert "Direct answer" in analytics_message.content
    assert "Key finding" in analytics_message.content