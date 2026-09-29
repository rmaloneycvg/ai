#!/usr/bin/env python3
"""Convert the Kiro react-orchestrator to a Copilot .agent.md with subagents + handoffs.

Mapping:
  - toolsSettings.crew.availableAgents -> `agents:` (only agents that actually exist
    on disk are listed; dangling refs like react-refactor are dropped and flagged).
  - `agent` tool added to `tools:` so the orchestrator can invoke subagents.
  - routing/pipeline prompt preserved as the Markdown body.
  - `handoffs:` chains added (net-new Copilot workflow UX) reflecting the react
    pipeline: architecture -> scaffold -> styling -> testing.
  - trustedAgents `react-*` glob has no Copilot equivalent -> replaced by the explicit
    `agents:` allow-list (flagged in MIGRATION-NOTES).
  - per-subagent model overrides (Kiro stage config) don't port -> flagged; each
    subagent's own `.agent.md` model applies instead.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SRC = Path.home() / "workspace" / "ai" / "agents" / "react-orchestrator.json"
AGENTS_DIR = Path(__file__).resolve().parent / ".github" / "agents"
OUT = AGENTS_DIR / "react-orchestrator.agent.md"


def yaml_scalar(v) -> str:
    s = str(v)
    if s == "":
        return "''"
    if re.search(r"[:#\[\]{}&*!|>'\"%@`,]", s) or s[0] in "-?" or s != s.strip():
        return "'" + s.replace("'", "''") + "'"
    return s


def existing_agents(names: list[str]) -> tuple[list[str], list[str]]:
    present, missing = [], []
    for n in names:
        if (AGENTS_DIR / f"{n}.agent.md").exists():
            present.append(n)
        else:
            missing.append(n)
    return present, missing


def main() -> int:
    d = json.loads(SRC.read_text())
    crew = d.get("toolsSettings", {}).get("crew", {})
    available = crew.get("availableAgents", [])
    present, missing = existing_agents(available)

    tools = ["agent", "search"]
    fm = ["---"]
    fm.append(f"name: {yaml_scalar(d.get('name','react-orchestrator'))}")
    fm.append(f"description: {yaml_scalar(d.get('description',''))}")
    fm.append("tools: [" + ", ".join(yaml_scalar(t) for t in tools) + "]")
    fm.append("agents: [" + ", ".join(yaml_scalar(a) for a in present) + "]")
    # Handoff chain reflecting the react pipeline (only include existing targets).
    handoff_chain = [
        ("react-architecture", "Design Architecture", "Decompose this feature: define component boundaries, server/client split, and data flow before any code is written."),
        ("react-scaffold", "Scaffold Components", "Scaffold the components, stories, and tests for the architecture decided above."),
        ("react-styling", "Apply Styling", "Apply Tailwind/shadcn styling and responsive, accessible design to the scaffolded components."),
        ("react-testing", "Write & Run Tests", "Write and run Vitest/Playwright tests and Storybook stories for the components above."),
    ]
    handoff_chain = [(a, l, p) for (a, l, p) in handoff_chain if a in present]
    if handoff_chain:
        fm.append("handoffs:")
        for agent, label, prompt in handoff_chain:
            fm.append(f"  - label: {yaml_scalar(label)}")
            fm.append(f"    agent: {yaml_scalar(agent)}")
            fm.append(f"    prompt: {yaml_scalar(prompt)}")
            fm.append("    send: false")
    fm.append("---")
    frontmatter = "\n".join(fm) + "\n\n"

    body = d.get("prompt", "").rstrip() + "\n"

    # Migration note appended to the body.
    note = ["\n\n---\n"]
    note.append("> **Migration notes (orchestrator).**\n")
    if missing:
        note.append(
            f"> - Kiro listed subagent(s) {', '.join('`'+m+'`' for m in missing)} in its crew, "
            "but no source agent definition exists for them; they are omitted from `agents:` "
            "here. Author the missing agent(s) to re-enable that route.\n"
        )
    note.append(
        "> - Kiro `trustedAgents: ['react-*']` (glob trust) has no Copilot equivalent; the "
        "explicit `agents:` allow-list above replaces it.\n"
    )
    note.append(
        "> - Kiro per-subagent/per-stage model overrides do not port. Each subagent uses the "
        "`model:` declared in its own `.agent.md`. The model table in the prompt above is "
        "descriptive only.\n"
    )
    note.append(
        "> - The `handoffs:` buttons above are a net-new Copilot capability (guided workflow) "
        "that Kiro's programmatic delegation did not surface. See MIGRATION-NOTES.md.\n"
    )
    body += "".join(note)

    OUT.write_text(frontmatter + body)
    print(f"  wrote {OUT.name}")
    print(f"  agents: {present}")
    print(f"  handoffs: {[a for a,_,_ in handoff_chain]}")
    if missing:
        print(f"  DROPPED missing subagents (flag in MIGRATION-NOTES): {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
