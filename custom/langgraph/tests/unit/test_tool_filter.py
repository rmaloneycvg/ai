"""Tests for the tool filter — tool mapping, expansion, and constraints."""

from __future__ import annotations

from src.runtime.loader import LoadedAgent
from src.runtime.tool_filter import (
    _expand_tool_names,
    _path_matches_patterns,
    get_tools_for_agent,
)


class TestToolNameExpansion:
    """Tests for expanding Kiro tool names to internal tool map keys."""

    def test_direct_tool_names(self):
        """Direct tool names pass through unchanged."""
        result = _expand_tool_names(
            tools=["read", "write", "shell"],
            allowed_tools=["read", "write"],
        )
        assert "read" in result
        assert "write" in result
        assert "shell" not in result  # Not in allowed_tools

    def test_allowed_tools_takes_precedence(self):
        """allowed_tools is more restrictive than tools."""
        result = _expand_tool_names(
            tools=["read", "write", "shell", "glob", "grep"],
            allowed_tools=["read", "glob"],
        )
        assert result == ["glob", "read"]

    def test_empty_allowed_tools_uses_tools(self):
        """If allowed_tools is empty, falls back to tools."""
        result = _expand_tool_names(
            tools=["read", "write"],
            allowed_tools=[],
        )
        assert "read" in result
        assert "write" in result

    def test_mcp_server_expansion(self):
        """@git expands to all @git/* tools."""
        result = _expand_tool_names(
            tools=["@git"],
            allowed_tools=["@git"],
        )
        assert "@git/git_status" in result
        assert "@git/git_diff" in result
        assert "@git/git_log" in result

    def test_specific_mcp_tool(self):
        """@git/git_status resolves to exactly one tool."""
        result = _expand_tool_names(
            tools=["@git/git_status"],
            allowed_tools=["@git/git_status"],
        )
        assert result == ["@git/git_status"]

    def test_io_server_expansion(self):
        """@io expands to all @io/* tools."""
        result = _expand_tool_names(
            tools=["@io"],
            allowed_tools=["@io"],
        )
        assert "@io/read_json" in result
        assert "@io/write_json" in result

    def test_code_maps_to_glob_and_grep(self):
        """'code' tool in Kiro maps to glob + grep locally."""
        result = _expand_tool_names(
            tools=["code"],
            allowed_tools=["code"],
        )
        assert "glob" in result
        assert "grep" in result

    def test_mixed_tools(self):
        """Combination of direct, MCP, and code tools."""
        result = _expand_tool_names(
            tools=["read", "code", "@git"],
            allowed_tools=["read", "code", "@git/git_status"],
        )
        assert "read" in result
        assert "glob" in result
        assert "grep" in result
        assert "@git/git_status" in result
        assert "@git/git_diff" not in result  # Not in allowed

    def test_unknown_tool_name(self):
        """Unknown tool names are included in expansion but won't map to anything."""
        result = _expand_tool_names(
            tools=["read", "nonexistent_tool"],
            allowed_tools=["read", "nonexistent_tool"],
        )
        assert "read" in result
        assert "nonexistent_tool" in result  # Included, but get_tools_for_agent will skip it


class TestPathMatchingPatterns:
    """Tests for the path glob matching used by write constraints."""

    def test_simple_glob(self):
        assert _path_matches_patterns("src/file.ts", ["src/**"])

    def test_extension_glob(self):
        assert _path_matches_patterns("component.tsx", ["*.tsx"])

    def test_nested_path(self):
        assert _path_matches_patterns("src/components/Button.tsx", ["src/**"])

    def test_no_match(self):
        assert not _path_matches_patterns("config/db.yml", ["src/**", "*.tsx"])

    def test_leading_dot_slash_stripped(self):
        assert _path_matches_patterns("./src/file.ts", ["src/**"])

    def test_multiple_patterns(self):
        patterns = ["src/**", "app/**", "*.md"]
        assert _path_matches_patterns("src/index.ts", patterns)
        assert _path_matches_patterns("app/page.tsx", patterns)
        assert _path_matches_patterns("README.md", patterns)
        assert not _path_matches_patterns("terraform/main.tf", patterns)

    def test_empty_patterns_never_match(self):
        assert not _path_matches_patterns("anything.ts", [])

    def test_wildcard_matches_everything(self):
        assert _path_matches_patterns("deep/nested/path/file.py", ["**"])


class TestGetToolsForAgent:
    """Tests for the full tool resolution pipeline."""

    def test_basic_agent_gets_tools(self):
        """Agent with simple tool list gets resolved tools."""
        agent = LoadedAgent(
            name="test",
            description="test",
            prompt="test",
            tools=["read", "glob", "grep"],
            allowed_tools=["read", "glob", "grep"],
        )
        tools = get_tools_for_agent(agent)
        assert len(tools) == 3
        tool_names = [t.name for t in tools]
        assert "read_file" in tool_names
        assert "glob_search" in tool_names
        assert "grep_search" in tool_names

    def test_agent_with_mcp_tools(self):
        """Agent with MCP server references gets mapped tools."""
        agent = LoadedAgent(
            name="test",
            description="test",
            prompt="test",
            tools=["read", "@git"],
            allowed_tools=["read", "@git/git_status"],
        )
        tools = get_tools_for_agent(agent)
        tool_names = [t.name for t in tools]
        assert "read_file" in tool_names
        assert "git_status" in tool_names
        assert len(tools) == 2

    def test_write_tool_with_path_constraints(self):
        """Write tool gets wrapped with path checking."""
        agent = LoadedAgent(
            name="test",
            description="test",
            prompt="test",
            tools=["write"],
            allowed_tools=["write"],
            tools_settings={
                "write": {"allowedPaths": ["src/**", "*.ts"]}
            },
        )
        tools = get_tools_for_agent(agent)
        assert len(tools) == 1
        # The tool should be the constrained version
        write_tool = tools[0]
        assert write_tool.name == "constrained_write"

    def test_unknown_tools_filtered_out(self):
        """Tools that don't exist in the tool map are silently skipped."""
        agent = LoadedAgent(
            name="test",
            description="test",
            prompt="test",
            tools=["read", "nonexistent_xyz"],
            allowed_tools=["read", "nonexistent_xyz"],
        )
        tools = get_tools_for_agent(agent)
        assert len(tools) == 1
        assert tools[0].name == "read_file"

    def test_code_tool_resolves_to_glob_and_grep(self):
        """The 'code' abstract tool produces glob + grep implementations."""
        agent = LoadedAgent(
            name="test",
            description="test",
            prompt="test",
            tools=["code"],
            allowed_tools=["code"],
        )
        tools = get_tools_for_agent(agent)
        tool_names = [t.name for t in tools]
        assert "glob_search" in tool_names
        assert "grep_search" in tool_names

    def test_empty_tools_returns_empty(self):
        """Agent with no tools gets an empty list."""
        agent = LoadedAgent(
            name="test",
            description="test",
            prompt="test",
            tools=[],
            allowed_tools=[],
        )
        tools = get_tools_for_agent(agent)
        assert tools == []
