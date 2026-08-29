from backend.app.ai.dependencies import get_ai_gateway
from backend.app.ai.gateway import ModelGateway


def test_get_ai_gateway_returns_model_gateway():
    get_ai_gateway.cache_clear()

    gateway = get_ai_gateway()

    assert isinstance(
        gateway,
        ModelGateway,
    )

    assert gateway.provider.name == "gemini"

    get_ai_gateway.cache_clear()