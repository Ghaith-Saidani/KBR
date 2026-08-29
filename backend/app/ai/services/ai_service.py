from __future__ import annotations

from typing import Protocol

from backend.app.ai.context import (
    AIIntent,
    IntentDetector,
    KBRContextFormatter,
    KBRContextRetriever,
)
from backend.app.ai.gateway import ModelGateway
from backend.app.ai.schemas import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
)


class ContextRetrieverProtocol(Protocol):
    """
    Protocol describing the context retrieval interface used by AIService.
    """

    def retrieve(
        self,
        *,
        intent: AIIntent,
        query: str,
    ) -> dict[str, object]:
        ...


class AIService:
    """
    Application-level service for AI model interactions.

    Responsibilities:

    1. Extract the user's latest message.
    2. Detect the user's intent.
    3. Retrieve relevant KBR information.
    4. Format the retrieved information.
    5. Inject the context into the model request.
    6. Delegate generation to ModelGateway.

    Architecture:

        Router
           ↓
        AIService
           ↓
        IntentDetector
           ↓
        KBRContextRetriever
           ↓
        KBRContextFormatter
           ↓
        ModelGateway
           ↓
        ModelProvider
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
        Generate an AI response.

        When a context retriever is configured, the service retrieves
        relevant public KBR information before sending the request
        to the model.
        """

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
        Return the latest user message from the conversation.
        """

        for message in reversed(request.messages):
            if message.role == "user":
                content = message.content.strip()

                if content:
                    return content

        return None

    @staticmethod
    def _with_context(
        request: ModelRequest,
        context: str,
    ) -> ModelRequest:
        """
        Create a new model request with retrieved KBR context.

        The context is inserted as a system message before the
        conversation so the model receives the database information
        before processing the user's request.
        """

        messages = [
            ModelMessage(
                role="system",
                content=context,
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


__all__ = [
    "AIService",
    "ContextRetrieverProtocol",
]