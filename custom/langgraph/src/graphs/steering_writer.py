"""Steering writer sub-agent — generates steering documentation."""

from __future__ import annotations

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
from src.resources.resolver import ResourceResolver

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output" / "steering"

STEERING_TEMPLATE = """# {title}

## Why This Exists

{why}

## {main_section_title}

{main_content}

## Rules

{rules}

## Anti-Patterns

{anti_patterns}
"""


def load_context_node(state: SubAgentState) -> dict:
    """Load existing steering structure for reference."""
    resolver = ResourceResolver()
    available = resolver.list_available()
    structure = {}
    for path in available:
        parts = path.split("/")
        if len(parts) >= 2:
            category = parts[0]
            structure.setdefault(category, []).append(parts[-1])

    context = "Steering structure: " + ", ".join(
        f"{k} ({len(v)} docs)" for k, v in structure.items()
    )
    return {"messages": [SystemMessage(content=context)]}


def classify_category_node(state: SubAgentState) -> dict:
    """Determine which steering category this doc belongs to."""
    pipeline_input = state.get("pipeline_input")
    description = pipeline_input.input.description if pipeline_input else ""
    desc_lower = description.lower()

    if any(w in desc_lower for w in ["convention", "style", "naming", "format"]):
        category = "conventions"
    elif any(w in desc_lower for w in ["security", "auth", "cors", "validation"]):
        category = "security"
    elif any(w in desc_lower for w in ["tilt", "docker", "k8s", "pipeline", "orchestrat"]):
        category = "orchestration"
    elif any(w in desc_lower for w in ["react", "node", "next", "csharp", "stack"]):
        category = "preferences"
    else:
        category = "conventions"

    return {"draft_content": category}


def draft_steering_node(state: SubAgentState) -> dict:
    """Generate the steering doc content."""
    pipeline_input = state.get("pipeline_input")
    description = pipeline_input.input.description if pipeline_input else ""
    category = state.get("draft_content", "conventions")

    title = _derive_title(description)
    content = STEERING_TEMPLATE.format(
        title=title,
        why=f"This document defines standards for {description.lower()}. "
        "Without clear conventions, inconsistencies accumulate across the codebase.",
        main_section_title="Conventions",
        main_content="TODO: Define specific conventions based on team discussion.",
        rules="- Follow the patterns defined above prescriptively\n"
        "- Document exceptions with justification\n"
        "- Review annually for staleness",
        anti_patterns="- ❌ Ignoring these conventions without documented exception\n"
        "- ❌ Duplicating guidance that belongs in a different steering doc\n"
        "- ❌ Adding rules without enforcement mechanism",
    )

    return {"draft_content": f"{category}|||{content}"}


def write_output_node(state: SubAgentState) -> dict:
    """Write the steering doc and produce PipelineOutput."""
    raw = state.get("draft_content", "")
    pipeline_input = state.get("pipeline_input")
    task_type = pipeline_input.task_type if pipeline_input else TaskType.STEERING_WRITE
    description = pipeline_input.input.description if pipeline_input else ""

    parts = raw.split("|||", 1)
    category = parts[0] if len(parts) > 1 else "conventions"
    content = parts[1] if len(parts) > 1 else raw

    # Write output
    output_subdir = OUTPUT_DIR / category
    output_subdir.mkdir(parents=True, exist_ok=True)
    filename = _derive_filename(description)
    output_path = output_subdir / filename
    output_path.write_text(content)

    return {
        "pipeline_output": PipelineOutput(
            task_type=task_type,
            output=PipelineOutputData(
                status=OutputStatus.SUCCESS,
                files_created=[str(output_path)],
                decisions_made=[
                    f"Category: {category}",
                    f"Created steering doc: {filename}",
                    "Template structure applied (Why, Conventions, Rules, Anti-Patterns)",
                ],
                retry_context=RetryContext(attempts_made=1, max_attempts=3),
            ),
        )
    }


def build_steering_writer_graph() -> StateGraph:
    """Build the steering writer subgraph."""
    builder = StateGraph(SubAgentState)

    builder.add_node("load_context", load_context_node)
    builder.add_node("classify_category", classify_category_node)
    builder.add_node("draft_steering", draft_steering_node)
    builder.add_node("write_output", write_output_node)

    builder.set_entry_point("load_context")
    builder.add_edge("load_context", "classify_category")
    builder.add_edge("classify_category", "draft_steering")
    builder.add_edge("draft_steering", "write_output")
    builder.add_edge("write_output", END)

    return builder


def _derive_title(description: str) -> str:
    return description.strip().rstrip(".").title()[:80]


def _derive_filename(description: str) -> str:
    words = description.lower().split()[:4]
    clean = [w for w in words if w.isalnum()]
    return "-".join(clean) + ".md" if clean else "new-steering.md"
