"""Provider factory."""

from app.features.proxy.providers import AnthropicProvider, OpenAIProvider, ProviderClient


def get_provider(provider: str) -> ProviderClient:
    if provider == "openai":
        return OpenAIProvider()
    if provider == "anthropic":
        return AnthropicProvider()
    raise ValueError(f"Unsupported provider: {provider}")
