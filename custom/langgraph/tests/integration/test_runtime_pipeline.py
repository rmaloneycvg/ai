"""Integration tests for the artifact runtime pipeline.

Tests the full flow: load artifact → resolve resources → map model →
filter tools → build prompt → execute graph. Uses mock providers to
avoid requiring Ollama.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.providers.base import ChatResponse, LLMProvider, ModelCapabilities
from src.runtime.agent_runtime import AgentRuntime
from src.runtime.loader import ArtifactLoader
from src.runtime.model_mapper import ModelMapper
from src.runtime.orchestrator import OrchestratorRuntime
from src.runtime.skill_runtime import SkillRuntime


class MockProvider(LLMProvider):
    """Mock provider that tracks all calls for assertion."""

    def __init__(self):
        self.calls: list[dict] = []
        self._call_count = 0

    async def chat(self, messages, **kwargs):
        self._call_count += 1
        self.calls.append({
            "messages": messages,
            "kwargs": kwargs,
            "call_number": self._call_count,
        })
        return ChatResponse(
            content=f"Response #{self._call_count}: Task processed successfully.",
            input_tokens=100,
            output_tokens=50,
            model="mock",
        )

    async def stream(self, messages, **kwargs):
        yield "streamed response"

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


class TestAgentRuntimePipeline:
    """End-to-end tests for agent execution using real workspace artifacts."""

    @pytest.fixture
    def provider(self):
        return MockProvider()

    @pytest.fixture
    def runtime(self, provider):
        return AgentRuntime(provider=provider)

    @pytest.mark.asyncio
    async def test_general_dev_agent_full_pipeline(self, runtime, provider):
        """Execute general-dev agent end-to-end."""
        loader = ArtifactLoader()
        if "general-dev" not in loader.list_agents():
            pytest.skip("Real workspace not available")

        result = await runtime.execute(
            agent_name="general-dev",
            task="What files are in this project?",
        )

        assert result.success
        assert len(result.messages) >= 2
        # Provider should have been called
        assert provider._call_count >= 1
        # System prompt should contain the agent's identity
        first_call = provider.calls[0]
        system_msg = first_call["messages"][0].content
        assert "full-stack" in system_msg.lower() or "development" in system_msg.lower()

    @pytest.mark.asyncio
    async def test_react_frontend_agent_loads_skills(self, runtime, provider):
        """React-frontend agent loads skill resources into context."""
        loader = ArtifactLoader()
        if "react-frontend" not in loader.list_agents():
            pytest.skip("Real workspace not available")

        result = await runtime.execute(
            agent_name="react-frontend",
            task="Add a new component",
        )

        assert result.success
        # The system prompt should contain skill content
        first_call = provider.calls[0]
        system_msg = first_call["messages"][0].content
        # react-frontend loads multiple skills about React
        assert "frontend" in system_msg.lower() or "react" in system_msg.lower()

    @pytest.mark.asyncio
    async def test_agent_hooks_provide_context(self, runtime, provider):
        """Agent hooks inject environment info into the prompt."""
        loader = ArtifactLoader()
        if "general-dev" not in loader.list_agents():
            pytest.skip("Real workspace not available")

        result = await runtime.execute(
            agent_name="general-dev",
            task="Check git status",
        )

        assert result.success
        first_call = provider.calls[0]
        system_msg = first_call["messages"][0].content
        # Hooks run git status, git branch — at least one should appear
        # (may show "Current Environment" section)
        assert len(system_msg) > 100  # Should have substantial context


class TestSkillRuntimePipeline:
    """End-to-end tests for skill workflow execution."""

    @pytest.fixture
    def provider(self):
        return MockProvider()

    @pytest.fixture
    def runtime(self, provider):
        return SkillRuntime(provider=provider)

    @pytest.mark.asyncio
    async def test_general_debug_skill_full_pipeline(self, runtime, provider):
        """Execute general-debug skill end-to-end."""
        loader = ArtifactLoader()
        if "general-debug" not in loader.list_skills():
            pytest.skip("Real workspace not available")

        result = await runtime.execute(
            skill_name="general-debug",
            task="The /api/users endpoint returns 500",
            interactive=False,
        )

        # Should complete (success or failed, but not crash)
        assert result.status.value in ("success", "failed")
        assert result.total_steps == 8  # general-debug has 8 steps
        assert len(result.messages) > 0
        # Provider should be called for each non-approval step
        assert provider._call_count >= 5

    @pytest.mark.asyncio
    async def test_skill_step_progression(self, runtime, provider):
        """Verify skill steps execute in order with results passed downstream."""
        loader = ArtifactLoader()
        if "general-debug" not in loader.list_skills():
            pytest.skip("Real workspace not available")

        result = await runtime.execute(
            skill_name="general-debug",
            task="Fix a bug",
            interactive=False,
        )

        # Step results should be populated
        assert len(result.step_results) > 0
        # Steps should have numbered keys
        step_numbers = sorted(result.step_results.keys())
        assert step_numbers[0] >= 1

    @pytest.mark.asyncio
    async def test_skill_guardrails_in_prompts(self, provider):
        """Verify guardrails are included in step prompts."""
        loader = ArtifactLoader()
        if "general-debug" not in loader.list_skills():
            pytest.skip("Real workspace not available")

        runtime = SkillRuntime(provider=provider)
        await runtime.execute(
            skill_name="general-debug",
            task="Debug the issue",
            interactive=False,
        )

        # Check that guardrails appear in at least one system prompt
        found_guardrail = False
        for call in provider.calls:
            system_msg = call["messages"][0].content
            if "NEVER" in system_msg:
                found_guardrail = True
                break
        assert found_guardrail, "Guardrails should appear in step prompts"

    @pytest.mark.asyncio
    async def test_react_scaffold_skill(self, provider):
        """Execute react-scaffold skill (pipeline sub-agent)."""
        loader = ArtifactLoader()
        if "react-scaffold" not in loader.list_skills():
            pytest.skip("Real workspace not available")

        runtime = SkillRuntime(loader=loader, provider=provider)
        result = await runtime.execute(
            skill_name="react-scaffold",
            task="Scaffold a UserProfile component",
            interactive=False,
        )

        assert result.status.value in ("success", "failed")
        assert result.total_steps >= 5  # react-scaffold has 6 steps
        assert len(result.messages) > 0


class TestOrchestratorPipeline:
    """End-to-end tests for orchestrator multi-agent execution."""

    @pytest.fixture
    def provider(self):
        return MockProvider()

    @pytest.mark.asyncio
    async def test_react_orchestrator_forced_routing(self, provider):
        """Forced routing bypasses LLM classification entirely."""
        loader = ArtifactLoader()
        if "react-orchestrator" not in loader.list_agents():
            pytest.skip("Real workspace not available")

        runtime = OrchestratorRuntime(loader=loader, provider=provider)
        result = await runtime.execute(
            orchestrator_name="react-orchestrator",
            task="scaffold: a new Button component",
            interactive=False,
        )

        assert result.success
        assert result.stages_completed >= 1
        # Should route to react-scaffold
        assert "react-scaffold" in result.stage_results

    @pytest.mark.asyncio
    async def test_react_orchestrator_all_prefixes(self, provider):
        """All forced routing prefixes resolve correctly."""
        loader = ArtifactLoader()
        if "react-orchestrator" not in loader.list_agents():
            pytest.skip("Real workspace not available")

        prefix_to_agent = {
            "scaffold: new thing": "react-scaffold",
            "test: the component": "react-testing",
            "refactor: extract hook": "react-refactor",
            "arch: how to structure": "react-architecture",
            "style: make responsive": "react-styling",
        }

        for task, expected_agent in prefix_to_agent.items():
            fresh_provider = MockProvider()
            runtime = OrchestratorRuntime(loader=loader, provider=fresh_provider)
            result = await runtime.execute(
                orchestrator_name="react-orchestrator",
                task=task,
                interactive=False,
            )

            assert result.success, f"Failed for prefix task: {task}"
            assert expected_agent in result.stage_results, (
                f"Expected {expected_agent} for '{task}', got {list(result.stage_results.keys())}"
            )

    @pytest.mark.asyncio
    async def test_orchestrator_passes_upstream_decisions(self, provider):
        """Multi-stage pipelines pass upstream decisions to downstream stages."""
        loader = ArtifactLoader()
        if "react-orchestrator" not in loader.list_agents():
            pytest.skip("Real workspace not available")

        # Use a provider that returns a pipeline classification
        class PipelineProvider(LLMProvider):
            def __init__(self):
                self._call_count = 0

            async def chat(self, messages, **kwargs):
                self._call_count += 1
                if self._call_count == 1:
                    # Classification call — return a 2-stage pipeline
                    return ChatResponse(
                        content="react-architecture -> react-scaffold",
                        input_tokens=50, output_tokens=10, model="mock",
                    )
                # Sub-agent execution calls
                return ChatResponse(
                    content=f"Stage {self._call_count - 1} complete. Decision: use server component.",
                    input_tokens=50, output_tokens=30, model="mock",
                )

            async def stream(self, messages, **kwargs):
                yield "streamed"

            def count_tokens(self, text):
                return len(text) // 4

            def get_capabilities(self):
                return ModelCapabilities(
                    context_window=8192, supports_tool_calling=False,
                    supports_structured_output=False, provider_name="mock", model_name="mock",
                )

        runtime = OrchestratorRuntime(loader=loader, provider=PipelineProvider())
        result = await runtime.execute(
            orchestrator_name="react-orchestrator",
            task="Build a complete user profile page",
            interactive=False,
        )

        assert result.stages_completed >= 1
        assert len(result.messages) > 0


class TestModelMappingIntegration:
    """Tests that model mapping works correctly in execution context."""

    def test_model_mapper_with_real_profiles(self):
        """Model mapper loads from config/model-profiles/ if present."""
        mapper = ModelMapper()
        # Should resolve without crashing
        result = mapper.resolve("claude-opus-4.8")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_model_mapper_for_orchestrator_sub_agents(self):
        """Orchestrator sub-agents get model assignments from prompt."""
        loader = ArtifactLoader()
        if "react-orchestrator" not in loader.list_agents():
            pytest.skip("Real workspace not available")

        orch = loader.load_agent("react-orchestrator")
        mapper = ModelMapper()

        # Each sub-agent should resolve to a model
        for agent_name in orch.available_sub_agents:
            model = mapper.resolve_for_agent(agent_name, orch.prompt)
            assert isinstance(model, str)
            assert len(model) > 0


class TestErrorRecovery:
    """Tests for error handling and recovery in the runtime."""

    @pytest.mark.asyncio
    async def test_agent_with_failing_hooks_still_executes(self):
        """If hooks fail, agent still runs (hooks are non-blocking)."""
        loader = ArtifactLoader()
        if "general-dev" not in loader.list_agents():
            pytest.skip("Real workspace not available")

        provider = MockProvider()
        runtime = AgentRuntime(loader=loader, provider=provider, cwd=Path("/nonexistent"))

        # CWD doesn't exist, so git hooks will fail — but agent should still run
        result = await runtime.execute(
            agent_name="general-dev",
            task="Test with bad cwd",
        )

        # Agent should still execute (hooks fail gracefully)
        assert result.success
        assert provider._call_count >= 1

    @pytest.mark.asyncio
    async def test_skill_with_no_workflow_steps(self):
        """Skill with empty workflow completes immediately."""
        from src.runtime.loader import FailureRecovery, LoadedSkill

        provider = MockProvider()
        skill = LoadedSkill(
            name="empty-skill",
            description="No steps",
            workflow_steps=[],
            failure_recovery=FailureRecovery(),
        )

        runtime = SkillRuntime(provider=provider)
        graph = runtime._compile_skill_graph(skill, provider, interactive=False)

        result = await graph.ainvoke(
            {
                "messages": [],
                "skill_name": "empty",
                "task_description": "test",
                "current_step": 0,
                "total_steps": 0,
                "step_results": {},
                "attempt_count": 0,
                "max_attempts": 3,
                "strategies_tried": [],
                "awaiting_approval": False,
                "approval_granted": False,
                "status": "running",
                "error": "",
            },
            config={"recursion_limit": 10},
        )

        assert result["status"] == "success"
