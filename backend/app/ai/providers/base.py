from abc import ABC, abstractmethod

from backend.app.ai.schemas.models import (
    ModelRequest,
    ModelResponse,
)


class ModelProvider(ABC):
    """
    Abstract interface for all AI model providers.

    Concrete providers must implement this interface.
    """

    name: str

    @abstractmethod
    async def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        """
        Generate a response from the configured model provider.
        """

        raise NotImplementedError