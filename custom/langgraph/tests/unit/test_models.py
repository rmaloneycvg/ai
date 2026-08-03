"""Unit tests for Pydantic pipeline models."""

import pytest
from pydantic import ValidationError

from src.models.pipeline import (
    OutputStatus,
    PipelineError,
    PipelineInput,
    PipelineInputData,
    PipelineOutput,
    PipelineOutputData,
    RetryContext,
    TaskType,
    UpstreamDecision,
)


class TestPipelineInput:
    def test_valid_input(self):
        inp = PipelineInput(
            task_type=TaskType.SKILL_CREATE,
            input=PipelineInputData(
                description="Create a debugging skill",
                target_files=["skills/"],
                constraints=["Must follow skill-schema.md"],
            ),
        )
        assert inp.task_type == TaskType.SKILL_CREATE
        assert inp.input.description == "Create a debugging skill"

    def test_minimal_input(self):
        inp = PipelineInput(
            task_type=TaskType.AGENT_CREATE,
            input=PipelineInputData(description="Create a dev agent"),
        )
        assert inp.input.target_files == []
        assert inp.input.constraints == []

    def test_to_prompt_fragment_compact(self):
        inp = PipelineInput(
            task_type=TaskType.SKILL_CREATE,
            input=PipelineInputData(description="Create a debugging skill"),
        )
        fragment = inp.to_prompt_fragment()
        assert "skill_create" in fragment
        assert "debugging skill" in fragment

    def test_roundtrip_serialization(self):
        inp = PipelineInput(
            task_type=TaskType.TOOL_BUILD,
            input=PipelineInputData(
                description="Build a git tool",
                constraints=["Must use subprocess"],
                upstream_decisions=[
                    UpstreamDecision(
                        from_agent="supervisor",
                        decisions=["Use git CLI", "Read-only operations"],
                    )
                ],
            ),
        )
        json_str = inp.model_dump_json()
        restored = PipelineInput.model_validate_json(json_str)
        assert restored == inp


class TestPipelineOutput:
    def test_success_output(self):
        out = PipelineOutput(
            task_type=TaskType.SKILL_CREATE,
            output=PipelineOutputData(
                status=OutputStatus.SUCCESS,
                files_created=["skills/debug-python.md"],
                decisions_made=["Used phased workflow pattern"],
                retry_context=RetryContext(attempts_made=1, max_attempts=3),
            ),
        )
        assert out.output.status == OutputStatus.SUCCESS
        assert out.output.error_count == 0

    def test_failed_output_with_errors(self):
        out = PipelineOutput(
            task_type=TaskType.AGENT_CREATE,
            output=PipelineOutputData(
                status=OutputStatus.FAILED,
                errors=[
                    PipelineError(
                        type="validation_error",
                        message="Invalid JSON syntax",
                        file="agents/test.json",
                        attempt=2,
                    )
                ],
                error_count=1,
                retry_context=RetryContext(
                    attempts_made=3,
                    max_attempts=3,
                    strategies_tried=["fix syntax", "regenerate", "simplify"],
                    should_escalate=True,
                ),
            ),
        )
        assert out.output.retry_context.should_escalate is True

    def test_to_prompt_fragment(self):
        out = PipelineOutput(
            task_type=TaskType.SKILL_CREATE,
            output=PipelineOutputData(
                status=OutputStatus.SUCCESS,
                files_created=["skills/test.md"],
                decisions_made=["Decision 1"],
                retry_context=RetryContext(),
            ),
        )
        fragment = out.to_prompt_fragment()
        assert "success" in fragment
        assert "skills/test.md" in fragment

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            PipelineOutput(
                task_type=TaskType.SKILL_CREATE,
                output=PipelineOutputData(
                    status="invalid_status",
                    retry_context=RetryContext(),
                ),
            )
