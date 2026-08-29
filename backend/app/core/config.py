from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KBR API"
    app_version: str = "0.1.0"
    app_env: str = "development"

    postgres_db: str = "kbr"
    postgres_test_db: str = "kbr_test"
    postgres_user: str = "kbr_user"
    postgres_password: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # ------------------------------------------------------------------
    # AI configuration
    # ------------------------------------------------------------------

    # Gemini is the active provider.
    ai_provider: str = "gemini"

    # Generic AI API key.
    #
    # GeminiProvider also supports gemini_api_key below. Keeping both
    # allows the provider abstraction to remain compatible with the
    # previous Groq-based configuration.
    ai_api_key: str | None = None

    # Generic AI model.
    #
    # This is intentionally aligned with the active Gemini provider.
    ai_model: str = "gemini-3.6-flash"

    # Generic AI base URL.
    #
    # Aligned with Google's Gemini REST API.
    ai_base_url: str = (
        "https://generativelanguage.googleapis.com/v1beta"
    )

    ai_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=300,
    )

    ai_temperature: float = Field(
        default=0.2,
        ge=0,
        le=2,
    )

    ai_max_tokens: int | None = Field(
        default=None,
        gt=0,
    )

    # ------------------------------------------------------------------
    # Gemini-specific configuration
    # ------------------------------------------------------------------

    gemini_api_key: str | None = None

    # Gemini 3.6 Flash has been verified against the configured API key.
    gemini_model: str = "gemini-3.6-flash"

    gemini_base_url: str = (
        "https://generativelanguage.googleapis.com/v1beta"
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator(
        "cors_origins",
        mode="before",
    )
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]

        return value

    @field_validator(
        "ai_provider",
        mode="before",
    )
    @classmethod
    def normalize_ai_provider(cls, value):
        if value is None:
            return "gemini"

        return str(value).strip().lower()

    @field_validator(
        "ai_base_url",
        mode="before",
    )
    @classmethod
    def normalize_ai_base_url(cls, value):
        if value is None:
            return (
                "https://generativelanguage.googleapis.com/v1beta"
            )

        return str(value).rstrip("/")

    @field_validator(
        "gemini_base_url",
        mode="before",
    )
    @classmethod
    def normalize_gemini_base_url(cls, value):
        if value is None:
            return (
                "https://generativelanguage.googleapis.com/v1beta"
            )

        return str(value).rstrip("/")

    @field_validator(
        "ai_api_key",
        "gemini_api_key",
        mode="before",
    )
    @classmethod
    def normalize_ai_api_keys(cls, value):
        if value is None:
            return None

        value = str(value).strip()

        return value or None

    @field_validator(
        "ai_max_tokens",
        mode="before",
    )
    @classmethod
    def parse_ai_max_tokens(cls, value):
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return None

        return value

    @field_validator(
        "ai_timeout_seconds",
        "ai_temperature",
        mode="before",
    )
    @classmethod
    def parse_optional_ai_numbers(cls, value):
        if isinstance(value, str):
            value = value.strip()

            if not value:
                return None

        return value

    # ------------------------------------------------------------------
    # Database URLs
    # ------------------------------------------------------------------

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_db}"
        )

    @property
    def test_database_url(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_test_db}"
        )

    # ------------------------------------------------------------------
    # Pydantic settings configuration
    # ------------------------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()