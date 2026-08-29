from typing import Any

import httpx

from backend.app.ai.providers.base import ModelProvider
from backend.app.ai.schemas.models import (
    ModelRequest,
    ModelResponse,
    ModelUsage,
)
from backend.app.core.config import Settings


class GeminiProvider(ModelProvider):
    """
    Google Gemini implementation of the provider-agnostic
    ModelProvider interface.

    Uses Google's REST GenerateContent API directly through httpx.

    The provider is responsible only for translating the
    provider-agnostic ModelRequest into Gemini's API format
    and translating Gemini responses/errors back into the
    application's provider-agnostic representation.

    Application-level system prompts should be supplied through
    ModelRequest.messages using the "system" role.
    """

    name = "gemini"

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self.client = client

    @property
    def endpoint(self) -> str:
        model = (
            self.settings.ai_model
            or self.settings.gemini_model
        )

        return (
            f"{self.settings.gemini_base_url}"
            f"/models/{model}:generateContent"
        )

    def _get_api_key(self) -> str | None:
        """
        Resolve the Gemini API key.

        Generic AI configuration takes priority, with the
        Gemini-specific key used as a fallback.
        """

        return (
            self.settings.ai_api_key
            or self.settings.gemini_api_key
        )

    @staticmethod
    def _normalize_role(role: str) -> str:
        """
        Convert provider-agnostic roles to Gemini roles.

        Gemini uses:
            user
            model

        System messages are handled separately.
        """

        normalized = role.strip().lower()

        if normalized in {"assistant", "model"}:
            return "model"

        return "user"

    @staticmethod
    def _is_gemini_3_model(model: str) -> bool:
        """
        Detect Gemini 3.x models.

        Gemini 3 models use thinkingLevel rather than the older
        thinkingBudget configuration.
        """

        normalized = model.strip().lower()

        return normalized.startswith("gemini-3")

    @staticmethod
    def _extract_error_message(
        response: httpx.Response,
    ) -> str:
        """
        Extract a useful error message from a Gemini error response.

        Gemini normally returns an error payload similar to:

            {
                "error": {
                    "code": 429,
                    "message": "...",
                    "status": "RESOURCE_EXHAUSTED"
                }
            }

        If the response is not valid JSON, fall back to the
        HTTP status text.
        """

        try:
            data = response.json()
        except ValueError:
            return response.text.strip() or response.reason_phrase

        if not isinstance(data, dict):
            return response.reason_phrase

        error = data.get("error")

        if not isinstance(error, dict):
            return response.reason_phrase

        message = error.get("message")

        if isinstance(message, str) and message.strip():
            return message.strip()

        return response.reason_phrase

    @classmethod
    def _raise_for_gemini_error(
        cls,
        response: httpx.Response,
    ) -> None:
        """
        Translate Gemini HTTP errors into clear application errors.

        The original Gemini response is intentionally not exposed
        directly to the application.
        """

        if response.is_success:
            return

        status_code = response.status_code
        provider_message = cls._extract_error_message(
            response
        )

        if status_code == 429:
            raise RuntimeError(
                "Gemini rate limit or quota exceeded. "
                "Please try again later."
            )

        if status_code in {401, 403}:
            raise RuntimeError(
                "Gemini authentication or authorization failed. "
                "Please verify the configured API key and project."
            )

        if status_code == 400:
            raise RuntimeError(
                "Gemini rejected the request. "
                f"Provider message: {provider_message}"
            )

        if status_code == 404:
            raise RuntimeError(
                "The configured Gemini model or endpoint was not found. "
                f"Provider message: {provider_message}"
            )

        if status_code == 408:
            raise RuntimeError(
                "Gemini request timed out. "
                "Please try again."
            )

        if 500 <= status_code <= 599:
            raise RuntimeError(
                "Gemini is temporarily unavailable. "
                "Please try again later."
            )

        raise RuntimeError(
            "Gemini request failed. "
            f"HTTP {status_code}: {provider_message}"
        )

    def _build_payload(
        self,
        request: ModelRequest,
        model: str,
    ) -> dict[str, Any]:
        """
        Translate a provider-agnostic ModelRequest into
        Gemini GenerateContent API format.

        System messages are converted into Gemini's
        systemInstruction field.

        No application-level prompt is injected here.
        """

        contents: list[dict[str, Any]] = []
        system_parts: list[dict[str, str]] = []

        for message in request.messages:
            role = message.role.strip().lower()

            if role == "system":
                system_parts.append(
                    {
                        "text": message.content,
                    }
                )
                continue

            contents.append(
                {
                    "role": self._normalize_role(role),
                    "parts": [
                        {
                            "text": message.content,
                        }
                    ],
                }
            )

        generation_config: dict[str, Any] = {}

        max_tokens = (
            request.max_tokens
            if request.max_tokens is not None
            else self.settings.ai_max_tokens
        )

        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens

        # Gemini 3.x uses thinkingLevel.
        #
        # Low is appropriate for the KBR website assistant because
        # most requests are simple informational/chat requests.
        if self._is_gemini_3_model(model):
            generation_config["thinkingConfig"] = {
                "thinkingLevel": "low",
            }
        else:
            # Older Gemini models continue to use temperature.
            generation_config["temperature"] = request.temperature

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        if system_parts:
            payload["systemInstruction"] = {
                "parts": system_parts,
            }

        return payload

    async def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        """
        Generate a response using Gemini.

        Provider errors are translated into clear RuntimeError
        messages instead of leaking raw httpx exceptions.
        """

        api_key = self._get_api_key()

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        model = (
            request.model
            or self.settings.gemini_model
            or self.settings.ai_model
        )

        endpoint = (
            f"{self.settings.gemini_base_url}"
            f"/models/{model}:generateContent"
        )

        payload = self._build_payload(
            request=request,
            model=model,
        )

        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }

        if self.client is not None:
            response = await self.client.post(
                endpoint,
                json=payload,
                headers=headers,
            )
        else:
            async with httpx.AsyncClient(
                timeout=self.settings.ai_timeout_seconds,
            ) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                )

        self._raise_for_gemini_error(response)

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
        """
        Convert Gemini's response into our provider-agnostic
        ModelResponse format.
        """

        candidates = data.get("candidates") or []

        if not candidates:
            raise RuntimeError(
                "Gemini provider returned no candidates."
            )

        first_candidate = candidates[0]

        content_data = (
            first_candidate.get("content")
            or {}
        )

        parts = content_data.get("parts") or []

        text_parts: list[str] = []

        for part in parts:
            # Gemini can return internal thought parts.
            # Only expose normal user-facing text.
            if part.get("thought") is True:
                continue

            text = part.get("text")

            if text is not None:
                text_parts.append(str(text))

        content = "".join(text_parts).strip()

        if not content:
            raise RuntimeError(
                "Gemini provider returned no text content."
            )

        usage_metadata = data.get("usageMetadata")

        usage = None

        if usage_metadata:
            usage = ModelUsage(
                prompt_tokens=usage_metadata.get(
                    "promptTokenCount"
                ),
                completion_tokens=usage_metadata.get(
                    "candidatesTokenCount"
                ),
                total_tokens=usage_metadata.get(
                    "totalTokenCount"
                ),
            )

        finish_reason = first_candidate.get(
            "finishReason"
        )

        return ModelResponse(
            content=content,
            model=data.get(
                "modelVersion",
                fallback_model,
            ),
            provider=self.name,
            usage=usage,
            finish_reason=finish_reason,
            # Do not expose the complete Gemini response.
            #
            # Gemini responses can contain thought signatures
            # and other internal metadata.
            raw_response=None,
        )