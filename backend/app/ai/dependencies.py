from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.ai.context import KBRContextRetriever
from backend.app.ai.gateway import ModelGateway
from backend.app.ai.providers import create_model_provider
from backend.app.ai.services.ai_service import AIService
from backend.app.core.config import Settings, get_settings
from backend.app.core.database import get_db


@lru_cache
def get_ai_gateway() -> ModelGateway:
    """
    Create and cache the application's AI model gateway.

    The gateway is built from the configured AI provider.
    This keeps FastAPI routes independent from concrete providers.
    """

    settings = get_settings()

    provider = create_model_provider(
        settings,
    )

    return ModelGateway(
        provider,
    )


def get_ai_service(
    db: Session = Depends(get_db),
) -> AIService:
    """
    FastAPI dependency for the application-level AI service.

    The service receives a database-backed context retriever so
    AI responses can be grounded in public KBR information.
    """

    context_retriever = KBRContextRetriever(
        db,
    )

    return AIService(
        gateway=get_ai_gateway(),
        context_retriever=context_retriever,
    )


__all__ = [
    "get_ai_gateway",
    "get_ai_service",
]