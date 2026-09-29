#!/usr/bin/env python3
"""Validation harness for the Copilot staging tree.

Checks, per artifact type:
  - instructions (.github/instructions/*.instructions.md): valid YAML frontmatter,
    has `applyTo`.
  - skills (.github/skills/<name>/SKILL.md): valid frontmatter, `name` present,
    lowercase/numbers/hyphens only, <=64 chars, equals parent directory name;
    `description` present and <=1024 chars.
  - agents (.github/agents/*.agent.md): valid frontmatter, has `name` + `description`;
    every entry in `agents:` and every `handoffs[].agent` resolves to another agent
    file in the same directory (built-in `agent`/`ask`/`plan` targets are allowed).
  - MCP registration JSON (.vscode/mcp.json, copilot-mcp.json): parses as JSON.

Exit code 0 = all good, 1 = at least one error. Prints a summary.

Usage:
  python3 validate.py [root]     # root defaults to the directory containing this file
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
SKILL_NAME_RE = re.compile(r"^[a-z0-9-]+$")
BUILTIN_AGENT_TARGETS = {"agent", "ask", "plan"}


class Validator:
    def __init__(self, root: Path):
        self.root = root
        self.errors: list[str] = []
        self.checked = 0

    def err(self, path: Path, msg: str) -> None:
        self.errors.append(f"{path.relative_to(self.root)}: {msg}")

    @staticmethod
    def parse_frontmatter(text: str):
        m = FRONTMATTER_RE.match(text)
        if not m:
            return None, "missing YAML frontmatter (--- block at top of file)"
        try:
            data = yaml.safe_load(m.group(1))
        except yaml.YAMLError as e:
            return None, f"invalid YAML frontmatter: {e}"
        if not isinstance(data, dict):
            return None, "frontmatter did not parse to a mapping"
        return data, None

    # ---- instructions ----
    def validate_instructions(self) -> None:
        d = self.root / ".github" / "instructions"
        if not d.is_dir():
            return
        for path in sorted(d.glob("*.instructions.md")):
            self.checked += 1
            data, e = self.parse_frontmatter(path.read_text())
            if e:
                self.err(path, e)
                continue
            if "applyTo" not in data or not str(data.get("applyTo", "")).strip():
                self.err(path, "instructions file missing required `applyTo`")

    # ---- skills ----
    def validate_skills(self) -> None:
        d = self.root / ".github" / "skills"
        if not d.is_dir():
            return
        for skill_md in sorted(d.glob("*/SKILL.md")):
            self.checked += 1
            dirname = skill_md.parent.name
            data, e = self.parse_frontmatter(skill_md.read_text())
            if e:
                self.err(skill_md, e)
                continue
            name = data.get("name")
            if not name:
                self.err(skill_md, "skill missing required `name`")
            else:
                if not SKILL_NAME_RE.match(str(name)):
                    self.err(skill_md, f"skill name '{name}' must be lowercase letters/numbers/hyphens only")
                if len(str(name)) > 64:
                    self.err(skill_md, f"skill name '{name}' exceeds 64 chars")
                if str(name) != dirname:
                    self.err(skill_md, f"skill name '{name}' must match parent dir '{dirname}'")
            desc = data.get("description")
            if not desc:
                self.err(skill_md, "skill missing required `description`")
            elif len(str(desc)) > 1024:
                self.err(skill_md, "skill description exceeds 1024 chars")
            ctx = data.get("context")
            if ctx is not None and ctx not in ("inline", "fork"):
                self.err(skill_md, f"skill context '{ctx}' must be 'inline' or 'fork'")

    # ---- agents ----
    def validate_agents(self) -> None:
        d = self.root / ".github" / "agents"
        if not d.is_dir():
            return
        agent_files = sorted(d.glob("*.agent.md"))
        # Map of declared agent name -> file (fall back to filename stem without .agent)
        known: set[str] = set()
        parsed: dict[Path, dict] = {}
        for path in agent_files:
            data, e = self.parse_frontmatter(path.read_text())
            if e:
                self.err(path, e)
                continue
            parsed[path] = data
            stem = path.name[: -len(".agent.md")]
            known.add(stem)
            if data.get("name"):
                known.add(str(data["name"]))
        for path, data in parsed.items():
            self.checked += 1
            if not data.get("name"):
                self.err(path, "agent missing required `name`")
            if not data.get("description"):
                self.err(path, "agent missing required `description`")
            # subagent references
            for sub in data.get("agents", []) or []:
                if sub == "*":
                    continue
                if sub not in known and sub not in BUILTIN_AGENT_TARGETS:
                    self.err(path, f"`agents:` references unknown agent '{sub}'")
            # handoff references
            for ho in data.get("handoffs", []) or []:
                target = ho.get("agent") if isinstance(ho, dict) else None
                if target and target not in known and target not in BUILTIN_AGENT_TARGETS:
                    self.err(path, f"`handoffs.agent` references unknown agent '{target}'")

    # ---- MCP registration JSON ----
    def validate_mcp_json(self) -> None:
        candidates = [
            self.root / ".vscode" / "mcp.json",
            self.root / "copilot-mcp.json",
            self.root / "mcp" / "copilot-cli-mcp.json",
            self.root / "plugin" / "mcp.json",
            self.root / "plugin" / "plugin.json",
            self.root / "plugin" / "com.github.copilot" / "hooks" / "hooks.json",
        ]
        for path in candidates:
            if path.is_file():
                self.checked += 1
                try:
                    json.loads(path.read_text())
                except json.JSONDecodeError as e:
                    self.err(path, f"invalid JSON: {e}")

    def validate_plugin(self) -> None:
        """The plugin bundle must only reference skills/agents that exist on disk."""
        pdir = self.root / "plugin"
        if not pdir.is_dir():
            return
        manifest = pdir / "plugin.json"
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text())
                if "$schema" not in data or "name" not in data:
                    self.err(manifest, "plugin.json missing required $schema or name")
            except json.JSONDecodeError:
                pass  # reported by validate_mcp_json
        # skills in the plugin must have SKILL.md with matching name
        for skill_md in sorted((pdir / "skills").glob("*/SKILL.md")) if (pdir / "skills").is_dir() else []:
            self.checked += 1
            dirname = skill_md.parent.name
            data, e = self.parse_frontmatter(skill_md.read_text())
            if e:
                self.err(skill_md, e)
            elif data.get("name") != dirname:
                self.err(skill_md, f"plugin skill name '{data.get('name')}' != dir '{dirname}'")
        # agents in the plugin: agents:/handoffs must resolve within the plugin
        adir = pdir / "com.github.copilot" / "agents"
        if adir.is_dir():
            known = set()
            parsed = {}
            for path in sorted(adir.glob("*.agent.md")):
                data, e = self.parse_frontmatter(path.read_text())
                if e:
                    self.err(path, e)
                    continue
                parsed[path] = data
                known.add(path.name[:-len(".agent.md")])
                if data.get("name"):
                    known.add(str(data["name"]))
            for path, data in parsed.items():
                self.checked += 1
                for sub in (data.get("agents", []) or []):
                    if sub != "*" and sub not in known and sub not in BUILTIN_AGENT_TARGETS:
                        self.err(path, f"plugin agent `agents:` references unknown '{sub}'")
                for ho in (data.get("handoffs", []) or []):
                    t = ho.get("agent") if isinstance(ho, dict) else None
                    if t and t not in known and t not in BUILTIN_AGENT_TARGETS:
                        self.err(path, f"plugin agent `handoffs.agent` references unknown '{t}'")

    def run(self) -> int:
        self.validate_instructions()
        self.validate_skills()
        self.validate_agents()
        self.validate_mcp_json()
        self.validate_plugin()
        if self.errors:
            print(f"VALIDATION FAILED — {len(self.errors)} error(s), {self.checked} file(s) checked:")
            for err in self.errors:
                print(f"  ✗ {err}")
            return 1
        print(f"VALIDATION OK — {self.checked} file(s) checked, no errors.")
        return 0


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    root = root.resolve()
    if not root.is_dir():
        print(f"ERROR: root '{root}' is not a directory", file=sys.stderr)
        return 2
    return Validator(root).run()


if __name__ == "__main__":
    raise SystemExit(main())
