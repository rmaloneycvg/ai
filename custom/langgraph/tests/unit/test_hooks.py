"""Tests for hook execution."""

import asyncio

import pytest

from src.runtime.hooks import execute_hooks, format_hook_context, _derive_key


class TestHookExecution:
    """Tests for agentSpawn hook execution."""

    def test_execute_simple_hook(self):
        hooks = {
            "agentSpawn": [
                {"command": "echo hello world", "timeout_ms": 3000},
            ]
        }
        results = asyncio.run(execute_hooks(hooks))
        assert "hello world" in results.get("echo_hello", "")

    def test_execute_multiple_hooks(self):
        hooks = {
            "agentSpawn": [
                {"command": "echo first", "timeout_ms": 3000},
                {"command": "echo second", "timeout_ms": 3000},
            ]
        }
        results = asyncio.run(execute_hooks(hooks))
        assert len(results) == 2

    def test_hook_timeout_handled(self):
        hooks = {
            "agentSpawn": [
                {"command": "sleep 10", "timeout_ms": 100},
            ]
        }
        results = asyncio.run(execute_hooks(hooks))
        # Should not raise, but should report timeout
        key = list(results.keys())[0]
        assert "timed out" in results[key]

    def test_hook_command_not_found(self):
        hooks = {
            "agentSpawn": [
                {"command": "nonexistent_command_xyz", "timeout_ms": 3000},
            ]
        }
        results = asyncio.run(execute_hooks(hooks))
        key = list(results.keys())[0]
        assert "[" in results[key]  # Wrapped in error brackets

    def test_empty_hooks(self):
        results = asyncio.run(execute_hooks({}))
        assert results == {}

    def test_no_agent_spawn(self):
        results = asyncio.run(execute_hooks({"someOtherHook": []}))
        assert results == {}


class TestDeriveKey:
    """Tests for hook key derivation."""

    def test_git_status(self):
        assert _derive_key("git status --porcelain") == "git_status"

    def test_git_branch(self):
        assert _derive_key("git branch --show-current") == "git_branch"

    def test_node_version(self):
        assert _derive_key("node --version") == "node"

    def test_package_json_pipe(self):
        assert _derive_key("cat package.json | grep name") == "package_info"

    def test_empty_command(self):
        assert _derive_key("") == "unknown"


class TestFormatHookContext:
    """Tests for formatting hook results into prompt context."""

    def test_formats_successful_hooks(self):
        results = {
            "git_status": "M src/file.py",
            "git_branch": "feat/new-feature",
        }
        formatted = format_hook_context(results)
        assert "Current Environment" in formatted
        assert "feat/new-feature" in formatted

    def test_skips_failed_hooks(self):
        results = {
            "git_status": "M src/file.py",
            "bad_hook": "[hook failed: timeout]",
        }
        formatted = format_hook_context(results)
        assert "hook failed" not in formatted
        assert "M src/file.py" in formatted

    def test_empty_results(self):
        assert format_hook_context({}) == ""
