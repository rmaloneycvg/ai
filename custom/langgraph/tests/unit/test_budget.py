"""Unit tests for the token budget manager."""

import pytest

from src.context.budget import ContextBudgetError, ContextBudgetManager


class TestContextBudgetManager:
    def test_allocations_sum_to_context_window_8k(self):
        mgr = ContextBudgetManager("llama3.1:8b", context_window=8192)
        report = mgr.get_report()
        assert report.total_allocated <= report.total_context

    def test_allocations_sum_to_context_window_32k(self):
        mgr = ContextBudgetManager("qwen2.5:14b", context_window=32768)
        report = mgr.get_report()
        assert report.total_allocated <= report.total_context

    def test_allocations_sum_to_context_window_128k(self):
        mgr = ContextBudgetManager("gpt-4o", context_window=128000)
        report = mgr.get_report()
        assert report.total_allocated <= report.total_context

    def test_proportional_scaling_larger_window_gets_more(self):
        mgr_small = ContextBudgetManager("test-small", context_window=8192)
        mgr_large = ContextBudgetManager("test-large", context_window=32768)

        # Larger window should have larger allocations per layer
        assert mgr_large.allocated("retrieved") > mgr_small.allocated("retrieved")
        assert mgr_large.allocated("history") > mgr_small.allocated("history")

    def test_use_tracks_consumption(self):
        mgr = ContextBudgetManager("test", context_window=8192)
        mgr.use("history", 100)
        assert mgr.used("history") == 100
        assert mgr.remaining("history") == mgr.allocated("history") - 100

    def test_overflow_raises_on_bounded_layer(self):
        mgr = ContextBudgetManager("test", context_window=8192)
        allocated = mgr.allocated("history")

        with pytest.raises(ContextBudgetError) as exc_info:
            mgr.use("history", allocated + 1)

        assert exc_info.value.layer == "history"
        assert exc_info.value.used == allocated + 1

    def test_protected_layer_does_not_raise_on_overflow(self):
        mgr = ContextBudgetManager("test", context_window=8192)
        allocated = mgr.allocated("system")
        # Protected layers don't raise
        mgr.use("system", allocated + 100)
        assert mgr.used("system") == allocated + 100

    def test_can_fit_checks_remaining(self):
        mgr = ContextBudgetManager("test", context_window=8192)
        allocated = mgr.allocated("tools")
        assert mgr.can_fit("tools", allocated)
        assert not mgr.can_fit("tools", allocated + 1)

    def test_reset_clears_usage(self):
        mgr = ContextBudgetManager("test", context_window=8192)
        mgr.use("system", 100)
        mgr.reset("system")
        assert mgr.used("system") == 0

    def test_reset_all(self):
        mgr = ContextBudgetManager("test", context_window=8192)
        mgr.use("system", 100)
        mgr.use("tools", 200)
        mgr.reset()
        assert mgr.used("system") == 0
        assert mgr.used("tools") == 0

    def test_unknown_layer_raises_keyerror(self):
        mgr = ContextBudgetManager("test", context_window=8192)
        with pytest.raises(KeyError):
            mgr.use("nonexistent", 100)

    def test_min_tokens_enforced(self):
        mgr = ContextBudgetManager("test", context_window=2048)
        # Even with tiny context, layers should have at least min_tokens
        for layer in mgr.layers.values():
            assert layer.allocated >= layer.min_tokens
