"""Tool registry — phase-based activation and schema compression.

Provides only the tools relevant to the current task phase,
reducing context token consumption from tool schemas.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.tools import BaseTool

from src.tools import git, grafana, io, jaeger, jira, linear, postgres, prometheus, shell


@dataclass
class ToolPhase:
    """A named phase with its associated tools."""

    name: str
    tools: list[BaseTool]
    description: str


# All available tools organized by domain
ALL_TOOLS: dict[str, list[BaseTool]] = {
    "git": [git.git_status, git.git_diff, git.git_log],
    "io": [io.read_json, io.write_json, io.read_file, io.write_file],
    "postgres": [postgres.postgres_query, postgres.postgres_seed],
    "prometheus": [
        prometheus.prometheus_query,
        prometheus.prometheus_range_query,
        prometheus.prometheus_metrics,
        prometheus.prometheus_alerts,
    ],
    "jaeger": [
        jaeger.jaeger_services,
        jaeger.jaeger_search_traces,
        jaeger.jaeger_get_trace,
        jaeger.jaeger_analyze_bottlenecks,
    ],
    "grafana": [
        grafana.grafana_search_dashboards,
        grafana.grafana_query,
        grafana.grafana_annotations,
    ],
    "jira": [jira.jira_search_issues, jira.jira_create_issue, jira.jira_list_sprints],
    "linear": [linear.linear_list_issues, linear.linear_create_issue, linear.linear_list_cycles],
    "shell": [shell.run_command],
}

# Phase definitions — which tools are active per task type
PHASES: dict[str, ToolPhase] = {
    "skill_create": ToolPhase(
        name="skill_create",
        tools=[io.read_file, io.write_file, io.read_json, git.git_status],
        description="Creating skill files — file I/O and git status",
    ),
    "agent_create": ToolPhase(
        name="agent_create",
        tools=[io.read_file, io.write_file, io.read_json, io.write_json, git.git_status],
        description="Creating agent configs — file I/O, JSON, git",
    ),
    "steering_write": ToolPhase(
        name="steering_write",
        tools=[io.read_file, io.write_file, git.git_status],
        description="Writing steering docs — file I/O and git",
    ),
    "tool_build": ToolPhase(
        name="tool_build",
        tools=[io.read_file, io.write_file, shell.run_command, git.git_status],
        description="Building tools — file I/O, shell, git",
    ),
    "model_profile": ToolPhase(
        name="model_profile",
        tools=[io.read_json, io.write_json],
        description="Model profiling — reading/writing profile JSON",
    ),
    "rag_manage": ToolPhase(
        name="rag_manage",
        tools=[
            io.read_file, io.write_file, io.read_json, io.write_json,
            postgres.postgres_query, postgres.postgres_seed,
            git.git_status,
        ],
        description="RAG management — file I/O, postgres for pgvector, git",
    ),
    "observability": ToolPhase(
        name="observability",
        tools=[
            *ALL_TOOLS["prometheus"],
            *ALL_TOOLS["jaeger"],
            *ALL_TOOLS["grafana"],
        ],
        description="Observability — Prometheus, Jaeger, Grafana",
    ),
    "project_management": ToolPhase(
        name="project_management",
        tools=[*ALL_TOOLS["jira"], *ALL_TOOLS["linear"]],
        description="Project management — Jira, Linear",
    ),
    "full": ToolPhase(
        name="full",
        tools=[t for tools in ALL_TOOLS.values() for t in tools],
        description="All tools available",
    ),
}


class ToolRegistry:
    """Provides phase-based tool activation and schema compression."""

    def __init__(self, max_tools_per_call: int = 8):
        self._max_tools = max_tools_per_call

    def get_tools(self, phase: str) -> list[BaseTool]:
        """Get tools for a specific phase, respecting max_tools limit."""
        tool_phase = PHASES.get(phase)
        if not tool_phase:
            # Fallback to skill_create (safe default)
            tool_phase = PHASES["skill_create"]

        tools = tool_phase.tools[: self._max_tools]
        return tools

    def get_phase_info(self, phase: str) -> ToolPhase | None:
        """Get phase metadata."""
        return PHASES.get(phase)

    def list_phases(self) -> list[str]:
        """List all available phases."""
        return list(PHASES.keys())

    def get_compressed_schemas(self, phase: str) -> list[dict]:
        """Get compressed tool schemas (name + short description only).

        Used for weak models that struggle with large tool schemas.
        """
        tools = self.get_tools(phase)
        schemas = []
        for tool in tools:
            schemas.append(
                {
                    "name": tool.name,
                    "description": (tool.description or "")[:100],
                }
            )
        return schemas

    def get_full_schemas(self, phase: str) -> list[dict]:
        """Get full tool schemas with parameter details."""
        tools = self.get_tools(phase)
        schemas = []
        for tool in tools:
            schema = {
                "name": tool.name,
                "description": tool.description or "",
            }
            if hasattr(tool, "args_schema") and tool.args_schema:
                schema["parameters"] = tool.args_schema.model_json_schema()
            schemas.append(schema)
        return schemas

    def estimate_tokens(self, phase: str, compressed: bool = False) -> int:
        """Estimate token cost of tool schemas for a phase."""
        import json

        if compressed:
            schemas = self.get_compressed_schemas(phase)
        else:
            schemas = self.get_full_schemas(phase)
        text = json.dumps(schemas)
        return max(1, len(text) // 4)
