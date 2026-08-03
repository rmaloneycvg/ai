"""vLLM provider adapter.

vLLM exposes an OpenAI-compatible API. This adapter uses ChatOpenAI with a
custom base_url pointing to the vLLM server.
"""

from __future__ import annotations

import os
from typing import AsyncIterator

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from .base import ChatResponse, LLMProvider, ModelCapabilities


class VLLMProvider(LLMProvider):
    """Adapter for vLLM OpenAI-compatible server."""

    def __init__(
        self,
        model: str = "default",
        base_url: str | None = None,
        context_window: int = 32768,
        supports_tools: bool = True,
        supports_structured_output: bool = True,
    ):
        self._model = model
        self._base_url = base_url or os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
        self._context_window = context_window
        self._supports_tools = supports_tools
        self._supports_structured_output = supports_structured_output
        self._llm = ChatOpenAI(
            model=model,
            base_url=self._base_url,
            api_key="not-needed",  # vLLM doesn't require auth by default
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
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        llm = self._llm
        if tools:
            llm = llm.bind_tools(tools)
        if response_format:
            llm = llm.bind(response_format=response_format)

        response = await llm.ainvoke(messages, **kwargs)
        content = response.content if isinstance(response.content, str) else ""

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
        """Approximate: chars / 4 (no local tokenizer for arbitrary vLLM models)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def get_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            context_window=self._context_window,
            supports_tool_calling=self._supports_tools,
            supports_structured_output=self._supports_structured_output,
            provider_name="vllm",
            model_name=self._model,
        )

    def get_chat_model(self) -> ChatOpenAI:
        return self._llm
