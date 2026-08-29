from backend.app.core.config import Settings


def test_ai_max_tokens_empty_value_becomes_none():
    settings = Settings(
        postgres_password="test-password",
        jwt_secret_key=(
            "test-secret-key-that-is-long-enough"
        ),
        ai_max_tokens="",
    )

    assert settings.ai_max_tokens is None


def test_ai_configuration_defaults():
    settings = Settings(
        postgres_password="test-password",
        jwt_secret_key=(
            "test-secret-key-that-is-long-enough"
        ),
    )

    assert settings.ai_provider == "gemini"

    assert (
        settings.gemini_model
        == "gemini-3.6-flash"
    )

    assert settings.gemini_base_url == (
        "https://generativelanguage.googleapis.com/v1beta"
    )

    assert settings.ai_timeout_seconds == 30.0

    assert settings.ai_temperature == 0.2

    assert settings.ai_max_tokens is None


def test_ai_api_key_empty_value_becomes_none():
    settings = Settings(
        postgres_password="test-password",
        jwt_secret_key=(
            "test-secret-key-that-is-long-enough"
        ),
        gemini_api_key="",
    )

    assert settings.gemini_api_key is None