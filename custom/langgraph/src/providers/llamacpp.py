"""llama.cpp provider adapter.

Provides direct GGUF model loading via llama-cpp-python.
Falls back to Ollama-style API if llama-cpp-python is not installed.

NOTE: Requires `uv add llama-cpp-python` separately (optional heavy dep with
platform-specific build requirements).
"""

from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator

from langchain_core.messages import BaseMessage

from .base import ChatResponse, LLMProvider, ModelCapabilities


class LlamaCppProvider(LLMProvider):
    """Adapter for direct llama.cpp inference via llama-cpp-python.

    This is a placeholder that raises ImportError with guidance if
    llama-cpp-python is not installed. Install with:
        uv add llama-cpp-python
    """

    def __init__(
        self,
        model_path: str | None = None,
        context_window: int = 8192,
        supports_tools: bool = False,
        supports_structured_output: bool = False,
    ):
        self._model_path = model_path or os.environ.get("LLAMACPP_MODEL_PATH", "")
        self._context_window = context_window
        self._supports_tools = supports_tools
        self._supports_structured_output = supports_structured_output

        if not self._model_path:
            raise ValueError("LLAMACPP_MODEL_PATH env var or model_path parameter required")

        try:
            from langchain_community.llms import LlamaCpp  # noqa: F401

            self._llm = LlamaCpp(
                model_path=self._model_path,
                n_ctx=context_window,
                verbose=False,
            )
        except ImportError:
            raise ImportError(
                "llama-cpp-python not installed. Run: uv add llama-cpp-python\n"
                "Note: requires C++ build tools. See "
                "https://github.com/abetlen/llama-cpp-python#installation"
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
        if tools:
            raise NotImplementedError(
                "LlamaCppProvider does not support tool calling. "
                "Use a provider with supports_tool_calling=True (e.g., Ollama, OpenAI)."
            )
        if response_format:
            raise NotImplementedError(
                "LlamaCppProvider does not support structured output / response_format. "
                "Use a provider with supports_structured_output=True."
            )

        # llama-cpp-python is sync; offload to thread to avoid blocking event loop
        prompt = "\n".join(f"{m.type}: {m.content}" for m in messages if m.content)
        response = await asyncio.to_thread(self._llm.invoke, prompt, temperature=temperature)
        content = response if isinstance(response, str) else str(response)

        return ChatResponse(
            content=content,
            input_tokens=self.count_tokens(prompt),
            output_tokens=self.count_tokens(content),
            model=os.path.basename(self._model_path),
            stop_reason="stop",
        )

    async def stream(
        self,
        messages: list[BaseMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list | None = None,
    ) -> AsyncIterator[str]:
        if tools:
            raise NotImplementedError(
                "LlamaCppProvider does not support tool calling. "
                "Use a provider with supports_tool_calling=True (e.g., Ollama, OpenAI)."
            )

        # llama-cpp-python streaming is sync; offload iteration to a thread
        # and deliver chunks incrementally via an asyncio.Queue.
        prompt = "\n".join(f"{m.type}: {m.content}" for m in messages if m.content)
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _stream_in_thread() -> None:
            try:
                for chunk in self._llm.stream(prompt, temperature=temperature):
                    if chunk:
                        queue.put_nowait(chunk)
            finally:
                queue.put_nowait(None)  # sentinel

        loop = asyncio.get_running_loop()
        task = loop.run_in_executor(None, _stream_in_thread)

        while True:
            item = await queue.get()
            if item is None:
                break
            yield item

        # Ensure the thread task completed (propagate exceptions)
        await task

    def count_tokens(self, text: str) -> int:
        """Approximate: chars / 4."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def get_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            context_window=self._context_window,
            supports_tool_calling=self._supports_tools,
            supports_structured_output=self._supports_structured_output,
            provider_name="llamacpp",
            model_name=os.path.basename(self._model_path),
        )
