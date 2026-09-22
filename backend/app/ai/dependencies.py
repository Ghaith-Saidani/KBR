from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.ai.context import KBRContextRetriever
from backend.app.ai.gateway import ModelGateway
from backend.app.ai.providers import create_model_provider
from backend.app.ai.services.ai_service import AIService
from backend.app.analytics import AnalyticsEngine
from backend.app.core.config import get_settings
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

    The service receives both:

    - a database-backed public context retriever;
    - a deterministic analytics engine.

    This allows the AI service to route knowledge questions
    through the existing RAG/context system and analytical
    questions through verified database statistics.
    """

    context_retriever = KBRContextRetriever(
        db,
    )

    analytics_engine = AnalyticsEngine(
        db,
    )

    return AIService(
        gateway=get_ai_gateway(),
        context_retriever=context_retriever,
        analytics_engine=analytics_engine,
    )


__all__ = [
    "get_ai_gateway",
    "get_ai_service",
]