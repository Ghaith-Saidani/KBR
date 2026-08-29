from backend.app.ai.providers.base import ModelProvider
from backend.app.ai.providers.gemini import GeminiProvider
from backend.app.ai.providers.groq import GroqProvider
from backend.app.core.config import Settings


def create_model_provider(
    settings: Settings,
) -> ModelProvider:
    provider_name = (
        settings.ai_provider.strip().lower()
    )

    if provider_name == "groq":
        return GroqProvider(
            settings=settings,
        )

    if provider_name == "gemini":
        return GeminiProvider(
            settings=settings,
        )

    raise ValueError(
        f"Unsupported AI provider: {provider_name}"
    )