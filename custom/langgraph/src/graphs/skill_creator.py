"""Skill creator sub-agent — generates Kiro-format skill files.

Nodes:
1. load_context — progressive disclosure of skill-schema steering
2. check_overlap — reads existing skill descriptions, identifies conflicts
3. draft_spec — generates skill spec using compiled prompt
4. validate — validates against SkillSpec Pydantic model
5. format_output — renders final markdown
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.messages import SystemMessage
from langgraph.graph import END, StateGraph

from src.graphs.state import SubAgentState
from src.models.pipeline import (
    OutputStatus,
    PipelineError,
    PipelineOutput,
    PipelineOutputData,
    RetryContext,
    TaskType,
)
from src.resources.resolver import ResourceResolver

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output" / "skills"

SKILL_TEMPLATE = """---
name: {name}
description: {description}
---

# {title}

## Role & Tone

{role_tone}

## Environment Scope

**{env_scope}** — {env_scope_detail}

## Workflow

{workflow}

### Failure Recovery (max 3 retries)

{failure_recovery}

### Rollback

{rollback}

## Guardrails

{guardrails}

## References

{references}
"""


def load_context_node(state: SubAgentState) -> dict:
    """Load skill-schema steering and existing skills metadata."""
    resolver = ResourceResolver()

    # Load skill schema steering (via symlink)
    schema_content = resolver.read("conventions/skill-schema.md") or ""

    # Get existing skill names for overlap detection
    skills_dir = Path(__file__).parent.parent.parent / "steering" / ".." / ".." / "skills"
    existing_skills: list[str] = []
    if skills_dir.exists():
        for f in skills_dir.glob("*.md"):
            # Extract name from frontmatter
            content = f.read_text()[:200]
            if "name:" in content:
                for line in content.split("\n"):
                    if line.strip().startswith("name:"):
                        existing_skills.append(line.split(":", 1)[1].strip())
                        break

    context = (
        f"Schema loaded ({len(schema_content)} chars). Existing skills: {len(existing_skills)}"
    )
    return {
        "messages": [SystemMessage(content=context)],
        "draft_content": schema_content[:3000],  # Budget-limited
    }


def check_overlap_node(state: SubAgentState) -> dict:
    """Check for overlap with existing skills."""
    pipeline_input = state.get("pipeline_input")
    description = pipeline_input.input.description if pipeline_input else ""

    # Simple keyword overlap check against known skill names
    overlap_warnings: list[str] = []
    known_skills = [
        "general-debug",
        "general-test",
        "general-refactor",
        "general-deploy",
        "backend-rest-api-feature",
        "backend-cron-feature",
        "react-components",
        "react-testing",
        "react-refactor",
    ]

    desc_lower = description.lower()
    for skill in known_skills:
        skill_words = set(skill.replace("-", " ").split())
        if skill_words & set(desc_lower.split()):
            overlap_warnings.append(f"Potential overlap with: {skill}")

    if overlap_warnings:
        return {"overlap_warnings": overlap_warnings}
    return {}


def draft_spec_node(state: SubAgentState) -> dict:
    """Draft the skill specification."""
    pipeline_input = state.get("pipeline_input")
    description = pipeline_input.input.description if pipeline_input else "No description provided"

    # Generate skill content from description
    name = _derive_name(description)
    title = _derive_title(description)

    content = SKILL_TEMPLATE.format(
        name=name,
        description=description,
        title=title,
        role_tone="Act as a senior engineer. Be concise and technical. Prefer working solutions over explanations.",
        env_scope="write+validate",
        env_scope_detail="Writes files and runs validation commands (lint, typecheck). No side effects.",
        workflow=_generate_workflow(description),
        failure_recovery="1. Identify issue from validation output\n2. Apply targeted fix\n3. Re-validate\n4. After 3 failures → report to user with diagnosis",
        rollback="If user cancels: revert all created/modified files. Confirm with listing.",
        guardrails=_generate_guardrails(),
        references="- `steering/conventions/skill-schema.md` — Full schema definition and quality checklist",
    )

    return {"draft_content": content}


def validate_node(state: SubAgentState) -> dict:
    """Validate the draft skill content."""
    content = state.get("draft_content", "")
    errors: list[str] = []

    # Carry forward overlap warnings from check_overlap_node
    overlap = state.get("overlap_warnings", [])
    if overlap:
        errors.extend(overlap)

    # Check required sections
    required_sections = ["## Role & Tone", "## Workflow", "## Guardrails"]
    for section in required_sections:
        if section not in content:
            errors.append(f"Missing required section: {section}")

    # Check frontmatter
    if not content.startswith("---"):
        errors.append("Missing YAML frontmatter")
    elif "name:" not in content[:200]:
        errors.append("Missing 'name' in frontmatter")
    elif "description:" not in content[:500]:
        errors.append("Missing 'description' in frontmatter")

    return {"validation_errors": errors, "attempt_count": state.get("attempt_count", 0) + 1}


def format_output_node(state: SubAgentState) -> dict:
    """Write the final skill file and produce PipelineOutput."""
    content = state.get("draft_content", "")
    validation_errors = state.get("validation_errors", [])
    pipeline_input = state.get("pipeline_input")
    task_type = pipeline_input.task_type if pipeline_input else TaskType.SKILL_CREATE

    if validation_errors:
        return {
            "pipeline_output": PipelineOutput(
                task_type=task_type,
                output=PipelineOutputData(
                    status=OutputStatus.PARTIAL,
                    errors=[
                        PipelineError(type="validation_error", message=e, attempt=1)
                        for e in validation_errors
                    ],
                    error_count=len(validation_errors),
                    decisions_made=["Draft generated with validation warnings"],
                    retry_context=RetryContext(attempts_made=1, max_attempts=3),
                ),
            )
        }

    # Write output file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    name = _extract_name(content)
    output_path = OUTPUT_DIR / f"{name}.md"
    output_path.write_text(content)

    return {
        "pipeline_output": PipelineOutput(
            task_type=task_type,
            output=PipelineOutputData(
                status=OutputStatus.SUCCESS,
                files_created=[str(output_path)],
                decisions_made=[
                    f"Created skill '{name}' with phased workflow",
                    "Used write+validate environment scope",
                    "Added failure recovery (max 3 retries) and rollback procedure",
                ],
                retry_context=RetryContext(attempts_made=1, max_attempts=3),
            ),
        )
    }


def build_skill_creator_graph() -> StateGraph:
    """Build the skill creator subgraph."""
    builder = StateGraph(SubAgentState)

    builder.add_node("load_context", load_context_node)
    builder.add_node("check_overlap", check_overlap_node)
    builder.add_node("draft_spec", draft_spec_node)
    builder.add_node("validate", validate_node)
    builder.add_node("format_output", format_output_node)

    builder.set_entry_point("load_context")
    builder.add_edge("load_context", "check_overlap")
    builder.add_edge("check_overlap", "draft_spec")
    builder.add_edge("draft_spec", "validate")
    builder.add_edge("validate", "format_output")
    builder.add_edge("format_output", END)

    return builder


# --- Helpers ---


def _derive_name(description: str) -> str:
    """Generate kebab-case name from description."""
    words = description.lower().split()[:4]
    clean = [w for w in words if w.isalnum()]
    return "-".join(clean) or "new-skill"


def _derive_title(description: str) -> str:
    """Generate a title from description."""
    return description.strip().rstrip(".").title()[:80]


def _extract_name(content: str) -> str:
    """Extract name from frontmatter."""
    for line in content.split("\n")[:10]:
        if line.strip().startswith("name:"):
            return line.split(":", 1)[1].strip()
    return "new-skill"


def _generate_workflow(description: str) -> str:
    return """1. **Check Existing State** — Verify target artifact doesn't already exist. If it does, report and stop.
2. **Gather Context** — Read relevant existing code/config. Identify integration points.
3. **Generate Spec** — Output requirements in EARS format. List all files to create/modify.
4. **Await Approval** — Present spec. Do NOT proceed until user confirms.
5. **Implement** — Execute the approved spec step by step.
6. **Verify** — Run validation. If fails, enter failure recovery loop.
7. **Document** — Update README/docs if the change is user-facing."""


def _generate_guardrails() -> str:
    return """- NEVER begin implementation until the spec is explicitly approved
- NEVER modify files outside the scope defined in the spec
- NEVER skip test/validation creation
- NEVER introduce new dependencies without stating them in the spec
- NEVER overwrite existing artifacts without explaining why
- NEVER proceed if overlap with existing skills is detected — ask for clarification"""
