"""Tests for the orchestrator runtime — multi-agent pipeline execution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.providers.base import ChatResponse, LLMProvider, ModelCapabilities
from src.runtime.loader import ArtifactLoader, LoadedAgent
from src.runtime.orchestrator import OrchestratorRuntime


class MockProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, responses: list[str] | None = None):
        self._responses = responses or ["mock response"]
        self._call_count = 0

    async def chat(self, messages, **kwargs):
        idx = min(self._call_count, len(self._responses) - 1)
        response = self._responses[idx]
        self._call_count += 1
        return ChatResponse(
            content=response, input_tokens=50, output_tokens=20, model="mock"
        )

    async def stream(self, messages, **kwargs):
        yield "mock"

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


@pytest.fixture
def orchestrator_loader(tmp_path):
    """Loader with orchestrator and sub-agent configs."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # Orchestrator config
    (agents_dir / "test-orchestrator.json").write_text("""{
        "name": "test-orchestrator",
        "description": "Test orchestrator with sub-agents",
        "prompt": "You are a test orchestrator.\\n\\nSub-agents:\\n- agent-a: handles analysis\\n- agent-b: handles implementation\\n\\nForced routing:\\n- 'analyze: ...' → agent-a directly\\n- 'build: ...' → agent-b directly\\n\\nPipelines:\\n- Full: agent-a -> agent-b",
        "tools": ["read", "subagent"],
        "allowedTools": ["read", "subagent"],
        "toolsSettings": {
            "crew": {
                "availableAgents": ["agent-a", "agent-b"]
            }
        },
        "resources": [],
        "hooks": {},
        "mcpServers": {}
    }""")

    # Sub-agent A
    (agents_dir / "agent-a.json").write_text("""{
        "name": "agent-a",
        "description": "Analysis sub-agent",
        "prompt": "You analyze requirements and produce specifications.",
        "tools": ["read", "glob"],
        "allowedTools": ["read", "glob"],
        "toolsSettings": {},
        "resources": [],
        "hooks": {},
        "mcpServers": {}
    }""")

    # Sub-agent B
    (agents_dir / "agent-b.json").write_text("""{
        "name": "agent-b",
        "description": "Implementation sub-agent",
        "prompt": "You implement code based on specifications.",
        "tools": ["read", "write"],
        "allowedTools": ["read", "write"],
        "toolsSettings": {},
        "resources": [],
        "hooks": {},
        "mcpServers": {}
    }""")

    # Non-orchestrator agent
    (agents_dir / "simple-agent.json").write_text("""{
        "name": "simple-agent",
        "description": "Not an orchestrator",
        "prompt": "You are a simple agent.",
        "tools": ["read"],
        "allowedTools": ["read"],
        "toolsSettings": {},
        "resources": [],
        "hooks": {},
        "mcpServers": {}
    }""")

    # Create empty skills dir
    (tmp_path / "skills").mkdir()

    return ArtifactLoader(workspace_root=tmp_path)


class TestOrchestratorDetection:
    """Tests for identifying orchestrator agents."""

    def test_orchestrator_detected(self, orchestrator_loader):
        agent = orchestrator_loader.load_agent("test-orchestrator")
        assert agent.is_orchestrator is True
        assert agent.available_sub_agents == ["agent-a", "agent-b"]

    def test_non_orchestrator_not_detected(self, orchestrator_loader):
        agent = orchestrator_loader.load_agent("simple-agent")
        assert agent.is_orchestrator is False


class TestForcedRouting:
    """Tests for forced routing prefix detection."""

    def test_forced_routing_detected(self):
        runtime = OrchestratorRuntime()
        prompt = (
            "Forced routing:\n"
            "- 'analyze: ...' → agent-a directly\n"
            "- 'build: ...' → agent-b directly\n"
        )
        assert runtime._check_forced_routing("analyze: the requirements", prompt) == "agent-a"
        assert runtime._check_forced_routing("build: the component", prompt) == "agent-b"

    def test_no_forced_routing(self):
        runtime = OrchestratorRuntime()
        prompt = "- 'test: ...' → agent-c directly"
        assert runtime._check_forced_routing("just a normal request", prompt) is None


class TestPipelineResponseParsing:
    """Tests for parsing LLM classification responses."""

    def test_single_agent(self):
        runtime = OrchestratorRuntime()
        available = ["agent-a", "agent-b", "agent-c"]

        result = runtime._parse_pipeline_response("agent-b", available)
        assert result == ["agent-b"]

    def test_pipeline_with_arrows(self):
        runtime = OrchestratorRuntime()
        available = ["agent-a", "agent-b", "agent-c"]

        result = runtime._parse_pipeline_response(
            "agent-a -> agent-b -> agent-c", available
        )
        assert result == ["agent-a", "agent-b", "agent-c"]

    def test_pipeline_with_unicode_arrows(self):
        runtime = OrchestratorRuntime()
        available = ["agent-a", "agent-b"]

        result = runtime._parse_pipeline_response("agent-a → agent-b", available)
        assert result == ["agent-a", "agent-b"]

    def test_invalid_agents_filtered(self):
        runtime = OrchestratorRuntime()
        available = ["agent-a", "agent-b"]

        result = runtime._parse_pipeline_response(
            "agent-a -> nonexistent -> agent-b", available
        )
        assert result == ["agent-a", "agent-b"]

    def test_no_match_returns_none(self):
        runtime = OrchestratorRuntime()
        available = ["agent-a", "agent-b"]

        result = runtime._parse_pipeline_response("I don't know", available)
        assert result is None


class TestOrchestratorExecution:
    """Tests for executing orchestrator pipelines."""

    @pytest.mark.asyncio
    async def test_execute_single_stage_pipeline(self, orchestrator_loader):
        """Execute a pipeline with forced routing to a single agent."""
        provider = MockProvider(responses=[
            "agent-a",  # Classification response (won't be used due to forced)
            "Analysis complete: need a UserProfile component",  # agent-a response
        ])

        runtime = OrchestratorRuntime(
            loader=orchestrator_loader,
            provider=provider,
        )

        result = await runtime.execute(
            orchestrator_name="test-orchestrator",
            task="analyze: the user profile requirements",
            interactive=False,
        )

        assert result.success
        assert result.stages_completed >= 1
        assert len(result.messages) > 0

    @pytest.mark.asyncio
    async def test_execute_multi_stage_pipeline(self, orchestrator_loader):
        """Execute a pipeline that the orchestrator classifies as multi-stage."""
        # Provide enough responses for: classification + each sub-agent
        provider = MockProvider(responses=[
            "agent-a -> agent-b",  # Classification response
            "Architecture: use server component",  # agent-a execution
            "Implementation complete",  # agent-b execution
            "extra response just in case",  # safety buffer
        ])

        runtime = OrchestratorRuntime(
            loader=orchestrator_loader,
            provider=provider,
        )

        result = await runtime.execute(
            orchestrator_name="test-orchestrator",
            task="Build a complete user settings page",
            interactive=False,
        )

        # Pipeline should execute and complete
        assert result.success
        assert result.stages_completed >= 1
        assert result.total_stages >= 1
        assert len(result.messages) > 0
        assert len(result.stage_results) >= 1

    @pytest.mark.asyncio
    async def test_non_orchestrator_delegates_to_agent_runtime(self, orchestrator_loader):
        """Non-orchestrator agents get executed as regular agents."""
        provider = MockProvider(responses=["Simple response"])

        runtime = OrchestratorRuntime(
            loader=orchestrator_loader,
            provider=provider,
        )

        result = await runtime.execute(
            orchestrator_name="simple-agent",
            task="Do something simple",
            interactive=False,
        )

        # Should still work (delegated to AgentRuntime)
        assert result.success

    @pytest.mark.asyncio
    async def test_missing_sub_agent_skipped(self, orchestrator_loader):
        """If a sub-agent config doesn't exist, it's skipped."""
        provider = MockProvider(responses=[
            "nonexistent-agent -> agent-b",  # Routes to missing agent first
            "Implementation done",  # agent-b response
        ])

        runtime = OrchestratorRuntime(
            loader=orchestrator_loader,
            provider=provider,
        )

        # The pipeline parsing will filter out nonexistent since it's not in available
        # So only agent-b should be in the pipeline
        result = await runtime.execute(
            orchestrator_name="test-orchestrator",
            task="Build something",
            interactive=False,
        )

        # Should handle gracefully
        assert len(result.messages) > 0


class TestRealOrchestratorExecution:
    """Integration tests with real workspace orchestrators."""

    @pytest.mark.asyncio
    async def test_list_real_orchestrators(self):
        """Verify real orchestrators are detected."""
        loader = ArtifactLoader()
        agents = loader.list_agents()

        if "react-orchestrator" not in agents:
            pytest.skip("Real workspace not available")

        orch = loader.load_agent("react-orchestrator")
        assert orch.is_orchestrator
        assert "react-scaffold" in orch.available_sub_agents
        assert "react-architecture" in orch.available_sub_agents

    @pytest.mark.asyncio
    async def test_classify_react_orchestrator(self):
        """Test classification with the real react-orchestrator prompt."""
        loader = ArtifactLoader()
        agents = loader.list_agents()

        if "react-orchestrator" not in agents:
            pytest.skip("Real workspace not available")

        orch = loader.load_agent("react-orchestrator")
        runtime = OrchestratorRuntime(loader=loader)

        # Test forced routing
        result = runtime._check_forced_routing("scaffold: a new button", orch.prompt)
        assert result == "react-scaffold"

        result = runtime._check_forced_routing("test: the login form", orch.prompt)
        assert result == "react-testing"

        result = runtime._check_forced_routing("refactor: extract hook", orch.prompt)
        assert result == "react-refactor"
