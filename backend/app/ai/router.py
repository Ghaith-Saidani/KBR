from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from backend.app.ai.dependencies import get_ai_service
from backend.app.ai.schemas import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
)
from backend.app.ai.services import AIService
from backend.app.core.config import get_settings


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


class AIChatRequest(BaseModel):
    """
    Public HTTP request schema for the AI chat endpoint.

    The client can provide conversation messages and optional
    generation parameters.

    The model and provider are intentionally controlled by the
    backend configuration. This prevents clients from selecting
    arbitrary or unsupported models.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    messages: list[ModelMessage] = Field(
        min_length=1,
    )

    temperature: float | None = Field(
        default=None,
        ge=0,
        le=2,
    )

    max_tokens: int | None = Field(
        default=None,
        gt=0,
    )


@router.post(
    "/chat",
    response_model=ModelResponse,
)
async def chat(
    request: AIChatRequest,
    service: AIService = Depends(get_ai_service),
) -> ModelResponse:
    """
    Generate an AI response through the configured provider.

    Provider and model selection remain server-side.
    """

    settings = get_settings()

    model_request = ModelRequest(
        messages=request.messages,
        model=settings.ai_model,
        temperature=(
            request.temperature
            if request.temperature is not None
            else settings.ai_temperature
        ),
        max_tokens=(
            request.max_tokens
            if request.max_tokens is not None
            else settings.ai_max_tokens
        ),
    )

    return await service.generate(
        model_request,
    )


__all__ = [
    "router",
    "AIChatRequest",
]