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


class AIService:
    """
    Application-level service for AI model interactions.

    Responsibilities:

    1. Extract the user's latest message.
    2. Detect the user's intent.
    3. Retrieve relevant public KBR information.
    4. Build the KBR system prompt.
    5. Format the structured KBR context.
    6. Inject the application instructions and context into the
       model request.
    7. Delegate generation to ModelGateway.

    The service owns application-level AI behavior.

    Providers are responsible only for translating the provider-
    agnostic ModelRequest into the provider's API format.
    """

    def __init__(
        self,
        gateway: ModelGateway,
        context_retriever: ContextRetrieverProtocol | None = None,
        intent_detector: IntentDetector | None = None,
    ) -> None:
        self.gateway = gateway
        self.context_retriever = context_retriever
        self.intent_detector = (
            intent_detector
            if intent_detector is not None
            else IntentDetector()
        )

    async def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        """
        Generate a response through the configured model gateway.

        The KBR system prompt is always injected for application
        requests.

        When a context retriever is configured, relevant public
        KBR information is retrieved and appended to the system
        instructions before generation.
        """

        request = self._with_system_prompt(
            request,
        )

        if self.context_retriever is None:
            return await self.gateway.generate(
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

    @staticmethod
    def _get_latest_user_message(
        request: ModelRequest,
    ) -> str | None:
        """
        Return the latest non-empty user message.
        """

        for message in reversed(request.messages):
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
        Add retrieved KBR context to the existing system instructions.

        The context becomes a second system message so the provider
        can translate it naturally to the target model API.
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
]