---
name: kiro-workflow-guidelines
description: Use when making decisions about Kiro AI workspace architecture — where to place steering docs vs skills, how agents load context (progressive disclosure), MCP server organization, and resource budget management. Also use when auditing the workspace for context bloat or architecture violations. NOT for creating/editing individual skills (use kiro-create-skill or kiro-refactor-skill), agents (use kiro-create-agent or kiro-refactor-agent), or orchestration pipelines (use kiro-create-orchestration or kiro-refactor-orchestration).
---

# Kiro Workflow Guidelines

## Role & Tone

Act as a senior platform engineer maintaining an AI agent configuration system. Be precise about context budget impact. Challenge any change that puts detailed reference material directly into agent context. Default to progressive disclosure over eager loading.

## Environment Scope

**write+validate** — Reads and validates workspace structure. May write steering docs or reorganize file placement. Validates by checking JSON syntax, confirming skill frontmatter parses, and verifying architecture invariants. Does NOT execute agents or run Kiro CLI.

## Architecture Invariants

These are the hard rules of this workspace. Every edit must preserve them.

### Context Loading Hierarchy

```
Agent startup:
  1. skill:// resources → metadata only (name + description)
  2. file:// resources  → full content always in context

On-demand (progressive):
  3. Skill triggered    → full skill content loaded
  4. Skill references steering → agent reads steering doc via read tool
```

### What Goes Where

| Layer | Contains | Loaded |
|-------|----------|--------|
| **Agent JSON** (`agents/*.json`) | Identity, tools, MCP servers, `skill://` refs, small project files (`file://`) | Always |
| **Skills** (`skills/*.md`) | Workflow steps, guardrails, pointers to steering docs | On demand |
| **Steering** (`steering/**/*.md`) | Detailed patterns, conventions, tech stack rules | Only when a skill or agent reads it |

### Rules

- **Steering docs NEVER appear as `file://` resources in agents** — they are too large for always-on context
- **Steering docs NEVER appear as `skill://` resources** — they lack frontmatter and are too detailed to be skills
- **Skills reference steering docs** in a `## References` section with relative paths
- **Agents load skills via `skill://`** — only metadata (name + description) consumes context at startup
- **`file://` in agents is reserved for** small project files the agent always needs (package.json, tsconfig.json, Tiltfile, etc.)
- **MCP servers are independent processes** — one server per tool domain (git, io, postgres), not one monolith
- **MCP servers use absolute paths** in agent configs so they work from any project directory

### Exceptions

- **Orchestrator agents MAY load steering docs as `file://`** when the doc defines a pipeline contract or protocol that the orchestrator must enforce on every invocation
- **Sub-agents (under `agents/`) load their skill as `file://`, not `skill://`** — sub-agents are single-purpose pipeline workers that always execute their one skill
- **Non-markdown file globs are acceptable as `file://`** — wildcards for code/config files (`*.yaml`, `k8s/*.yaml`) are fine since they're small project artifacts

## Workflow

1. **Identify Change Type** — Classify what's being edited: resource placement, MCP server structure, steering organization, or context budget.
2. **Check Current State** — Read the relevant files. Confirm the change doesn't already exist.
3. **Validate Against Invariants** — Before making any change, verify it doesn't violate the architecture rules above. Specifically:
   - Is a steering doc being added as a resource? → REJECT. Add a skill reference instead.
   - Is a skill being added as `file://`? → REJECT. Use `skill://`.
   - Is a new MCP tool being added to an existing server instead of creating a focused one? → ASK if it should be independent.
   - Is a `file://` resource large or rarely needed? → SUGGEST moving to skill reference.
4. **Draft Change** — Make the minimal edit.
5. **Present for Approval** — Show the diff. Explain context budget impact if relevant.
6. **Apply** — Write the files.
7. **Verify** — Re-read saved files. Confirm no architecture violations.

### Failure Recovery (max 3 retries)

7a. Identify the issue (architecture violation, broken reference)
7b. Fix the specific problem
7c. Re-verify
7d. After 3 failures → show error to user, ask for guidance

### Rollback

If user rejects: revert all modified files to pre-edit state. Confirm with file listing.

## Common Operations

### Adding a steering doc to the system

1. Write the doc in `steering/` with appropriate subdirectory
2. Find or create a skill that covers the topic
3. Add a `## References` entry in that skill pointing to the new steering doc
4. Do NOT add it to any agent's resources

### Removing context bloat

1. Check agent resources for any `file://` pointing to steering docs → convert to skill reference
2. Check for wildcard globs (`**/*.md`) → replace with explicit `skill://` refs
3. Check for large `file://` entries that could be on-demand → move to skill

### Reorganizing steering docs

1. Move the file to the appropriate subdirectory
2. Update all `## References` sections in skills that point to the old path
3. Verify no agent configs reference it directly

## Guardrails

- NEVER add steering markdown files as `file://` or `skill://` resources in standard agents (orchestrators excepted — see Exceptions)
- NEVER use wildcard globs for `.md` files in agent resource arrays
- NEVER combine unrelated tools into a single MCP server
- NEVER add a resource without considering its context budget impact
- NEVER skip the architecture invariant check before applying changes
- NEVER hardcode relative paths in MCP server commands — use absolute paths
- NEVER duplicate skill content that belongs in a steering doc — use References pointers

## References

- `steering/conventions/skill-schema.md` — Skill schema structure (for validating skill resources)
- `steering/orchestration/pipeline-contract.md` — Pipeline I/O contract for orchestrator sub-agents
