"""OpenAI provider adapter.

Wraps langchain-openai's ChatOpenAI. Uses tiktoken for accurate token counting.
No context window cap (external model — uses model's reported max).
"""

from __future__ import annotations

import os
from typing import AsyncIterator

import tiktoken
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from .base import ChatResponse, LLMProvider, ModelCapabilities


class OpenAIProvider(LLMProvider):
    """Adapter for OpenAI API models."""

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        context_window: int = 128000,
        supports_tools: bool = True,
        supports_structured_output: bool = True,
    ):
        self._model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._context_window = context_window
        self._supports_tools = supports_tools
        self._supports_structured_output = supports_structured_output
        self._llm = ChatOpenAI(
            model=model,
            api_key=self._api_key,
        )
        # Initialize tokenizer for accurate counting
        try:
            self._encoding = tiktoken.encoding_for_model(model)
        except KeyError:
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
        kwargs: dict = {"temperature": temperature}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        llm = self._llm
        if tools:
            llm = llm.bind_tools(tools)
        if response_format:
            llm = llm.bind(response_format=response_format)

        response = await llm.ainvoke(messages, **kwargs)
        content = response.content if isinstance(response.content, str) else ""

        # Extract token usage from response metadata
        usage = response.response_metadata.get("token_usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        return ChatResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self._model,
            stop_reason=response.response_metadata.get("finish_reason"),
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
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        llm = self._llm
        if tools:
            llm = llm.bind_tools(tools)

        async for chunk in llm.astream(messages, **kwargs):
            if chunk.content:
                yield chunk.content

    def count_tokens(self, text: str) -> int:
        """Accurate token count via tiktoken."""
        if not text:
            return 0
        return len(self._encoding.encode(text))

    def get_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            context_window=self._context_window,
            supports_tool_calling=self._supports_tools,
            supports_structured_output=self._supports_structured_output,
            provider_name="openai",
            model_name=self._model,
        )

    def get_chat_model(self) -> ChatOpenAI:
        return self._llm
