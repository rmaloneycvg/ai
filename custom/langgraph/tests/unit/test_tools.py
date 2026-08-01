"""Unit tests for tool registry."""

from src.tools.registry import ALL_TOOLS, PHASES, ToolRegistry


class TestToolRegistry:
    def test_get_tools_for_phase(self):
        registry = ToolRegistry(max_tools_per_call=8)
        tools = registry.get_tools("skill_create")
        assert len(tools) > 0
        assert len(tools) <= 8

    def test_unknown_phase_falls_back(self):
        registry = ToolRegistry()
        tools = registry.get_tools("nonexistent_phase")
        assert len(tools) > 0  # Falls back to skill_create

    def test_max_tools_limit_enforced(self):
        registry = ToolRegistry(max_tools_per_call=3)
        tools = registry.get_tools("full")
        assert len(tools) <= 3

    def test_compressed_schemas_smaller(self):
        registry = ToolRegistry()
        full_tokens = registry.estimate_tokens("full", compressed=False)
        compressed_tokens = registry.estimate_tokens("full", compressed=True)
        assert compressed_tokens < full_tokens

    def test_all_phases_defined(self):
        expected_phases = [
            "skill_create",
            "agent_create",
            "steering_write",
            "tool_build",
            "model_profile",
            "observability",
            "project_management",
            "full",
        ]
        for phase in expected_phases:
            assert phase in PHASES

    def test_all_tool_domains_populated(self):
        expected_domains = [
            "git",
            "io",
            "postgres",
            "prometheus",
            "jaeger",
            "grafana",
            "jira",
            "linear",
            "shell",
        ]
        for domain in expected_domains:
            assert domain in ALL_TOOLS
            assert len(ALL_TOOLS[domain]) > 0

    def test_tools_have_docstrings(self):
        for domain, tools in ALL_TOOLS.items():
            for tool in tools:
                assert tool.description, f"Tool {tool.name} in {domain} missing description"

    def test_phase_info_returns_metadata(self):
        registry = ToolRegistry()
        info = registry.get_phase_info("skill_create")
        assert info is not None
        assert info.name == "skill_create"
        assert info.description != ""

    def test_list_phases(self):
        registry = ToolRegistry()
        phases = registry.list_phases()
        assert "skill_create" in phases
        assert "full" in phases
