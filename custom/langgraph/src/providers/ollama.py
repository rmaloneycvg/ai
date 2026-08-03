"""Ollama provider adapter.

Wraps langchain-ollama's ChatOllama for local model inference.
Token counting uses chars/4 approximation (no tokenizer available locally).

NOTE: For GPU acceleration on WSL2 with AMD Radeon, run Ollama on the
Windows host and access from WSL2 via localhost (network mirroring) or
the gateway IP. Set OLLAMA_BASE_URL if localhost doesn't reach the host.
"""

from __future__ import annotations

import os
from typing import AsyncIterator

from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama

from .base import ChatResponse, LLMProvider, ModelCapabilities


class OllamaProvider(LLMProvider):
    """Adapter for Ollama local model server."""

    def __init__(
        self,
        model: str = "llama3.1:8b",
        base_url: str | None = None,
        context_window: int = 8192,
        supports_tools: bool = True,
        supports_structured_output: bool = True,
    ):
        self._model = model
        self._base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self._context_window = context_window
        self._supports_tools = supports_tools
        self._supports_structured_output = supports_structured_output

    def _build_llm(
        self,
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> ChatOllama:
        """Construct a ChatOllama instance with runtime parameters.

        langchain-ollama>=0.3 requires temperature/num_predict as constructor
        args rather than ainvoke kwargs.
        """
        return ChatOllama(
            model=self._model,
            base_url=self._base_url,
            num_ctx=self._context_window,
            temperature=temperature,
            num_predict=max_tokens or -1,
        )

    async def chat(
        self,
        messages: list[BaseMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list | None = None,
        response_format: dict | None = None,
    ) -> ChatResponse:
        llm = self._build_llm(temperature=temperature, max_tokens=max_tokens)

        if tools:
            llm = llm.bind_tools(tools)
        if response_format:
            llm = llm.bind(format=response_format.get("type", "json"))

        response = await llm.ainvoke(messages)
        content = response.content if isinstance(response.content, str) else ""

        # Ollama doesn't report token usage consistently; approximate
        input_tokens = sum(self.count_tokens(m.content or "") for m in messages)
        output_tokens = self.count_tokens(content)

        return ChatResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self._model,
            stop_reason=response.response_metadata.get("done_reason"),
        )

    async def stream(
        self,
        messages: list[BaseMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list | None = None,
    ) -> AsyncIterator[str]:
        llm = self._build_llm(temperature=temperature, max_tokens=max_tokens)

        if tools:
            llm = llm.bind_tools(tools)

        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content

    def count_tokens(self, text: str) -> int:
        """Approximate token count: chars / 4 for local models without tokenizer."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def get_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            context_window=self._context_window,
            supports_tool_calling=self._supports_tools,
            supports_structured_output=self._supports_structured_output,
            provider_name="ollama",
            model_name=self._model,
        )

    def get_chat_model(self) -> ChatOllama:
        """Return a default ChatOllama instance for LangGraph node usage."""
        return self._build_llm()
