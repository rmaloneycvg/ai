"""Tests for the agent runtime — prompt construction, resource resolution, execution."""

from __future__ import annotations

import pytest

from src.providers.base import ChatResponse, LLMProvider, ModelCapabilities
from src.runtime.agent_runtime import AgentRuntime, ExecutionResult
from src.runtime.loader import ArtifactLoader, LoadedAgent


class MockProvider(LLMProvider):
    """Mock provider for agent runtime tests."""

    def __init__(self, response: str = "Mock agent response"):
        self._response = response
        self.call_count = 0
        self.last_messages = None

    async def chat(self, messages, **kwargs):
        self.call_count += 1
        self.last_messages = messages
        return ChatResponse(
            content=self._response,
            input_tokens=50,
            output_tokens=20,
            model="mock",
        )

    async def stream(self, messages, **kwargs):
        yield self._response

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
def workspace(tmp_path):
    """Create a minimal workspace for agent runtime testing."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    steering_dir = tmp_path / "steering" / "conventions"
    steering_dir.mkdir(parents=True)

    # Agent config
    (agents_dir / "test-agent.json").write_text("""{
        "name": "test-agent",
        "description": "A test agent",
        "prompt": "You are a helpful test agent. Be concise.",
        "tools": ["read", "glob"],
        "allowedTools": ["read", "glob"],
        "toolsSettings": {},
        "resources": [
            "skill://../skills/test-skill.md",
            "file://../steering/conventions/test-steering.md"
        ],
        "hooks": {
            "agentSpawn": [
                {"command": "echo test-hook-output", "timeout_ms": 3000}
            ]
        },
        "mcpServers": {}
    }""")

    # Agent without resources or hooks
    (agents_dir / "minimal-agent.json").write_text("""{
        "name": "minimal-agent",
        "description": "Minimal agent with no resources",
        "prompt": "You are minimal.",
        "tools": [],
        "allowedTools": [],
        "toolsSettings": {},
        "resources": [],
        "hooks": {},
        "mcpServers": {}
    }""")

    # Skill file
    (skills_dir / "test-skill.md").write_text("""---
name: test-skill
description: A test skill for runtime testing.
---

# Test Skill

## Role & Tone
Act as a test engineer.

## Workflow
1. **Check** — Verify state.
2. **Execute** — Do work.

## Guardrails
- NEVER skip validation
- NEVER produce errors
""")

    # Steering doc
    (steering_dir / "test-steering.md").write_text("""# Test Steering

## Rules
- Always test first
- Keep it simple
""")

    return tmp_path


@pytest.fixture
def runtime(workspace):
    """Agent runtime with mock provider and test workspace."""
    loader = ArtifactLoader(workspace_root=workspace)
    provider = MockProvider()
    return AgentRuntime(loader=loader, provider=provider)


class TestAgentRuntimePromptConstruction:
    """Tests for system prompt assembly."""

    def test_build_system_prompt_includes_agent_prompt(self, runtime):
        agent = runtime.loader.load_agent("test-agent")
        prompt = runtime._build_system_prompt(agent, {}, "")
        assert "helpful test agent" in prompt

    def test_build_system_prompt_includes_hook_context(self, runtime):
        agent = runtime.loader.load_agent("test-agent")
        hook_context = {"git_status": "M src/file.py", "git_branch": "feat/test"}
        prompt = runtime._build_system_prompt(agent, hook_context, "")
        # format_hook_context formats these
        assert "feat/test" in prompt

    def test_build_system_prompt_includes_resources(self, runtime):
        agent = runtime.loader.load_agent("test-agent")
        resource_ctx = "### Skill: test-skill\n*Test description*"
        prompt = runtime._build_system_prompt(agent, {}, resource_ctx)
        assert "test-skill" in prompt

    def test_build_system_prompt_empty_sections_omitted(self, runtime):
        agent = runtime.loader.load_agent("minimal-agent")
        prompt = runtime._build_system_prompt(agent, {}, "")
        # Should just be the agent prompt, no extra separators
        assert prompt == "You are minimal."


class TestAgentRuntimeResourceResolution:
    """Tests for loading resources from agent configs."""

    @pytest.mark.asyncio
    async def test_resolve_skill_resource(self, workspace):
        loader = ArtifactLoader(workspace_root=workspace)
        provider = MockProvider()
        runtime = AgentRuntime(loader=loader, provider=provider)
        agent = loader.load_agent("test-agent")

        context = await runtime._resolve_resources(agent, "test task")
        # Should include the skill content
        assert "test-skill" in context
        assert "test engineer" in context

    @pytest.mark.asyncio
    async def test_resolve_file_resource(self, workspace):
        loader = ArtifactLoader(workspace_root=workspace)
        provider = MockProvider()
        runtime = AgentRuntime(loader=loader, provider=provider)
        agent = loader.load_agent("test-agent")

        context = await runtime._resolve_resources(agent, "test task")
        # Should include the steering doc
        assert "Test Steering" in context

    @pytest.mark.asyncio
    async def test_resolve_empty_resources(self, workspace):
        loader = ArtifactLoader(workspace_root=workspace)
        provider = MockProvider()
        runtime = AgentRuntime(loader=loader, provider=provider)
        agent = loader.load_agent("minimal-agent")

        context = await runtime._resolve_resources(agent, "test task")
        assert context == ""

    @pytest.mark.asyncio
    async def test_resolve_missing_resource_skipped(self, workspace):
        loader = ArtifactLoader(workspace_root=workspace)
        provider = MockProvider()
        runtime = AgentRuntime(loader=loader, provider=provider)

        # Create agent with nonexistent resource
        agent = LoadedAgent(
            name="test",
            description="test",
            prompt="test",
            resources=["file://nonexistent.json", "skill://../skills/test-skill.md"],
            source_path=workspace / "agents" / "test.json",
        )

        context = await runtime._resolve_resources(agent, "test task")
        # Should still include the valid skill, skip the missing file
        assert "test-skill" in context


class TestAgentRuntimeExecution:
    """Tests for full agent execution."""

    @pytest.mark.asyncio
    async def test_execute_minimal_agent(self, workspace):
        """Execute an agent with no tools (direct chat)."""
        provider = MockProvider(response="I am the minimal agent responding.")
        loader = ArtifactLoader(workspace_root=workspace)
        runtime = AgentRuntime(loader=loader, provider=provider)

        result = await runtime.execute(
            agent_name="minimal-agent",
            task="Hello, what can you do?",
        )

        assert result.success
        assert len(result.messages) == 2  # Human + AI
        assert "minimal agent responding" in result.messages[1].content
        assert provider.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_agent_with_hooks(self, workspace):
        """Execute an agent that has agentSpawn hooks."""
        provider = MockProvider(response="Agent with hooks responding.")
        loader = ArtifactLoader(workspace_root=workspace)
        runtime = AgentRuntime(loader=loader, provider=provider)

        result = await runtime.execute(
            agent_name="test-agent",
            task="Do something",
        )

        assert result.success
        # The system prompt should include hook output
        messages = provider.last_messages
        system_msg = messages[0].content
        assert "test-hook-output" in system_msg

    @pytest.mark.asyncio
    async def test_execute_agent_not_found(self, workspace):
        """Executing a nonexistent agent raises FileNotFoundError."""
        provider = MockProvider()
        loader = ArtifactLoader(workspace_root=workspace)
        runtime = AgentRuntime(loader=loader, provider=provider)

        with pytest.raises(FileNotFoundError, match="nonexistent"):
            await runtime.execute(agent_name="nonexistent", task="test")

    @pytest.mark.asyncio
    async def test_execute_result_structure(self, workspace):
        """Verify ExecutionResult fields are properly populated."""
        provider = MockProvider(response="Task complete.")
        loader = ArtifactLoader(workspace_root=workspace)
        runtime = AgentRuntime(loader=loader, provider=provider)

        result = await runtime.execute(
            agent_name="minimal-agent",
            task="Do the task",
        )

        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.error is None
        assert isinstance(result.messages, list)
        assert isinstance(result.files_created, list)
        assert isinstance(result.files_modified, list)


class TestAgentRuntimeWithRealWorkspace:
    """Integration-style tests using the real workspace (if available)."""

    @pytest.mark.asyncio
    async def test_load_and_prepare_real_agent(self):
        """Load a real agent and verify prompt construction succeeds."""
        loader = ArtifactLoader()
        agents = loader.list_agents()

        if "general-dev" not in agents:
            pytest.skip("Real workspace not available")

        provider = MockProvider()
        runtime = AgentRuntime(loader=loader, provider=provider)
        agent = loader.load_agent("general-dev")

        # Execute hooks
        from src.runtime.hooks import execute_hooks

        hooks = await execute_hooks(agent.hooks)
        assert isinstance(hooks, dict)

        # Resolve resources
        context = await runtime._resolve_resources(agent, "test task")
        # general-dev has resources (git-workflow skill, package.json, tsconfig)
        # At minimum the skill should load
        assert len(context) > 0 or len(agent.resources) == 0

    @pytest.mark.asyncio
    async def test_prompt_includes_guardrails_from_skills(self):
        """Verify that skill guardrails end up in the system prompt."""
        loader = ArtifactLoader()
        agents = loader.list_agents()

        if "react-frontend" not in agents:
            pytest.skip("Real workspace not available")

        provider = MockProvider()
        runtime = AgentRuntime(loader=loader, provider=provider)
        agent = loader.load_agent("react-frontend")

        context = await runtime._resolve_resources(agent, "Add a component")
        # react-frontend loads multiple skills — should have guardrails
        if context:
            assert "NEVER" in context or "Workflow" in context
