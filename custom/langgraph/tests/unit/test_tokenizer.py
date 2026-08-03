"""Unit tests for the unified tokenizer."""

from src.context.tokenizer import Tokenizer


class TestTokenizer:
    def test_empty_string_returns_zero(self):
        tok = Tokenizer()
        assert tok.count("") == 0

    def test_approximation_reasonable(self):
        tok = Tokenizer()
        # "hello world" = 11 chars, ~3 tokens (chars/4)
        count = tok.count("hello world")
        assert 1 <= count <= 5

    def test_long_text_scales(self):
        tok = Tokenizer()
        short = tok.count("hello")
        long = tok.count("hello " * 100)
        assert long > short

    def test_for_model_tiktoken(self):
        tok = Tokenizer.for_model("gpt-4o")
        # tiktoken should give accurate count for known text
        count = tok.count("Hello, world!")
        assert count > 0
        assert count < 10  # Should be 4 tokens

    def test_for_model_unknown_falls_back(self):
        tok = Tokenizer.for_model("some-unknown-model-xyz")
        count = tok.count("Hello, world!")
        assert count > 0

    def test_count_messages(self):
        from langchain_core.messages import HumanMessage, SystemMessage

        tok = Tokenizer()
        messages = [
            SystemMessage(content="You are helpful."),
            HumanMessage(content="Hello!"),
        ]
        count = tok.count_messages(messages)
        # Should include per-message overhead (4 tokens each)
        assert count >= 8  # At least overhead for 2 messages

    def test_with_provider(self, mock_provider):
        tok = Tokenizer(provider=mock_provider)
        count = tok.count("test string")
        # Should use provider's count_tokens method
        assert count == mock_provider.count_tokens("test string")
