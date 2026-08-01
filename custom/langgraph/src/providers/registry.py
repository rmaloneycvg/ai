"""Provider registry — factory that instantiates the correct LLM backend.

Resolution order: CLI args > env vars > config/providers.yaml defaults.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from .anthropic import AnthropicProvider
from .base import LLMProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .vllm import VLLMProvider

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "providers.yaml"

# Provider class lookup
_PROVIDERS: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "vllm": VLLMProvider,
}


def _load_config() -> dict:
    """Load providers.yaml config."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def _get_model_config(config: dict, provider_name: str, model_name: str) -> dict:
    """Extract model-specific config from providers.yaml."""
    providers = config.get("providers", {})
    provider_config = providers.get(provider_name, {})
    models = provider_config.get("models", {})
    return models.get(model_name, {})


def get_provider(
    provider_name: str | None = None,
    model_name: str | None = None,
    **kwargs,
) -> LLMProvider:
    """Create an LLM provider instance.

    Args:
        provider_name: Provider backend (ollama, openai, anthropic, vllm, llamacpp).
            Falls back to LLM_PROVIDER env var, then config defaults.
        model_name: Model identifier.
            Falls back to LLM_MODEL env var, then config defaults.
        **kwargs: Additional kwargs passed to the provider constructor.

    Returns:
        Configured LLMProvider instance.

    Raises:
        ValueError: If provider_name is not recognized.
    """
    config = _load_config()
    defaults = config.get("defaults", {})

    # Resolve provider
    provider_name = (
        provider_name or os.environ.get("LLM_PROVIDER") or defaults.get("provider", "ollama")
    )

    # Resolve model
    model_name = model_name or os.environ.get("LLM_MODEL") or defaults.get("model", "llama3.1:8b")

    # Get model-specific config from yaml
    model_config = _get_model_config(config, provider_name, model_name)

    # Build constructor kwargs
    ctor_kwargs: dict = {
        "model": model_name,
        "context_window": model_config.get("context_window", 8192),
        "supports_tools": model_config.get("supports_tools", False),
        "supports_structured_output": model_config.get("supports_structured_output", False),
    }

    # Provider-specific connection args
    if provider_name == "ollama":
        ctor_kwargs["base_url"] = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    elif provider_name == "openai":
        ctor_kwargs["api_key"] = os.environ.get("OPENAI_API_KEY", "")
    elif provider_name == "anthropic":
        ctor_kwargs["api_key"] = os.environ.get("ANTHROPIC_API_KEY", "")
    elif provider_name == "vllm":
        ctor_kwargs["base_url"] = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
    elif provider_name == "llamacpp":
        from .llamacpp import LlamaCppProvider

        _PROVIDERS["llamacpp"] = LlamaCppProvider
        ctor_kwargs["model_path"] = os.environ.get("LLAMACPP_MODEL_PATH", "")
        # LlamaCpp doesn't use 'model' kwarg
        ctor_kwargs.pop("model", None)

    # Merge any caller-provided overrides
    ctor_kwargs.update(kwargs)

    # Instantiate
    provider_cls = _PROVIDERS.get(provider_name)
    if provider_cls is None:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(_PROVIDERS.keys())}")

    return provider_cls(**ctor_kwargs)


def list_providers() -> list[str]:
    """Return list of available provider names."""
    return list(_PROVIDERS.keys()) + ["llamacpp"]


def list_configured_models() -> dict[str, list[str]]:
    """Return {provider: [model_names]} from config."""
    config = _load_config()
    result: dict[str, list[str]] = {}
    for provider_name, provider_config in config.get("providers", {}).items():
        models = provider_config.get("models", {})
        result[provider_name] = list(models.keys())
    return result
