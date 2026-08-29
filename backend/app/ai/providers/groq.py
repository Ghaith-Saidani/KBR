from typing import Any

import httpx

from backend.app.ai.providers.base import ModelProvider
from backend.app.ai.schemas.models import (
    ModelRequest,
    ModelResponse,
    ModelUsage,
)
from backend.app.core.config import Settings


class GroqProvider(ModelProvider):
    """
    Groq implementation of the provider-agnostic ModelProvider interface.

    The provider communicates with Groq's OpenAI-compatible
    Chat Completions API.
    """

    name = "groq"

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self.client = client

    @property
    def endpoint(self) -> str:
        return (
            f"{self.settings.ai_base_url}"
            "/chat/completions"
        )

    async def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        if not self.settings.ai_api_key:
            raise RuntimeError(
                "AI_API_KEY is not configured."
            )

        model = (
            request.model
            or self.settings.ai_model
        )

        temperature = request.temperature

        if request.temperature == 0.2:
            temperature = self.settings.ai_temperature

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                }
                for message in request.messages
            ],
            "temperature": temperature,
        }

        max_tokens = (
            request.max_tokens
            if request.max_tokens is not None
            else self.settings.ai_max_tokens
        )

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": (
                f"Bearer {self.settings.ai_api_key}"
            ),
            "Content-Type": "application/json",
        }

        if self.client is not None:
            response = await self.client.post(
                self.endpoint,
                json=payload,
                headers=headers,
            )
        else:
            async with httpx.AsyncClient(
                timeout=self.settings.ai_timeout_seconds,
            ) as client:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                )

        response.raise_for_status()

        data = response.json()

        return self._parse_response(
            data=data,
            fallback_model=model,
        )

    def _parse_response(
        self,
        data: dict[str, Any],
        fallback_model: str,
    ) -> ModelResponse:
        choices = data.get("choices") or []

        if not choices:
            raise RuntimeError(
                "AI provider returned no choices."
            )

        first_choice = choices[0]

        message = first_choice.get(
            "message"
        ) or {}

        content = message.get("content")

        if content is None:
            content = ""

        usage_data = data.get("usage")

        usage = None

        if usage_data:
            usage = ModelUsage(
                prompt_tokens=usage_data.get(
                    "prompt_tokens"
                ),
                completion_tokens=usage_data.get(
                    "completion_tokens"
                ),
                total_tokens=usage_data.get(
                    "total_tokens"
                ),
            )

        return ModelResponse(
            content=str(content),
            model=data.get(
                "model",
                fallback_model,
            ),
            provider=self.name,
            usage=usage,
            finish_reason=first_choice.get(
                "finish_reason"
            ),
            raw_response=data,
        )