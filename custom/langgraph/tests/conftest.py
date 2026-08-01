"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.profile import ModelProfile, ModelScores, ModelStrategies, ReasoningLevel
from src.providers.base import ChatResponse, LLMProvider, ModelCapabilities


@pytest.fixture
def mock_provider() -> LLMProvider:
    """Mock provider that returns deterministic responses."""
    provider = MagicMock(spec=LLMProvider)
    provider.get_capabilities.return_value = ModelCapabilities(
        context_window=8192,
        supports_tool_calling=True,
        supports_structured_output=True,
        provider_name="mock",
        model_name="mock-model",
    )
    provider.context_window = 8192
    provider.count_tokens = lambda text: max(1, len(text) // 4) if text else 0

    async def mock_chat(*args, **kwargs):
        return ChatResponse(
            content="Mock response",
            input_tokens=10,
            output_tokens=5,
            model="mock-model",
        )

    provider.chat = AsyncMock(side_effect=mock_chat)
    return provider


@pytest.fixture
def weak_profile() -> ModelProfile:
    """Profile representing a weak local model."""
    return ModelProfile(
        model_name="tinyllama",
        provider="ollama",
        context_window=2048,
        scores=ModelScores(
            reasoning=3.0,
            instruction_following=4.0,
            structured_output=3.0,
            tool_calling=2.0,
            creativity=5.0,
        ),
        strategies=ModelStrategies(
            cot_needed=True,
            json_mode=False,
            xml_preferred=False,
            max_tools_per_call=3,
            prompt_length_sweet_spot=600,
            examples_needed=3,
            reasoning_scaffolding=ReasoningLevel.FULL,
        ),
    )


@pytest.fixture
def strong_profile() -> ModelProfile:
    """Profile representing a strong external model."""
    return ModelProfile(
        model_name="gpt-4o",
        provider="openai",
        context_window=128000,
        scores=ModelScores(
            reasoning=9.0,
            instruction_following=9.5,
            structured_output=9.0,
            tool_calling=9.5,
            creativity=8.5,
        ),
        strategies=ModelStrategies(
            cot_needed=False,
            json_mode=True,
            xml_preferred=False,
            max_tools_per_call=15,
            prompt_length_sweet_spot=70000,
            examples_needed=0,
            reasoning_scaffolding=ReasoningLevel.NONE,
        ),
    )


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture
def tmp_output(tmp_path) -> Path:
    """Temporary output directory for test artifacts."""
    output = tmp_path / "output"
    output.mkdir()
    return output
