"""Tests for the model mapper."""

from pathlib import Path

import pytest

from src.runtime.model_mapper import ModelMapper, ModelMapping


@pytest.fixture
def mapper(tmp_path):
    """Model mapper with a test config."""
    config = tmp_path / "model-mapping.yaml"
    config.write_text("""
default: llama3.1:8b

tiers:
  strong: qwen2.5:14b
  medium: llama3.1:8b
  fast: tinyllama

overrides:
  claude-opus-4.8: qwen2.5:14b
  gpt-4o: qwen2.5:14b
""")
    return ModelMapper(config_path=config)


@pytest.fixture
def mapper_no_config(tmp_path):
    """Model mapper with no config file (uses defaults)."""
    return ModelMapper(config_path=tmp_path / "nonexistent.yaml")


class TestModelMapper:
    """Tests for model reference resolution."""

    def test_resolve_direct_override(self, mapper):
        assert mapper.resolve("claude-opus-4.8") == "qwen2.5:14b"
        assert mapper.resolve("gpt-4o") == "qwen2.5:14b"

    def test_resolve_by_tier_strong(self, mapper):
        # Opus models → strong tier
        assert mapper.resolve("claude-opus-4.5") == "qwen2.5:14b"
        assert mapper.resolve("claude-opus-4.7") == "qwen2.5:14b"

    def test_resolve_by_tier_medium(self, mapper):
        # Sonnet 3.5 → medium
        assert mapper.resolve("claude-sonnet-3.5") == "llama3.1:8b"

    def test_resolve_by_tier_fast(self, mapper):
        # Haiku → fast tier
        assert mapper.resolve("claude-haiku-4.5") == "tinyllama"
        assert mapper.resolve("claude-haiku-3") == "tinyllama"

    def test_resolve_none_returns_default(self, mapper):
        assert mapper.resolve(None) == "llama3.1:8b"

    def test_resolve_unknown_model_uses_medium(self, mapper):
        # Unknown models default to medium tier
        assert mapper.resolve("some-unknown-model") == "llama3.1:8b"

    def test_resolve_sonnet_4_plus_is_strong(self, mapper):
        assert mapper.resolve("claude-sonnet-4") == "qwen2.5:14b"
        assert mapper.resolve("claude-sonnet-5") == "qwen2.5:14b"

    def test_get_tier(self, mapper):
        assert mapper.get_tier("claude-opus-4.8") == "strong"
        assert mapper.get_tier("claude-haiku-4.5") == "fast"
        assert mapper.get_tier("gpt-4o") == "strong"
        assert mapper.get_tier("gpt-4o-mini") == "medium"

    def test_no_config_falls_back(self, mapper_no_config):
        # With no config file, mapper builds from profiles or uses defaults.
        # Result depends on whether config/model-profiles/ has entries.
        result = mapper_no_config.resolve("claude-opus-4.8")
        # Should resolve to some model (not crash)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_resolve_for_agent(self, mapper):
        prompt = """
        ## Sub-Agents
        - react-scaffold stages: model: 'claude-haiku-4.5'
        - react-architecture stages: model: 'claude-opus-4.8'
        """
        assert mapper.resolve_for_agent("react-scaffold", prompt) == "tinyllama"
        assert mapper.resolve_for_agent("react-architecture", prompt) == "qwen2.5:14b"

    def test_resolve_for_agent_no_match(self, mapper):
        prompt = "No model assignments here."
        # Falls back to default
        assert mapper.resolve_for_agent("unknown-agent", prompt) == "llama3.1:8b"
