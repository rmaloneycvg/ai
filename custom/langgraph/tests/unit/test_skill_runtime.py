"""Tests for the skill runtime — workflow compilation and execution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.runtime.loader import ArtifactLoader, FailureRecovery, LoadedSkill, WorkflowStep
from src.runtime.skill_runtime import SkillExecutionStatus, SkillRuntime


@pytest.fixture
def simple_skill():
    """A minimal skill for testing graph compilation."""
    return LoadedSkill(
        name="test-simple",
        description="A simple test skill",
        role_tone="Act as a test engineer.",
        environment_scope="write+validate",
        workflow_steps=[
            WorkflowStep(number=1, name="Gather Context", description="Read relevant files."),
            WorkflowStep(number=2, name="Implement", description="Write the code."),
            WorkflowStep(number=3, name="Verify", description="Run tests."),
        ],
        failure_recovery=FailureRecovery(max_retries=2, steps=["Fix error", "Re-verify"]),
        guardrails=["NEVER skip tests", "NEVER modify unrelated files"],
    )


@pytest.fixture
def skill_with_approval():
    """A skill with an approval gate."""
    return LoadedSkill(
        name="test-approval",
        description="A skill that requires approval",
        role_tone="Be careful.",
        environment_scope="write+validate",
        workflow_steps=[
            WorkflowStep(number=1, name="Generate Spec", description="Create the spec."),
            WorkflowStep(
                number=2,
                name="Await Approval",
                description="Wait for user to confirm.",
                is_approval_gate=True,
            ),
            WorkflowStep(number=3, name="Implement", description="Write code."),
        ],
        failure_recovery=FailureRecovery(max_retries=3),
        guardrails=["NEVER proceed without approval"],
    )


@pytest.fixture
def fixtures_loader(tmp_path):
    """Loader with test skill files."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "compile-test.md").write_text("""---
name: compile-test
description: Test skill for graph compilation.
---

# Compile Test

## Role & Tone

Act as a compiler tester.

## Environment Scope

**write+validate** — Writes and validates.

## Workflow

1. **Read Input** — Understand the task.
2. **Process** — Do the work.
3. **Verify** — Check the output.
4. **Report** — Summarize results.

### Failure Recovery (max 2 retries)

1. Identify the error
2. Apply fix
3. Re-verify

## Guardrails

- NEVER skip verification
- NEVER produce invalid output
""")
    return ArtifactLoader(workspace_root=tmp_path)


class TestSkillRuntimeCompilation:
    """Tests for compiling skills into LangGraph graphs."""

    def test_compile_simple_skill(self, simple_skill):
        """Verify a simple skill compiles to a graph without errors."""
        from src.providers.base import ChatResponse, LLMProvider, ModelCapabilities

        class MockProvider(LLMProvider):
            async def chat(self, messages, **kwargs):
                return ChatResponse(content="Done", input_tokens=10, output_tokens=5, model="test")

            async def stream(self, messages, **kwargs):
                yield "Done"

            def count_tokens(self, text):
                return len(text) // 4

            def get_capabilities(self):
                return ModelCapabilities(
                    context_window=8192,
                    supports_tool_calling=False,
                    supports_structured_output=False,
                    provider_name="mock",
                    model_name="mock",
                )

        runtime = SkillRuntime(provider=MockProvider())
        graph = runtime._compile_skill_graph(simple_skill, MockProvider(), interactive=False)
        # Graph should compile without error
        assert graph is not None

    def test_step_to_node_name(self, simple_skill):
        """Verify step names are converted to valid node names."""
        runtime = SkillRuntime()

        step = WorkflowStep(number=1, name="Gather Context", description="...")
        assert runtime._step_to_node_name(step) == "step_1_gather_context"

        step = WorkflowStep(number=3, name="Await Approval", description="...")
        assert runtime._step_to_node_name(step) == "step_3_await_approval"

        step = WorkflowStep(number=5, name="Clean Up", description="...")
        assert runtime._step_to_node_name(step) == "step_5_clean_up"

    def test_is_verify_step(self):
        """Verify detection of verification steps."""
        runtime = SkillRuntime()

        assert runtime._is_verify_step(WorkflowStep(1, "Verify", "Run tests"))
        assert runtime._is_verify_step(WorkflowStep(1, "Validate Output", "Check"))
        assert runtime._is_verify_step(WorkflowStep(1, "Check Results", "Verify"))
        assert not runtime._is_verify_step(WorkflowStep(1, "Implement", "Write code"))
        assert not runtime._is_verify_step(WorkflowStep(1, "Gather Context", "Read"))

    def test_find_fix_step(self, simple_skill):
        """Verify the fix step is correctly identified for retry routing."""
        runtime = SkillRuntime()
        step_names = [
            runtime._step_to_node_name(s) for s in simple_skill.workflow_steps
        ]

        fix_step = runtime._find_fix_step(simple_skill, step_names)
        # Should find "Implement" (step before "Verify")
        assert "implement" in fix_step

    def test_find_fix_step_no_verify(self):
        """When no verify step exists, falls back to first step."""
        runtime = SkillRuntime()
        skill = LoadedSkill(
            name="no-verify",
            description="...",
            workflow_steps=[
                WorkflowStep(1, "Do Thing", "..."),
                WorkflowStep(2, "Done", "..."),
            ],
        )
        step_names = [runtime._step_to_node_name(s) for s in skill.workflow_steps]
        fix_step = runtime._find_fix_step(skill, step_names)
        assert fix_step == step_names[0]


class TestSkillPromptConstruction:
    """Tests for building step-specific prompts."""

    def test_build_step_prompt_includes_role(self, simple_skill):
        """Step prompt includes the skill's role."""
        runtime = SkillRuntime()
        step = simple_skill.workflow_steps[0]
        prompt = runtime._build_step_prompt(step, simple_skill, {})
        assert "test engineer" in prompt

    def test_build_step_prompt_includes_step_info(self, simple_skill):
        """Step prompt includes the current step's name and description."""
        runtime = SkillRuntime()
        step = simple_skill.workflow_steps[1]  # Implement
        prompt = runtime._build_step_prompt(step, simple_skill, {})
        assert "Implement" in prompt
        assert "Write the code" in prompt

    def test_build_step_prompt_includes_guardrails(self, simple_skill):
        """Step prompt includes guardrails."""
        runtime = SkillRuntime()
        step = simple_skill.workflow_steps[0]
        prompt = runtime._build_step_prompt(step, simple_skill, {})
        assert "NEVER skip tests" in prompt

    def test_build_step_prompt_includes_previous_results(self, simple_skill):
        """Step prompt includes context from completed steps."""
        runtime = SkillRuntime()
        step = simple_skill.workflow_steps[1]
        previous = {1: "Found 3 files to modify"}
        prompt = runtime._build_step_prompt(step, simple_skill, previous)
        assert "Found 3 files" in prompt

    def test_build_step_prompt_truncates_long_results(self, simple_skill):
        """Long previous results are truncated."""
        runtime = SkillRuntime()
        step = simple_skill.workflow_steps[1]
        previous = {1: "x" * 500}
        prompt = runtime._build_step_prompt(step, simple_skill, previous)
        assert "..." in prompt
        assert len(prompt) < 1000


class TestSkillRuntimeExecution:
    """Tests for executing skills with a mock provider."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock LLM provider."""
        from src.providers.base import ChatResponse, LLMProvider, ModelCapabilities

        class MockProvider(LLMProvider):
            def __init__(self):
                self.call_count = 0

            async def chat(self, messages, **kwargs):
                self.call_count += 1
                return ChatResponse(
                    content=f"Step completed (call {self.call_count})",
                    input_tokens=50,
                    output_tokens=20,
                    model="mock",
                )

            async def stream(self, messages, **kwargs):
                yield "Done"

            def count_tokens(self, text):
                return len(text) // 4

            def get_capabilities(self):
                return ModelCapabilities(
                    context_window=8192,
                    supports_tool_calling=False,
                    supports_structured_output=False,
                    provider_name="mock",
                    model_name="mock",
                )

        return MockProvider()

    @pytest.mark.asyncio
    async def test_execute_simple_skill(self, mock_provider, fixtures_loader):
        """Execute a skill end-to-end with a mock provider."""
        runtime = SkillRuntime(
            loader=fixtures_loader,
            provider=mock_provider,
        )

        result = await runtime.execute(
            skill_name="compile-test",
            task="Compile and validate the output",
            interactive=False,
        )

        assert result.success
        assert result.status == SkillExecutionStatus.SUCCESS
        assert result.total_steps == 4
        assert len(result.messages) > 0
        # Mock provider should have been called for each non-verify step
        assert mock_provider.call_count >= 3

    @pytest.mark.asyncio
    async def test_execute_skill_non_interactive_skips_approval(
        self, mock_provider
    ):
        """Non-interactive mode auto-approves at gates."""
        skill = LoadedSkill(
            name="approval-test",
            description="Test approval",
            workflow_steps=[
                WorkflowStep(1, "Plan", "Make a plan."),
                WorkflowStep(2, "Await Approval", "Get approval.", is_approval_gate=True),
                WorkflowStep(3, "Execute", "Do the work."),
            ],
            failure_recovery=FailureRecovery(max_retries=1),
        )

        runtime = SkillRuntime(provider=mock_provider)
        graph = runtime._compile_skill_graph(skill, mock_provider, interactive=False)

        # Run through the graph
        initial_state: dict = {
            "messages": [],
            "skill_name": "approval-test",
            "task_description": "Test task",
            "current_step": 0,
            "total_steps": 3,
            "step_results": {},
            "attempt_count": 0,
            "max_attempts": 1,
            "strategies_tried": [],
            "awaiting_approval": False,
            "approval_granted": False,
            "status": "running",
            "error": "",
        }

        result = await graph.ainvoke(initial_state, config={"recursion_limit": 20})
        assert result["status"] == "success"
        # Approval step should be auto-approved
        assert result["step_results"].get(2) == "Auto-approved"

    @pytest.mark.asyncio
    async def test_execute_from_real_workspace(self, mock_provider):
        """Test loading and executing a real skill from the workspace."""
        loader = ArtifactLoader()
        skills = loader.list_skills()

        if "general-debug" not in skills:
            pytest.skip("Real workspace not available")

        runtime = SkillRuntime(loader=loader, provider=mock_provider)
        result = await runtime.execute(
            skill_name="general-debug",
            task="The /api/users endpoint returns 500",
            interactive=False,
        )

        # Should complete without crashing
        assert result.status in (
            SkillExecutionStatus.SUCCESS,
            SkillExecutionStatus.FAILED,
        )
        assert result.total_steps >= 5  # general-debug has 8 steps
        assert len(result.messages) > 0
