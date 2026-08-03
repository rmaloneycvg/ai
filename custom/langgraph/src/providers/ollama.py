"""Ollama provider adapter.

Wraps langchain-ollama's ChatOllama for local model inference.
Token counting uses chars/4 approximation (no tokenizer available locally).
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
        self._llm = ChatOllama(
            model=model,
            base_url=self._base_url,
            num_ctx=context_window,
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
        kwargs: dict = {"temperature": temperature}
        if max_tokens is not None:
            kwargs["num_predict"] = max_tokens

        llm = self._llm
        if tools:
            llm = llm.bind_tools(tools)
        if response_format:
            llm = llm.bind(format=response_format.get("type", "json"))

        response = await llm.ainvoke(messages, **kwargs)
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
        kwargs: dict = {"temperature": temperature}
        if max_tokens is not None:
            kwargs["num_predict"] = max_tokens

        llm = self._llm
        if tools:
            llm = llm.bind_tools(tools)

        async for chunk in llm.astream(messages, **kwargs):
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
        return self._llm
