"""Anthropic/Claude provider adapter.

Wraps langchain-anthropic's ChatAnthropic. Uses tiktoken cl100k_base as
approximation for token counting (Anthropic doesn't expose a public tokenizer).
No context window cap (external model).
"""

from __future__ import annotations

import os
from typing import AsyncIterator

import tiktoken
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage

from .base import ChatResponse, LLMProvider, ModelCapabilities


class AnthropicProvider(LLMProvider):
    """Adapter for Anthropic Claude API models."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
        context_window: int = 200000,
        supports_tools: bool = True,
        supports_structured_output: bool = True,
    ):
        self._model = model
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._context_window = context_window
        self._supports_tools = supports_tools
        self._supports_structured_output = supports_structured_output
        self._llm = ChatAnthropic(
            model=model,
            anthropic_api_key=self._api_key,
            max_tokens=4096,
        )
        self._encoding = tiktoken.get_encoding("cl100k_base")

    async def chat(
        self,
        messages: list[BaseMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list | None = None,
        response_format: dict | None = None,
    ) -> ChatResponse:
        llm = self._llm
        if max_tokens:
            llm = llm.bind(max_tokens=max_tokens)
        if tools:
            llm = llm.bind_tools(tools)

        response = await llm.ainvoke(messages, temperature=temperature)
        content = response.content if isinstance(response.content, str) else ""

        usage = response.response_metadata.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        return ChatResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self._model,
            stop_reason=response.response_metadata.get("stop_reason"),
        )

    async def stream(
        self,
        messages: list[BaseMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list | None = None,
    ) -> AsyncIterator[str]:
        llm = self._llm
        if max_tokens:
            llm = llm.bind(max_tokens=max_tokens)
        if tools:
            llm = llm.bind_tools(tools)

        async for chunk in llm.astream(messages, temperature=temperature):
            if chunk.content:
                yield chunk.content

    def count_tokens(self, text: str) -> int:
        """Approximate token count using cl100k_base encoding."""
        if not text:
            return 0
        return len(self._encoding.encode(text))

    def get_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            context_window=self._context_window,
            supports_tool_calling=self._supports_tools,
            supports_structured_output=self._supports_structured_output,
            provider_name="anthropic",
            model_name=self._model,
        )

    def get_chat_model(self) -> ChatAnthropic:
        return self._llm
