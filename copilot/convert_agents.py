#!/usr/bin/env python3
"""Convert Kiro simple (single-role) agents to Copilot .agent.md files.

Reads ~/workspace/ai/agents/<name>.json and writes
copilot/.github/agents/<name>.agent.md with YAML frontmatter + Markdown body.

Mapping decisions (documented in MIGRATION-NOTES):
  - prompt            -> Markdown body (verbatim)
  - name/description  -> frontmatter name/description
  - model:            'auto'          -> omitted (no Copilot equivalent)
                       'claude-sonnet-4' -> ['Claude Sonnet 4']  (model-priority array)
  - tools:            Kiro '@builtin' is mapped per-agent to a Copilot tool set
                      derived from the agent's role + Kiro permission rules
                      (least privilege): read-only planners get no `edit`/`runCommands`.
  - MCP tools:        Kiro allowedTools like '@git/git_status', '@io/read_json'
                      become Copilot MCP tool refs 'git/*', 'io/*' and are recorded
                      as needed MCP servers (registered in Task 6).
  - hooks:            Kiro agentSpawn shell hooks are carried into the body as an
                      informational note (agent-scoped `hooks:` is Local/Preview only;
                      full treatment in Task 7). Not emitted as frontmatter here to
                      keep these agents portable across CLI/cloud.
  - permissions:      Kiro deny/ask/allow rules have NO Copilot equivalent; the
                      restriction intent is preserved only via the `tools` allow-list.

The orchestrator (react-orchestrator) is handled separately in Task 5.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SRC = Path.home() / "workspace" / "ai" / "agents"
DST = Path(__file__).resolve().parent / ".github" / "agents"

SIMPLE_AGENTS = [
    "general-dev", "react-architecture", "react-frontend", "react-scaffold",
    "react-styling", "react-testing", "resume-builder", "spec-planner", "work-summary",
]

# Per-agent Copilot tool policy. Read-only agents omit edit/runCommands.
# Values are Copilot tool / tool-set names (and MCP <server>/* refs).
TOOL_POLICY: dict[str, list[str]] = {
    # Plan/analysis only — least privilege, no editing or shell.
    "spec-planner": ["search", "web/fetch"],
    "react-architecture": ["search", "web/fetch"],
    # Code-editing agents.
    "react-scaffold": ["edit", "search", "runCommands"],
    "react-styling": ["edit", "search"],
    "react-testing": ["edit", "search", "runCommands"],
    "react-frontend": ["edit", "search", "runCommands", "git/*", "io/*"],
    "general-dev": ["edit", "search", "runCommands", "web/fetch"],
    # Content generators that run python + fetch and write to scoped dirs.
    "resume-builder": ["edit", "search", "runCommands", "web/fetch"],
    # work-summary scans git repos + AI sessions -> git + work-summary MCP servers.
    "work-summary": ["edit", "search", "runCommands", "web/fetch", "git/*", "work-summary/*"],
}

# MCP servers each agent needs (Copilot mcp-servers frontmatter references).
MCP_SERVERS: dict[str, list[str]] = {
    "react-frontend": ["git", "io"],
    "work-summary": ["git", "work-summary"],
}

MODEL_MAP = {
    "claude-sonnet-4": ["Claude Sonnet 4"],
    # 'auto' -> omitted
}


def yaml_scalar(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v)
    if s == "":
        return "''"
    if re.search(r"[:#\[\]{}&*!|>'\"%@`,]", s) or s[0] in "-?" or s != s.strip():
        return "'" + s.replace("'", "''") + "'"
    return s


def yaml_list(items: list[str]) -> str:
    return "[" + ", ".join(yaml_scalar(i) for i in items) + "]"


def hook_note(hooks: dict) -> str:
    """Render Kiro agentSpawn hooks as an informational body note."""
    spawn = (hooks or {}).get("agentSpawn") or []
    if not spawn:
        return ""
    cmds = "\n".join(f"  - `{h.get('command','')}`" for h in spawn)
    return (
        "\n\n---\n"
        "> **Migration note (Kiro `agentSpawn` hooks).** In Kiro this agent ran the "
        "following commands to seed context at spawn time:\n"
        f"{cmds}\n\n"
        "> Copilot has no portable per-agent spawn hook (agent-scoped `hooks:` run only "
        "in the Local harness/Preview). Run these manually or rely on the git/io MCP "
        "server tools. See MIGRATION-NOTES.md.\n"
    )


def convert(name: str) -> dict:
    d = json.loads((SRC / f"{name}.json").read_text())
    fm_lines = ["---"]
    fm_lines.append(f"name: {yaml_scalar(d.get('name', name))}")
    fm_lines.append(f"description: {yaml_scalar(d.get('description',''))}")

    tools = TOOL_POLICY[name]
    fm_lines.append(f"tools: {yaml_list(tools)}")

    if name in MCP_SERVERS:
        # mcp-servers frontmatter is a list of server config names; the concrete
        # config (command/args/env) is registered in Task 6. We reference by name.
        fm_lines.append(f"mcp-servers: {yaml_list(MCP_SERVERS[name])}")

    model = d.get("model")
    if model and model in MODEL_MAP:
        fm_lines.append(f"model: {yaml_list(MODEL_MAP[model])}")
    # model 'auto' or unknown -> omitted

    fm_lines.append("---")
    frontmatter = "\n".join(fm_lines) + "\n\n"

    body = d.get("prompt", "").rstrip() + "\n"
    body += hook_note(d.get("hooks", {}))

    out = DST / f"{name}.agent.md"
    out.write_text(frontmatter + body)
    return {
        "name": name,
        "tools": tools,
        "mcp": MCP_SERVERS.get(name, []),
        "model": model,
        "read_only": "edit" not in tools,
        "had_hooks": bool((d.get("hooks") or {}).get("agentSpawn")),
        "had_permissions": bool(d.get("permissions", {}).get("rules")),
    }


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    for name in SIMPLE_AGENTS:
        info = convert(name)
        flags = []
        if info["read_only"]:
            flags.append("read-only")
        if info["mcp"]:
            flags.append("mcp=" + ",".join(info["mcp"]))
        if info["had_hooks"]:
            flags.append("had-spawn-hooks")
        if info["had_permissions"]:
            flags.append("had-perms")
        print(f"  {name}.agent.md  tools={info['tools']}  " + " ".join(flags))
    print(f"\nConverted {len(SIMPLE_AGENTS)} simple agents.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
