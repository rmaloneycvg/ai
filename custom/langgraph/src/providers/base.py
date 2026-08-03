"""Abstract LLM provider interface.

All provider adapters implement this protocol so the rest of the system
is backend-agnostic. The registry instantiates the correct provider from
config/env at runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator

from langchain_core.messages import BaseMessage


@dataclass(frozen=True)
class ModelCapabilities:
    """Static capabilities reported by a model/provider combination."""

    context_window: int
    supports_tool_calling: bool
    supports_structured_output: bool
    provider_name: str
    model_name: str


@dataclass
class ChatResponse:
    """Unified response from any provider."""

    content: str
    input_tokens: int
    output_tokens: int
    model: str
    stop_reason: str | None = None


class LLMProvider(ABC):
    """Protocol for all LLM backend adapters."""

    @abstractmethod
    async def chat(
        self,
        messages: list[BaseMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list | None = None,
        response_format: dict | None = None,
    ) -> ChatResponse:
        """Send messages and get a complete response."""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[BaseMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list | None = None,
    ) -> AsyncIterator[str]:
        """Stream response tokens."""
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens for the given text using model-appropriate tokenizer."""
        ...

    @abstractmethod
    def get_capabilities(self) -> ModelCapabilities:
        """Return static model capabilities."""
        ...

    @property
    def context_window(self) -> int:
        """Shortcut to get context window size."""
        return self.get_capabilities().context_window

    @property
    def supports_tool_calling(self) -> bool:
        """Shortcut to check tool calling support."""
        return self.get_capabilities().supports_tool_calling

    @property
    def supports_structured_output(self) -> bool:
        """Shortcut to check structured output support."""
        return self.get_capabilities().supports_structured_output

    def get_chat_model(self):
        """Return the underlying LangChain ChatModel for use in LangGraph nodes.

        Subclasses should override to return their specific ChatModel instance.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not expose a raw ChatModel")
