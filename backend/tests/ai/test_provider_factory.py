import pytest

from backend.app.ai.providers import (
    GeminiProvider,
    GroqProvider,
    create_model_provider,
)
from backend.app.core.config import Settings


def create_settings(
    **overrides,
) -> Settings:
    values = {
        "postgres_password": "test-password",
        "jwt_secret_key": (
            "test-secret-key-that-is-long-enough"
        ),
        "ai_provider": "groq",
        "ai_api_key": "test-api-key",
    }

    values.update(overrides)

    return Settings(**values)


def test_factory_creates_groq_provider():
    settings = create_settings(
        ai_provider="groq",
    )

    provider = create_model_provider(
        settings,
    )

    assert isinstance(
        provider,
        GroqProvider,
    )


def test_factory_creates_gemini_provider():
    settings = create_settings(
        ai_provider="gemini",
    )

    provider = create_model_provider(
        settings,
    )

    assert isinstance(
        provider,
        GeminiProvider,
    )


def test_factory_normalizes_provider_name():
    settings = create_settings(
        ai_provider="GROQ",
    )

    provider = create_model_provider(
        settings,
    )

    assert isinstance(
        provider,
        GroqProvider,
    )


def test_factory_normalizes_gemini_provider_name():
    settings = create_settings(
        ai_provider="GEMINI",
    )

    provider = create_model_provider(
        settings,
    )

    assert isinstance(
        provider,
        GeminiProvider,
    )


def test_factory_rejects_unknown_provider():
    settings = create_settings(
        ai_provider="unknown",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported AI provider",
    ):
        create_model_provider(
            settings,
        )