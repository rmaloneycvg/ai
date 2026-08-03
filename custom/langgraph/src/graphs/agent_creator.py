"""Agent creator sub-agent — generates Kiro-format agent JSON configs."""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import SystemMessage
from langgraph.graph import END, StateGraph

from src.graphs.state import SubAgentState
from src.models.pipeline import (
    OutputStatus,
    PipelineOutput,
    PipelineOutputData,
    RetryContext,
    TaskType,
)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output" / "agents"

TOOL_PRESETS = {
    "read-only": {
        "tools": ["read", "glob", "grep", "code"],
        "allowedTools": ["read", "glob", "grep", "code"],
    },
    "development": {
        "tools": ["read", "write", "shell", "glob", "grep", "code", "@git", "@io"],
        "allowedTools": ["read", "glob", "grep", "code", "@git/git_status", "@io/read_json"],
    },
    "infrastructure": {
        "tools": ["read", "write", "shell", "glob", "grep", "code", "@git"],
        "allowedTools": ["read", "glob", "grep", "code"],
    },
}


def load_schema_node(state: SubAgentState) -> dict:
    """Load agent schema and existing agent metadata."""
    from src.resources.resolver import ResourceResolver

    ResourceResolver()

    # Check for existing agents
    agents_dir = Path(__file__).parent.parent.parent.parent / "agents"
    existing = []
    if agents_dir.exists():
        existing = [f.stem for f in agents_dir.glob("*.json")]

    context = f"Existing agents: {', '.join(existing[:10]) if existing else 'none'}"
    return {"messages": [SystemMessage(content=context)]}


def determine_scope_node(state: SubAgentState) -> dict:
    """Determine tool scope from task requirements."""
    pipeline_input = state.get("pipeline_input")
    description = pipeline_input.input.description if pipeline_input else ""
    desc_lower = description.lower()

    # Classify agent type from description
    if any(w in desc_lower for w in ["infra", "terraform", "docker", "k8s", "deploy"]):
        preset = "infrastructure"
    elif any(w in desc_lower for w in ["review", "analysis", "audit", "score"]):
        preset = "read-only"
    else:
        preset = "development"

    return {"tool_preset": preset}


def draft_config_node(state: SubAgentState) -> dict:
    """Generate the agent JSON config."""
    pipeline_input = state.get("pipeline_input")
    description = pipeline_input.input.description if pipeline_input else ""

    # Read preset from dedicated state field
    preset = state.get("tool_preset", "development") or "development"
    tool_config = TOOL_PRESETS[preset]

    # Derive agent name
    name = _derive_agent_name(description)

    config = {
        "name": name,
        "description": description,
        "prompt": f"You are a {name.replace('-', ' ')} agent. {description}",
        "mcpServers": {},
        "tools": tool_config["tools"],
        "allowedTools": tool_config["allowedTools"],
        "toolsSettings": {
            "shell": {"allowedCommands": ["git *", "ls *", "cat *", "find *", "grep *"]}
        }
        if "shell" in tool_config["tools"]
        else {},
        "resources": [],
        "hooks": {
            "agentSpawn": [
                {"command": "git status --porcelain", "timeout_ms": 5000},
                {"command": "git branch --show-current", "timeout_ms": 3000},
            ]
        },
    }

    return {"draft_content": json.dumps(config, indent=2)}


def validate_config_node(state: SubAgentState) -> dict:
    """Validate the agent config JSON."""
    content = state.get("draft_content", "")
    errors: list[str] = []

    try:
        config = json.loads(content)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return {"validation_errors": errors}

    # Required fields
    for field in ["name", "description", "prompt", "tools", "allowedTools"]:
        if field not in config:
            errors.append(f"Missing required field: {field}")

    # allowedTools must be subset of tools
    if "tools" in config and "allowedTools" in config:
        allowed = set(config["allowedTools"])
        available = set(config["tools"])
        # Account for prefixed tools like @git/git_status being under @git
        for tool in allowed:
            base = tool.split("/")[0]
            if tool not in available and base not in available:
                errors.append(f"allowedTool '{tool}' not in tools list")

    return {"validation_errors": errors}


def write_output_node(state: SubAgentState) -> dict:
    """Write the agent config and produce PipelineOutput."""
    content = state.get("draft_content", "")
    errors = state.get("validation_errors", [])
    pipeline_input = state.get("pipeline_input")
    task_type = pipeline_input.task_type if pipeline_input else TaskType.AGENT_CREATE

    if errors:
        return {
            "pipeline_output": PipelineOutput(
                task_type=task_type,
                output=PipelineOutputData(
                    status=OutputStatus.PARTIAL,
                    decisions_made=[f"Validation error: {e}" for e in errors],
                    error_count=len(errors),
                    retry_context=RetryContext(attempts_made=1, max_attempts=3),
                ),
            )
        }

    config = json.loads(content)
    name = config.get("name", "new-agent")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{name}.json"
    output_path.write_text(content)

    return {
        "pipeline_output": PipelineOutput(
            task_type=task_type,
            output=PipelineOutputData(
                status=OutputStatus.SUCCESS,
                files_created=[str(output_path)],
                decisions_made=[
                    f"Created agent '{name}'",
                    f"Tool preset: {state.get('tool_preset', 'development')}",
                    f"Tools: {', '.join(config.get('tools', []))}",
                ],
                retry_context=RetryContext(attempts_made=1, max_attempts=3),
            ),
        )
    }


def build_agent_creator_graph() -> StateGraph:
    """Build the agent creator subgraph."""
    builder = StateGraph(SubAgentState)

    builder.add_node("load_schema", load_schema_node)
    builder.add_node("determine_scope", determine_scope_node)
    builder.add_node("draft_config", draft_config_node)
    builder.add_node("validate_config", validate_config_node)
    builder.add_node("write_output", write_output_node)

    builder.set_entry_point("load_schema")
    builder.add_edge("load_schema", "determine_scope")
    builder.add_edge("determine_scope", "draft_config")
    builder.add_edge("draft_config", "validate_config")
    builder.add_edge("validate_config", "write_output")
    builder.add_edge("write_output", END)

    return builder


def _derive_agent_name(description: str) -> str:
    words = description.lower().split()[:3]
    clean = [w for w in words if w.isalnum()]
    return "-".join(clean) or "new-agent"
