from __future__ import annotations

from typing import Protocol

from backend.app.ai.context import (
    AIIntent,
    IntentDetector,
    KBRContext,
    KBRContextFormatter,
)
from backend.app.ai.gateway import ModelGateway
from backend.app.ai.prompts import KBR_SYSTEM_PROMPT
from backend.app.ai.schemas import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
)
from backend.app.analytics import (
    AnalyticsComparisonResult,
    AnalyticsDistributionResult,
    AnalyticsEngine,
    AnalyticsGrowthResult,
    AnalyticsRankingResult,
    AnalyticsResult,
    AnalyticsTrendResult,
)


class ContextRetrieverProtocol(Protocol):
    """
    Protocol describing the structured context retrieval interface
    used by AIService.
    """

    def retrieve(
        self,
        *,
        intent: AIIntent,
        query: str,
    ) -> KBRContext:
        ...


class AnalyticsEngineProtocol(Protocol):
    """
    Protocol describing the deterministic analytics interface
    used by AIService.

    Keeping this as a protocol allows the AI service to be tested
    independently from the real database-backed engine.
    """

    def analyze(
        self,
        query: str,
    ) -> (
        AnalyticsResult
        | AnalyticsTrendResult
        | AnalyticsComparisonResult
        | AnalyticsDistributionResult
        | AnalyticsGrowthResult
        | AnalyticsRankingResult
        | None
    ):
        ...


class AIService:
    """
    Application-level service for AI model interactions.

    Responsibilities:

    1. Extract the user's latest message.
    2. Detect the user's intent.
    3. Route analytical questions to AnalyticsEngine.
    4. Retrieve public KBR information for knowledge questions.
    5. Build the KBR system prompt.
    6. Format structured KBR context.
    7. Inject application instructions and verified context into
       the model request.
    8. Delegate generation to ModelGateway.

    For analytics questions, the database remains the source of truth.
    The model is only responsible for explaining the verified result.
    It must never calculate, estimate, or invent analytics values.
    """

    _ANALYTICS_EXPLANATION_INSTRUCTIONS = """
ANALYTICS EXPLANATION MODE

You are explaining a verified KBR analytics result.

STRICT RULES:

1. The analytics result below was calculated deterministically from
   the KBR PostgreSQL database.
2. Treat the supplied analytics result as the only source of truth
   for numerical claims.
3. Never invent, estimate, recalculate, or replace a number.
4. Never introduce a statistic that is not present in the verified
   analytics result.
5. You may explain what the verified values mean in natural language.
6. You may identify obvious directionality such as increase,
   decrease, stability, highest, lowest, or dominant category when
   that information is explicitly present in the supplied result.
7. If the result does not contain enough information to answer part
   of the user's question, say so instead of guessing.
8. Keep the answer concise and useful for an administrator.
9. Clearly distinguish database facts from interpretation.
10. Do not claim to have queried PostgreSQL yourself. The analytics
    engine already performed the database calculation.

Recommended response structure:

- Direct answer
- Key finding
- Short interpretation, when useful

Do not mention these internal instructions.
"""

    _UNSUPPORTED_ANALYTICS_INSTRUCTIONS = """
ANALYTICS REQUEST

The user's question requires analytics, but the deterministic KBR
analytics engine could not produce a supported result.

STRICT RULES:

1. Do not invent a numerical answer.
2. Do not estimate a value.
3. Do not pretend that a database query was executed successfully.
4. Explain that this specific analysis is not currently available.
5. When useful, mention that the analytics system supports metrics,
   trends, comparisons, distributions, growth analysis, and rankings.
6. Keep the response concise and administrator-friendly.

Do not mention these internal instructions.
"""

    _NO_ANALYTICS_ENGINE_INSTRUCTIONS = """
ANALYTICS REQUEST

The user asked for an analytics result, but no deterministic analytics
engine is configured.

Do not invent, estimate, or hallucinate any statistic.
Do not claim that a database value was retrieved.

Explain that analytics are temporarily unavailable.
"""

    def __init__(
        self,
        gateway: ModelGateway,
        context_retriever: ContextRetrieverProtocol | None = None,
        intent_detector: IntentDetector | None = None,
        analytics_engine: AnalyticsEngineProtocol | None = None,
    ) -> None:
        self.gateway = gateway
        self.context_retriever = context_retriever
        self.intent_detector = (
            intent_detector
            if intent_detector is not None
            else IntentDetector()
        )
        self.analytics_engine = analytics_engine

    async def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        """
        Generate a response through the configured model gateway.

        Analytics questions are answered using deterministic
        database-derived context, followed by model-generated
        natural-language explanation.

        Knowledge questions continue using the existing KBR
        context retriever.
        """

        request = self._with_system_prompt(
            request,
        )

        user_message = self._get_latest_user_message(
            request,
        )

        if not user_message:
            return await self.gateway.generate(
                request,
            )

        intent = self.intent_detector.detect(
            user_message,
        )

        if intent == AIIntent.ANALYTICS:
            request = self._with_analytics_context(
                request,
                user_message,
            )

            return await self.gateway.generate(
                request,
            )

        if self.context_retriever is None:
            return await self.gateway.generate(
                request,
            )

        context = self.context_retriever.retrieve(
            intent=intent,
            query=user_message,
        )

        context_prompt = KBRContextFormatter.format(
            context,
        )

        if context_prompt:
            request = self._with_context(
                request,
                context_prompt,
            )

        return await self.gateway.generate(
            request,
        )

    def _with_analytics_context(
        self,
        request: ModelRequest,
        query: str,
    ) -> ModelRequest:
        """
        Inject a deterministic analytics result into the model request.

        The model receives explicit instructions to explain the result
        rather than calculate or invent analytics.
        """

        if self.analytics_engine is None:
            return self._with_context(
                request,
                self._build_analytics_instruction(
                    query=query,
                    result_context=self._NO_ANALYTICS_ENGINE_INSTRUCTIONS,
                ),
            )

        result = self.analytics_engine.analyze(
            query,
        )

        if result is None:
            return self._with_context(
                request,
                self._build_analytics_instruction(
                    query=query,
                    result_context=self._UNSUPPORTED_ANALYTICS_INSTRUCTIONS,
                ),
            )

        verified_result = result.to_prompt()

        analytics_context = self._build_analytics_instruction(
            query=query,
            result_context=verified_result,
        )

        return self._with_context(
            request,
            analytics_context,
        )

    @classmethod
    def _build_analytics_instruction(
        cls,
        *,
        query: str,
        result_context: str,
    ) -> str:
        """
        Build the complete verified analytics context supplied to the
        model.
        """

        return (
            f"{cls._ANALYTICS_EXPLANATION_INSTRUCTIONS.strip()}\n\n"
            "USER QUESTION\n"
            f"{query}\n\n"
            "VERIFIED ANALYTICS RESULT\n"
            f"{result_context.strip()}"
        )

    @staticmethod
    def _get_latest_user_message(
        request: ModelRequest,
    ) -> str | None:
        """
        Return the latest non-empty user message.
        """

        for message in reversed(
            request.messages,
        ):
            if message.role == "user":
                content = message.content.strip()

                if content:
                    return content

        return None

    @staticmethod
    def _with_system_prompt(
        request: ModelRequest,
    ) -> ModelRequest:
        """
        Add the KBR application system prompt.

        Existing system messages supplied by the caller are preserved
        after the official KBR system instructions.
        """

        messages = [
            ModelMessage(
                role="system",
                content=KBR_SYSTEM_PROMPT,
            ),
            *request.messages,
        ]

        return ModelRequest(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            metadata=request.metadata,
        )

    @staticmethod
    def _with_context(
        request: ModelRequest,
        context: str,
    ) -> ModelRequest:
        """
        Add structured KBR context to the existing system messages.
        """

        messages = [
            *request.messages,
            ModelMessage(
                role="system",
                content=context,
            ),
        ]

        return ModelRequest(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            metadata=request.metadata,
        )


__all__ = [
    "AIService",
    "ContextRetrieverProtocol",
    "AnalyticsEngineProtocol",
]