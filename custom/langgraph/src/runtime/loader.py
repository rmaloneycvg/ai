"""Artifact loader — discovers and parses Kiro workspace artifacts.

Resolves agents, skills, and steering docs from the workspace directory
structure. Handles both the primary workspace (~/workspace/ai/) and
locally-generated artifacts (output/).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Default workspace root — can be overridden via env or constructor
_DEFAULT_WORKSPACE = Path.home() / "workspace" / "ai"
_LOCAL_OUTPUT = Path(__file__).parent.parent.parent / "output"


@dataclass
class WorkflowStep:
    """A single step in a skill's workflow."""

    number: int
    name: str
    description: str
    is_approval_gate: bool = False
    commands: list[str] = field(default_factory=list)


@dataclass
class FailureRecovery:
    """Failure recovery configuration from a skill."""

    max_retries: int = 3
    steps: list[str] = field(default_factory=list)


@dataclass
class LoadedSkill:
    """Parsed representation of a Kiro skill file."""

    name: str
    description: str
    role_tone: str = ""
    environment_scope: str = "write+validate"
    workflow_steps: list[WorkflowStep] = field(default_factory=list)
    failure_recovery: FailureRecovery = field(default_factory=FailureRecovery)
    rollback: str = ""
    guardrails: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    raw_content: str = ""
    source_path: Path | None = None


@dataclass
class LoadedAgent:
    """Parsed representation of a Kiro agent JSON config."""

    name: str
    description: str
    prompt: str
    tools: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    tools_settings: dict[str, Any] = field(default_factory=dict)
    resources: list[str] = field(default_factory=list)
    hooks: dict[str, list[dict]] = field(default_factory=dict)
    mcp_servers: dict[str, Any] = field(default_factory=dict)
    source_path: Path | None = None

    @property
    def is_orchestrator(self) -> bool:
        """Detect if this agent is an orchestrator (delegates to sub-agents)."""
        crew = self.tools_settings.get("crew", {})
        if crew.get("availableAgents"):
            return True
        if "subagent" in self.tools:
            return True
        return False

    @property
    def available_sub_agents(self) -> list[str]:
        """Get sub-agent names if this is an orchestrator."""
        crew = self.tools_settings.get("crew", {})
        return crew.get("availableAgents", [])


class ArtifactLoader:
    """Discovers and loads Kiro workspace artifacts."""

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root or _DEFAULT_WORKSPACE
        self.agents_dir = self.workspace_root / "agents"
        self.skills_dir = self.workspace_root / "skills"
        self.steering_dir = self.workspace_root / "steering"
        self.local_output = _LOCAL_OUTPUT

    # ------------------------------------------------------------------
    # Agent loading
    # ------------------------------------------------------------------

    def list_agents(self) -> list[str]:
        """List available agent names (without .json extension)."""
        agents = []
        for path in self._agent_paths():
            agents.append(path.stem)
        return sorted(set(agents))

    def load_agent(self, name: str) -> LoadedAgent:
        """Load and parse an agent JSON config by name.

        Resolution order:
        1. Primary workspace: agents/<name>.json
        2. Local output: output/agents/<name>.json

        Raises:
            FileNotFoundError: If agent not found in any location.
        """
        # Try primary workspace
        path = self.agents_dir / f"{name}.json"
        if path.exists():
            return self._parse_agent(path)

        # Try local output
        local_path = self.local_output / "agents" / f"{name}.json"
        if local_path.exists():
            return self._parse_agent(local_path)

        raise FileNotFoundError(
            f"Agent '{name}' not found. Searched:\n"
            f"  {path}\n"
            f"  {local_path}\n"
            f"Available: {self.list_agents()}"
        )

    def _parse_agent(self, path: Path) -> LoadedAgent:
        """Parse an agent JSON file into LoadedAgent."""
        with open(path) as f:
            data = json.load(f)

        return LoadedAgent(
            name=data.get("name", path.stem),
            description=data.get("description", ""),
            prompt=data.get("prompt", ""),
            tools=data.get("tools", []),
            allowed_tools=data.get("allowedTools", []),
            tools_settings=data.get("toolsSettings", {}),
            resources=data.get("resources", []),
            hooks=data.get("hooks", {}),
            mcp_servers=data.get("mcpServers", {}),
            source_path=path,
        )

    def _agent_paths(self) -> list[Path]:
        """Get all agent JSON file paths."""
        paths = []
        if self.agents_dir.exists():
            paths.extend(self.agents_dir.glob("*.json"))
        local_agents = self.local_output / "agents"
        if local_agents.exists():
            paths.extend(local_agents.glob("*.json"))
        return paths

    # ------------------------------------------------------------------
    # Skill loading
    # ------------------------------------------------------------------

    def list_skills(self) -> list[str]:
        """List available skill names (without .md extension)."""
        skills = []
        for path in self._skill_paths():
            skills.append(path.stem)
        return sorted(set(skills))

    def load_skill(self, name: str) -> LoadedSkill:
        """Load and parse a skill markdown file by name.

        Resolution order:
        1. Primary workspace: skills/<name>.md
        2. Local output: output/skills/<name>.md

        Raises:
            FileNotFoundError: If skill not found in any location.
        """
        path = self.skills_dir / f"{name}.md"
        if path.exists():
            return self._parse_skill(path)

        local_path = self.local_output / "skills" / f"{name}.md"
        if local_path.exists():
            return self._parse_skill(local_path)

        raise FileNotFoundError(
            f"Skill '{name}' not found. Searched:\n"
            f"  {path}\n"
            f"  {local_path}\n"
            f"Available: {self.list_skills()}"
        )

    def _parse_skill(self, path: Path) -> LoadedSkill:
        """Parse a skill markdown file into LoadedSkill."""
        content = path.read_text()
        frontmatter, body = self._split_frontmatter(content)

        name = frontmatter.get("name", path.stem)
        description = frontmatter.get("description", "")

        # Extract sections
        role_tone = self._extract_section(body, "Role & Tone")
        env_scope = self._extract_environment_scope(body)
        workflow_steps = self._extract_workflow(body)
        failure_recovery = self._extract_failure_recovery(body)
        rollback = self._extract_section(body, "Rollback")
        guardrails = self._extract_guardrails(body)
        references = self._extract_references(body)

        return LoadedSkill(
            name=name,
            description=description,
            role_tone=role_tone,
            environment_scope=env_scope,
            workflow_steps=workflow_steps,
            failure_recovery=failure_recovery,
            rollback=rollback,
            guardrails=guardrails,
            references=references,
            raw_content=content,
            source_path=path,
        )

    def _skill_paths(self) -> list[Path]:
        """Get all skill markdown file paths."""
        paths = []
        if self.skills_dir.exists():
            paths.extend(self.skills_dir.glob("*.md"))
        local_skills = self.local_output / "skills"
        if local_skills.exists():
            paths.extend(local_skills.glob("*.md"))
        return paths

    # ------------------------------------------------------------------
    # Markdown parsing helpers
    # ------------------------------------------------------------------

    def _split_frontmatter(self, content: str) -> tuple[dict[str, str], str]:
        """Split YAML frontmatter from markdown body."""
        if not content.startswith("---"):
            return {}, content

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content

        frontmatter_raw = parts[1].strip()
        body = parts[2].strip()

        # Simple YAML parsing (key: value pairs)
        frontmatter: dict[str, str] = {}
        current_key = None
        current_value_lines: list[str] = []

        for line in frontmatter_raw.split("\n"):
            match = re.match(r"^(\w[\w_-]*)\s*:\s*(.*)$", line)
            if match:
                # Save previous key
                if current_key:
                    frontmatter[current_key] = " ".join(current_value_lines).strip()
                current_key = match.group(1)
                current_value_lines = [match.group(2).strip()]
            elif current_key and line.startswith("  "):
                # Continuation of multi-line value
                current_value_lines.append(line.strip())

        if current_key:
            frontmatter[current_key] = " ".join(current_value_lines).strip()

        return frontmatter, body

    def _extract_section(self, body: str, heading: str) -> str:
        """Extract content under a ## heading until the next ## heading."""
        pattern = rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s|\Z)"
        match = re.search(pattern, body, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_environment_scope(self, body: str) -> str:
        """Extract environment scope from the body."""
        section = self._extract_section(body, "Environment Scope")
        if not section:
            return "write+validate"

        # Look for bold scope declaration
        match = re.search(r"\*\*(write[^*]*)\*\*", section)
        if match:
            return match.group(1).strip()

        # Fallback: first line
        first_line = section.split("\n")[0].strip()
        for scope in ("write+execute", "write+validate", "write-only"):
            if scope in first_line.lower():
                return scope

        return "write+validate"

    def _extract_workflow(self, body: str) -> list[WorkflowStep]:
        """Extract numbered workflow steps."""
        section = self._extract_section(body, "Workflow")
        if not section:
            return []

        steps = []
        # Match numbered steps: "1. **Name** — Description"
        pattern = r"(\d+)\.\s+\*\*([^*]+)\*\*\s*[-—–]\s*(.*?)(?=\n\d+\.\s+\*\*|\n###|\Z)"
        for match in re.finditer(pattern, section, re.DOTALL):
            number = int(match.group(1))
            name = match.group(2).strip()
            desc = match.group(3).strip()

            # Detect approval gates
            is_gate = any(
                keyword in name.lower()
                for keyword in ("await approval", "approval", "confirm")
            )

            # Extract commands (backtick-wrapped in description)
            commands = re.findall(r"`([^`]+)`", desc)

            steps.append(WorkflowStep(
                number=number,
                name=name,
                description=desc,
                is_approval_gate=is_gate,
                commands=commands,
            ))

        return steps

    def _extract_failure_recovery(self, body: str) -> FailureRecovery:
        """Extract failure recovery config."""
        # Check for subsection header variations
        for heading in ("Failure Recovery", "Failure Recovery Loop"):
            section = self._extract_section(body, heading)
            if section:
                break

        # Also check for ### subsection within Workflow
        workflow_section = self._extract_section(body, "Workflow")
        if not section and workflow_section:
            pattern = r"###\s+Failure Recovery.*?\n(.*?)(?=^###|\Z)"
            match = re.search(pattern, workflow_section, re.MULTILINE | re.DOTALL)
            if match:
                section = match.group(1).strip()

        if not section:
            return FailureRecovery()

        # Extract max retries
        max_retries = 3
        retries_match = re.search(r"max\s+(\d+)\s+retr", section, re.IGNORECASE)
        if retries_match:
            max_retries = int(retries_match.group(1))

        # Extract steps
        steps = []
        for line in section.split("\n"):
            line = line.strip()
            if re.match(r"^\d+[a-d]?\.", line) or line.startswith("-"):
                steps.append(re.sub(r"^\d+[a-d]?\.\s*|-\s*", "", line).strip())

        return FailureRecovery(max_retries=max_retries, steps=steps)

    def _extract_guardrails(self, body: str) -> list[str]:
        """Extract guardrail rules from the Guardrails section."""
        section = self._extract_section(body, "Guardrails")
        if not section:
            return []

        guardrails = []
        for line in section.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                guardrails.append(line[2:].strip())
        return guardrails

    def _extract_references(self, body: str) -> list[str]:
        """Extract reference file paths."""
        section = self._extract_section(body, "References")
        if not section:
            return []

        refs = []
        for line in section.split("\n"):
            # Match: - `path/to/file.md` — description
            match = re.match(r"-\s+`([^`]+)`", line.strip())
            if match:
                refs.append(match.group(1))
        return refs

    # ------------------------------------------------------------------
    # Resource resolution
    # ------------------------------------------------------------------

    def resolve_resource_path(self, uri: str, relative_to: Path | None = None) -> Path | None:
        """Resolve a resource URI to an absolute path.

        Supports:
        - skill://../skills/name.md → workspace/skills/name.md
        - file://path → relative to CWD or workspace
        - Bare paths → relative to workspace root
        """
        if uri.startswith("skill://"):
            # skill://../skills/name.md → resolve relative to agents dir
            rel_path = uri.replace("skill://", "")
            base = relative_to or self.agents_dir
            resolved = (base / rel_path).resolve()
            if resolved.exists():
                return resolved
            # Fallback: try workspace root
            alt = (self.workspace_root / rel_path.lstrip("../")).resolve()
            if alt.exists():
                return alt
            return None

        if uri.startswith("file://"):
            rel_path = uri.replace("file://", "")
            # Try relative to CWD first
            cwd_path = Path.cwd() / rel_path
            if cwd_path.exists():
                return cwd_path.resolve()
            # Try relative to workspace
            ws_path = (self.workspace_root / rel_path.lstrip("../")).resolve()
            if ws_path.exists():
                return ws_path
            return None

        # Bare path
        path = Path(uri)
        if path.is_absolute() and path.exists():
            return path
        ws_path = (self.workspace_root / uri).resolve()
        if ws_path.exists():
            return ws_path
        return None
