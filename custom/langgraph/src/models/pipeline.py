"""Pipeline I/O Pydantic models — inter-agent communication contracts.

Source of truth: schemas/pipeline-io.schema.json
These models validate all data flowing between supervisor and sub-agents.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    SKILL_CREATE = "skill_create"
    AGENT_CREATE = "agent_create"
    STEERING_WRITE = "steering_write"
    TOOL_BUILD = "tool_build"
    MODEL_PROFILE = "model_profile"
    RAG_MANAGE = "rag_manage"


class UpstreamDecision(BaseModel):
    """Decisions from an earlier pipeline stage."""

    from_agent: str
    decisions: list[str]


class PipelineInputData(BaseModel):
    """The input payload for a pipeline task."""

    description: str = Field(description="What needs to be done")
    target_files: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    upstream_decisions: list[UpstreamDecision] = Field(default_factory=list)


class PipelineInput(BaseModel):
    """Input contract for sub-agents."""

    task_type: TaskType
    input: PipelineInputData

    def to_prompt_fragment(self) -> str:
        """Compact representation for injection into prompts."""
        lines = [
            f"Task: {self.task_type.value}",
            f"Description: {self.input.description}",
        ]
        if self.input.target_files:
            lines.append(f"Target files: {', '.join(self.input.target_files)}")
        if self.input.constraints:
            lines.append("Constraints:")
            for c in self.input.constraints:
                lines.append(f"  - {c}")
        if self.input.upstream_decisions:
            lines.append("Upstream decisions:")
            for ud in self.input.upstream_decisions:
                lines.append(f"  From {ud.from_agent}:")
                for d in ud.decisions:
                    lines.append(f"    - {d}")
        return "\n".join(lines)


class PipelineError(BaseModel):
    """A single error encountered during pipeline execution."""

    type: str
    message: str
    file: str | None = None
    line: int | None = None
    attempt: int


class RetryContext(BaseModel):
    """Retry state for orchestrator decision-making."""

    attempts_made: int = 0
    max_attempts: int = 3
    strategies_tried: list[str] = Field(default_factory=list)
    should_escalate: bool = False


class OutputStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class PipelineOutputData(BaseModel):
    """The output payload from a sub-agent."""

    status: OutputStatus
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    decisions_made: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    errors: list[PipelineError] = Field(default_factory=list)
    error_count: int = 0
    retry_context: RetryContext = Field(default_factory=RetryContext)


class PipelineOutput(BaseModel):
    """Output contract from sub-agents."""

    task_type: TaskType
    output: PipelineOutputData

    def to_prompt_fragment(self) -> str:
        """Compact representation for downstream agents."""
        lines = [
            f"Task: {self.task_type.value}",
            f"Status: {self.output.status.value}",
        ]
        if self.output.files_created:
            lines.append(f"Created: {', '.join(self.output.files_created)}")
        if self.output.files_modified:
            lines.append(f"Modified: {', '.join(self.output.files_modified)}")
        if self.output.decisions_made:
            lines.append("Decisions:")
            for d in self.output.decisions_made:
                lines.append(f"  - {d}")
        if self.output.errors:
            lines.append(f"Errors ({self.output.error_count}):")
            for e in self.output.errors:
                lines.append(f"  [{e.type}] {e.message}")
        return "\n".join(lines)
