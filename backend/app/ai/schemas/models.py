from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelMessage:
    """
    A single message sent to an AI model.
    """

    role: str
    content: str


@dataclass(frozen=True)
class ModelRequest:
    """
    Provider-agnostic request sent through the model gateway.
    """

    messages: list[ModelMessage]
    model: str | None = None
    temperature: float = 0.2
    max_tokens: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelUsage:
    """
    Token usage returned by a model provider.

    Providers may not always expose all values.
    """

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class ModelResponse:
    """
    Provider-agnostic response returned by the model gateway.
    """

    content: str
    model: str
    provider: str
    usage: ModelUsage | None = None
    finish_reason: str | None = None
    raw_response: dict[str, Any] | None = None