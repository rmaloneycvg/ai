#!/usr/bin/env python3
"""Assemble an Agent Plugins 1.0 bundle from the staging tree.

Layout produced under copilot/plugin/ (Agent Plugins 1.0 spec):

  plugin/
    plugin.json                         # $schema = agent-plugins 1.0
    skills/<name>/SKILL.md              # portable skills (copied from .github/skills)
    mcp.json                            # portable MCP config (servers{} form)
    com.github.copilot/
      agents/<name>.agent.md           # Copilot-specific custom agents
      hooks/hooks.json                 # Copilot-specific lifecycle hooks (enrichment)
    scripts/                            # hook scripts referenced via ${PLUGIN_ROOT}

Only components that exist on disk are bundled. Skills and MCP are the portable
component types; agents + hooks live under the com.github.copilot namespace.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GH = ROOT / ".github"
PLUGIN = ROOT / "plugin"

NAME = "kiro-ported-devtools"
VERSION = "0.1.0"


def rmtree(p: Path):
    if p.exists():
        shutil.rmtree(p)


def main() -> int:
    rmtree(PLUGIN)
    PLUGIN.mkdir(parents=True)

    # --- plugin.json (Agent Plugins 1.0) ---
    manifest = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": NAME,
        "version": VERSION,
        "description": "Kiro configuration ported to GitHub Copilot: agent skills, custom "
                       "agents (with subagents + handoffs), and MCP servers.",
        "keywords": ["react", "nextjs", "security", "planning", "mcp", "devtools"],
        "license": "MIT",
    }
    (PLUGIN / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # --- portable skills/ ---
    skills_src = GH / "skills"
    skills_dst = PLUGIN / "skills"
    skill_names = []
    if skills_src.is_dir():
        shutil.copytree(skills_src, skills_dst)
        skill_names = sorted(p.name for p in skills_dst.iterdir() if p.is_dir())

    # --- portable mcp.json (servers{} form, reuse .vscode/mcp.json content) ---
    vscode_mcp = ROOT / ".vscode" / "mcp.json"
    mcp_servers = []
    if vscode_mcp.is_file():
        data = json.loads(vscode_mcp.read_text())
        servers = data.get("servers", {})
        # Portable MCP config uses the same servers{} shape; drop $comment.
        portable = {"servers": servers}
        (PLUGIN / "mcp.json").write_text(json.dumps(portable, indent=2) + "\n")
        mcp_servers = sorted(servers.keys())

    # --- Copilot-specific: agents + hooks ---
    copilot_dir = PLUGIN / "com.github.copilot"
    agents_src = GH / "agents"
    agent_names = []
    if agents_src.is_dir():
        shutil.copytree(agents_src, copilot_dir / "agents")
        agent_names = sorted(p.name[:-len(".agent.md")] for p in (copilot_dir / "agents").glob("*.agent.md"))

    # hooks: enrichment hooks only (guards are pre-commit/CI, not agent hooks).
    scripts_src = ROOT / "hooks" / "scripts"
    if scripts_src.is_dir():
        shutil.copytree(scripts_src, PLUGIN / "scripts")
    hooks_cfg = {
        "hooks": {
            "SessionStart": [
                {"type": "command", "command": "${PLUGIN_ROOT}/scripts/validate-environment.sh"}
            ],
            "UserPromptSubmit": [
                {"type": "command", "command": "${PLUGIN_ROOT}/scripts/git-context.sh"}
            ],
        }
    }
    (copilot_dir / "hooks").mkdir(parents=True, exist_ok=True)
    (copilot_dir / "hooks" / "hooks.json").write_text(json.dumps(hooks_cfg, indent=2) + "\n")

    print(f"Plugin '{NAME}' v{VERSION} assembled at plugin/")
    print(f"  skills ({len(skill_names)}): {', '.join(skill_names)}")
    print(f"  agents ({len(agent_names)}): {', '.join(agent_names)}")
    print(f"  mcp servers ({len(mcp_servers)}): {', '.join(mcp_servers)}")
    print(f"  hooks: SessionStart, UserPromptSubmit (enrichment; guards are pre-commit/CI)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
