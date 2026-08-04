"""Tests for the artifact loader."""

from pathlib import Path

import pytest

from src.runtime.loader import ArtifactLoader, LoadedAgent, LoadedSkill


@pytest.fixture
def loader():
    """Loader pointing at the real workspace."""
    return ArtifactLoader(workspace_root=Path.home() / "workspace" / "ai")


@pytest.fixture
def fixtures_loader(tmp_path):
    """Loader pointing at test fixtures."""
    # Create fixture agents
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "test-agent.json").write_text("""{
        "name": "test-agent",
        "description": "A test agent for unit testing",
        "prompt": "You are a test agent.",
        "tools": ["read", "write", "shell", "@git"],
        "allowedTools": ["read", "@git/git_status"],
        "toolsSettings": {
            "write": {"allowedPaths": ["src/**", "*.ts"]},
            "shell": {"allowedCommands": ["npm *", "git *"]}
        },
        "resources": ["skill://../skills/test-skill.md"],
        "hooks": {
            "agentSpawn": [
                {"command": "echo hello", "timeout_ms": 3000}
            ]
        },
        "mcpServers": {}
    }""")

    (agents_dir / "orchestrator.json").write_text("""{
        "name": "orchestrator",
        "description": "A test orchestrator",
        "prompt": "You orchestrate sub-agents.",
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

    # Create fixture skills
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "test-skill.md").write_text("""---
name: test-skill
description: Use when testing the runtime system. Covers validation and verification.
---

# Test Skill

## Role & Tone

Act as a QA engineer. Be thorough and systematic.

## Environment Scope

**write+validate** — Writes test files. Runs `pytest`. No side effects.

## Workflow

1. **Check Existing State** — Verify tests don't already exist for this module.
2. **Gather Context** — Read the source file to understand the API surface.
3. **Await Approval** — Present test plan. Wait for confirmation.
4. **Implement** — Write pytest test file.
5. **Verify** — Run `pytest` on the new file.

### Failure Recovery (max 3 retries)

1. Read pytest error output
2. Fix the specific assertion or import
3. Re-run pytest

## Guardrails

- NEVER modify source code — only create test files
- NEVER skip the approval step
- NEVER create tests without assertions

## References

- `steering/conventions/code-style.md` — naming conventions
""")

    return ArtifactLoader(workspace_root=tmp_path)


class TestAgentLoading:
    """Tests for agent JSON parsing."""

    def test_list_agents(self, fixtures_loader):
        agents = fixtures_loader.list_agents()
        assert "test-agent" in agents
        assert "orchestrator" in agents

    def test_load_agent(self, fixtures_loader):
        agent = fixtures_loader.load_agent("test-agent")
        assert isinstance(agent, LoadedAgent)
        assert agent.name == "test-agent"
        assert agent.description == "A test agent for unit testing"
        assert agent.prompt == "You are a test agent."
        assert "read" in agent.tools
        assert "shell" in agent.tools
        assert "@git" in agent.tools
        assert agent.allowed_tools == ["read", "@git/git_status"]

    def test_agent_tools_settings(self, fixtures_loader):
        agent = fixtures_loader.load_agent("test-agent")
        assert agent.tools_settings["write"]["allowedPaths"] == ["src/**", "*.ts"]
        assert "npm *" in agent.tools_settings["shell"]["allowedCommands"]

    def test_agent_hooks(self, fixtures_loader):
        agent = fixtures_loader.load_agent("test-agent")
        hooks = agent.hooks["agentSpawn"]
        assert len(hooks) == 1
        assert hooks[0]["command"] == "echo hello"
        assert hooks[0]["timeout_ms"] == 3000

    def test_orchestrator_detection(self, fixtures_loader):
        orch = fixtures_loader.load_agent("orchestrator")
        assert orch.is_orchestrator is True
        assert orch.available_sub_agents == ["agent-a", "agent-b"]

        agent = fixtures_loader.load_agent("test-agent")
        assert agent.is_orchestrator is False
        assert agent.available_sub_agents == []

    def test_agent_not_found_raises(self, fixtures_loader):
        with pytest.raises(FileNotFoundError, match="nonexistent"):
            fixtures_loader.load_agent("nonexistent")


class TestSkillLoading:
    """Tests for skill markdown parsing."""

    def test_list_skills(self, fixtures_loader):
        skills = fixtures_loader.list_skills()
        assert "test-skill" in skills

    def test_load_skill_frontmatter(self, fixtures_loader):
        skill = fixtures_loader.load_skill("test-skill")
        assert isinstance(skill, LoadedSkill)
        assert skill.name == "test-skill"
        assert "testing the runtime" in skill.description

    def test_skill_role_tone(self, fixtures_loader):
        skill = fixtures_loader.load_skill("test-skill")
        assert "QA engineer" in skill.role_tone

    def test_skill_environment_scope(self, fixtures_loader):
        skill = fixtures_loader.load_skill("test-skill")
        assert skill.environment_scope == "write+validate"

    def test_skill_workflow_steps(self, fixtures_loader):
        skill = fixtures_loader.load_skill("test-skill")
        assert len(skill.workflow_steps) >= 4
        assert skill.workflow_steps[0].name == "Check Existing State"
        assert skill.workflow_steps[0].number == 1

    def test_skill_approval_gate_detected(self, fixtures_loader):
        skill = fixtures_loader.load_skill("test-skill")
        approval_steps = [s for s in skill.workflow_steps if s.is_approval_gate]
        assert len(approval_steps) >= 1
        assert "Approval" in approval_steps[0].name

    def test_skill_failure_recovery(self, fixtures_loader):
        skill = fixtures_loader.load_skill("test-skill")
        assert skill.failure_recovery.max_retries == 3
        assert len(skill.failure_recovery.steps) >= 1

    def test_skill_guardrails(self, fixtures_loader):
        skill = fixtures_loader.load_skill("test-skill")
        assert len(skill.guardrails) == 3
        assert any("NEVER modify source" in g for g in skill.guardrails)
        assert any("NEVER skip" in g for g in skill.guardrails)

    def test_skill_references(self, fixtures_loader):
        skill = fixtures_loader.load_skill("test-skill")
        assert "steering/conventions/code-style.md" in skill.references

    def test_skill_not_found_raises(self, fixtures_loader):
        with pytest.raises(FileNotFoundError, match="nonexistent"):
            fixtures_loader.load_skill("nonexistent")


class TestRealWorkspace:
    """Integration tests that load from the real workspace (if available)."""

    def test_list_real_agents(self, loader):
        """Verify we can list agents from ~/workspace/ai/agents/."""
        agents = loader.list_agents()
        # These should exist based on our earlier exploration
        if agents:  # Only assert if workspace exists
            assert "react-frontend" in agents or "general-dev" in agents

    def test_load_real_agent(self, loader):
        """Verify we can parse a real agent config."""
        agents = loader.list_agents()
        if "general-dev" in agents:
            agent = loader.load_agent("general-dev")
            assert agent.name == "general-dev"
            assert "read" in agent.tools
            assert len(agent.prompt) > 0

    def test_list_real_skills(self, loader):
        """Verify we can list skills from ~/workspace/ai/skills/."""
        skills = loader.list_skills()
        if skills:
            assert "general-debug" in skills or "react-scaffold" in skills

    def test_load_real_skill(self, loader):
        """Verify we can parse a real skill file."""
        skills = loader.list_skills()
        if "general-debug" in skills:
            skill = loader.load_skill("general-debug")
            assert skill.name == "general-debug"
            assert len(skill.workflow_steps) >= 3
            assert len(skill.guardrails) >= 1
