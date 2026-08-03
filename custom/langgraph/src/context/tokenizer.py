"""Unified token counting across model providers.

Uses tiktoken for OpenAI models, chars/4 approximation for local models.
Provider-aware: detects the best counting method from the provider instance.
"""

from __future__ import annotations

from functools import lru_cache

import tiktoken

from src.providers.base import LLMProvider


@lru_cache(maxsize=8)
def _get_encoding(model: str) -> tiktoken.Encoding | None:
    """Get tiktoken encoding for a model, or None if not available."""
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None


class Tokenizer:
    """Unified token counter that adapts to the active provider."""

    def __init__(self, provider: LLMProvider | None = None):
        self._provider = provider

    def count(self, text: str) -> int:
        """Count tokens in text using the best available method.

        Resolution order:
        1. Provider's own count_tokens method (if provider set)
        2. tiktoken (if encoding available)
        3. chars / 4 approximation
        """
        if not text:
            return 0

        if self._provider:
            return self._provider.count_tokens(text)

        return self._approximate_count(text)

    def count_messages(self, messages: list) -> int:
        """Count total tokens across a list of messages.

        Each message adds ~4 tokens overhead (role, separators).
        """
        total = 0
        for msg in messages:
            content = ""
            if hasattr(msg, "content"):
                content = msg.content or ""
            elif isinstance(msg, dict):
                content = msg.get("content", "")
            total += self.count(content) + 4  # per-message overhead
        return total

    @staticmethod
    def _approximate_count(text: str) -> int:
        """Fallback: chars / 4 approximation."""
        return max(1, len(text) // 4)

    @classmethod
    def for_model(cls, model_name: str) -> "Tokenizer":
        """Create a tokenizer optimized for a specific model name.

        Uses tiktoken if the model is recognized, otherwise falls back
        to approximation.
        """
        encoding = _get_encoding(model_name)
        if encoding:
            return _TiktokenWrapper(encoding)
        return cls(provider=None)


class _TiktokenWrapper(Tokenizer):
    """Tokenizer backed by a specific tiktoken encoding."""

    def __init__(self, encoding: tiktoken.Encoding):
        super().__init__(provider=None)
        self._encoding = encoding

    def count(self, text: str) -> int:
        if not text:
            return 0
        return len(self._encoding.encode(text))
