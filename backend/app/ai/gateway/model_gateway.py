from backend.app.ai.providers.base import ModelProvider
from backend.app.ai.schemas.models import (
    ModelRequest,
    ModelResponse,
)


class ModelGateway:
    """
    Central entry point for model inference.

    The gateway isolates the rest of the application from
    concrete model provider implementations.
    """

    def __init__(
        self,
        provider: ModelProvider,
    ) -> None:
        self.provider = provider

    async def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        """
        Generate a model response through the configured provider.
        """

        return await self.provider.generate(request)