"""Tool builder sub-agent — scaffolds Python @tool implementations."""

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

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output" / "tools"

TOOL_TEMPLATE = '''"""{{module_doc}}"""

from __future__ import annotations

import json

from langchain_core.tools import tool


@tool
def {func_name}({params}) -> str:
    """{docstring}

    Args:
{args_doc}
    """
    try:
        # TODO: Implement tool logic
        result = {{"status": "not_implemented", "tool": "{func_name}"}}
        return json.dumps(result)
    except Exception as e:
        return json.dumps({{"error": str(e)}})
'''


def analyze_requirements_node(state: SubAgentState) -> dict:
    """Analyze tool requirements from task description."""
    pipeline_input = state.get("pipeline_input")
    description = pipeline_input.input.description if pipeline_input else ""

    # Extract tool characteristics
    desc_lower = description.lower()
    needs_http = any(w in desc_lower for w in ["api", "http", "rest", "graphql", "webhook"])
    needs_db = any(w in desc_lower for w in ["database", "sql", "query", "postgres"])
    needs_shell = any(w in desc_lower for w in ["command", "shell", "subprocess", "cli"])

    imports = ["json"]
    if needs_http:
        imports.append("httpx")
    if needs_shell:
        imports.append("subprocess")

    context = f"Imports needed: {', '.join(imports)}. HTTP: {needs_http}, DB: {needs_db}, Shell: {needs_shell}"
    return {
        "messages": [SystemMessage(content=context)],
        "draft_content": json.dumps({"imports": imports}),
    }


def scaffold_tool_node(state: SubAgentState) -> dict:
    """Generate the tool implementation scaffold."""

    pipeline_input = state.get("pipeline_input")
    description = pipeline_input.input.description if pipeline_input else ""

    func_name = _derive_func_name(description)
    func_name.replace("_", "-")

    # Generate the tool file content
    content = f'''"""{description}"""

from __future__ import annotations

import json
import os

from langchain_core.tools import tool


@tool
def {func_name}(input_data: str = "") -> str:
    """{description}

    Args:
        input_data: Input parameters as JSON string.
    """
    try:
        # TODO: Implement tool logic
        params = json.loads(input_data) if input_data else {{}}
        result = {{"status": "not_implemented", "tool": "{func_name}", "params": params}}
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({{"error": str(e)}})
'''

    return {"draft_content": content}


def validate_syntax_node(state: SubAgentState) -> dict:
    """Validate the generated Python is syntactically correct."""
    content = state.get("draft_content", "")
    errors: list[str] = []

    try:
        compile(content, "<tool>", "exec")
    except SyntaxError as e:
        errors.append(f"Syntax error: {e}")

    # Check for required elements
    if "@tool" not in content:
        errors.append("Missing @tool decorator")
    if "def " not in content:
        errors.append("Missing function definition")
    if '"""' not in content:
        errors.append("Missing docstring")

    return {"validation_errors": errors}


def write_output_node(state: SubAgentState) -> dict:
    """Write the tool file and produce PipelineOutput."""
    content = state.get("draft_content", "")
    errors = state.get("validation_errors", [])
    pipeline_input = state.get("pipeline_input")
    task_type = pipeline_input.task_type if pipeline_input else TaskType.TOOL_BUILD
    description = pipeline_input.input.description if pipeline_input else ""

    if errors:
        return {
            "pipeline_output": PipelineOutput(
                task_type=task_type,
                output=PipelineOutputData(
                    status=OutputStatus.FAILED,
                    decisions_made=[f"Validation failed: {e}" for e in errors],
                    error_count=len(errors),
                    retry_context=RetryContext(
                        attempts_made=1, max_attempts=3, should_escalate=True
                    ),
                ),
            )
        }

    func_name = _derive_func_name(description)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{func_name}.py"
    output_path.write_text(content)

    return {
        "pipeline_output": PipelineOutput(
            task_type=task_type,
            output=PipelineOutputData(
                status=OutputStatus.SUCCESS,
                files_created=[str(output_path)],
                decisions_made=[
                    f"Created tool scaffold: {func_name}",
                    "Used @tool decorator pattern",
                    "JSON input/output for consistent interface",
                    "TODO markers for implementation logic",
                ],
                retry_context=RetryContext(attempts_made=1, max_attempts=3),
            ),
        )
    }


def build_tool_builder_graph() -> StateGraph:
    """Build the tool builder subgraph."""
    builder = StateGraph(SubAgentState)

    builder.add_node("analyze_requirements", analyze_requirements_node)
    builder.add_node("scaffold_tool", scaffold_tool_node)
    builder.add_node("validate_syntax", validate_syntax_node)
    builder.add_node("write_output", write_output_node)

    builder.set_entry_point("analyze_requirements")
    builder.add_edge("analyze_requirements", "scaffold_tool")
    builder.add_edge("scaffold_tool", "validate_syntax")
    builder.add_edge("validate_syntax", "write_output")
    builder.add_edge("write_output", END)

    return builder


def _derive_func_name(description: str) -> str:
    words = description.lower().split()[:4]
    clean = [w for w in words if w.isalnum()]
    return "_".join(clean) or "new_tool"
