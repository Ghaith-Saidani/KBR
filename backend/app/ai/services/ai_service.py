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
    AnalyticsEngine,
    AnalyticsResult,
    AnalyticsTrendResult,
    AnalyticsComparisonResult,
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

    Providers remain responsible only for translating the
    provider-agnostic ModelRequest into the provider API format.
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
        database-derived context.

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
        Add deterministic analytics context to the model request.

        When no supported analytical metric can be resolved, the
        model receives an explicit instruction not to invent a
        statistical answer.
        """

        if self.analytics_engine is None:
            analytics_prompt = (
                "ANALYTICS REQUEST\n"
                f"User question: {query}\n\n"
                "No analytics engine is currently configured. "
                "Do not invent statistics or claim that a database "
                "value was retrieved."
            )

            return self._with_context(
                request,
                analytics_prompt,
            )

        result = self.analytics_engine.analyze(
            query,
        )

        if result is None:
            analytics_prompt = (
                "ANALYTICS REQUEST\n"
                f"User question: {query}\n\n"
                "This analytical question is not currently "
                "supported by the deterministic analytics engine.\n"
                "Do not invent, estimate, or hallucinate a numerical "
                "answer.\n"
                "Explain that this specific statistic is not "
                "currently available and, when useful, mention "
                "the types of KBR statistics that are available."
            )

            return self._with_context(
                request,
                analytics_prompt,
            )

        return self._with_context(
            request,
            result.to_prompt(),
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