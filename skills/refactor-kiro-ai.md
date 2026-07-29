---
name: refactor-kiro-ai
description: Use when editing, reorganizing, or adding to the AI workspace configuration — agent JSON files, skill files, MCP server setup, or steering document references. Enforces the progressive disclosure pattern (skills reference steering, agents load skills, steering is never in agent resources). NOT for creating new skills from scratch (use create-kiro-skill) or refactoring a single skill's content (use refactor-kiro-skill).
---

# Refactor Kiro AI Workspace

## Role & Tone

Act as a senior platform engineer maintaining an AI agent configuration system. Be precise about context budget impact. Challenge any change that puts detailed reference material directly into agent context. Default to progressive disclosure over eager loading.

## Environment Scope

**write+validate** — Reads and writes agent JSON configs, skill markdown files, and MCP server TypeScript files. Validates by checking JSON syntax, confirming skill frontmatter parses, and verifying MCP servers initialize. Does NOT execute agents or run Kiro CLI.

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

- **Orchestrator agents MAY load steering docs as `file://`** when the doc defines a pipeline contract or protocol that the orchestrator must enforce on every invocation (e.g., `frontend-pipeline-contract.md` in the frontend-orchestrator)
- **Sub-agents (under `agents/`) load their skill as `file://`, not `skill://`** — sub-agents are single-purpose pipeline workers that always execute their one skill; progressive disclosure adds no value when the agent's entire purpose IS that skill
- **Non-markdown file globs are acceptable as `file://`** — wildcards for code/config files (`*.yaml`, `*.yml`, `docker-compose*.yml`, `k8s/*.yaml`) are fine since they're small project artifacts, not heavy reference docs. The no-glob rule applies only to `.md` steering/skill files

## Workflow

1. **Identify Change Type** — Classify what's being edited: agent config, skill content, MCP server, or steering structure.
2. **Check Current State** — Read the relevant files. Confirm the change doesn't already exist.
3. **Validate Against Invariants** — Before making any change, verify it doesn't violate the architecture rules above. Specifically:
   - Is a steering doc being added as a resource? → REJECT. Add a skill reference instead.
   - Is a skill being added as `file://`? → REJECT. Use `skill://`.
   - Is a new MCP tool being added to an existing server instead of creating a focused one? → ASK if it should be independent.
   - Is a `file://` resource large or rarely needed? → SUGGEST moving to skill reference.
4. **Draft Change** — Make the minimal edit. For agent configs: valid JSON. For skills: valid frontmatter + schema.
5. **Present for Approval** — Show the diff. Explain context budget impact if relevant.
6. **Apply** — Write the files.
7. **Verify** — Re-read saved files. Confirm JSON parses, frontmatter is valid, no architecture violations.

### Failure Recovery (max 3 retries)

7a. Identify the issue (JSON syntax error, missing frontmatter field, architecture violation)
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

### Adding a skill to an agent

1. Confirm the skill exists in `skills/`
2. Add `"skill://../skills/<name>.md"` to the agent's `resources` array
3. Never add as `file://`

### Adding a new MCP tool

1. Create a new server file in `mcp/mcp-scripts/servers/<domain>.ts`
2. Keep it focused — one domain per server (git, io, postgres, etc.)
3. Add the server to relevant agent configs with absolute path
4. Use the server name as the key (e.g., `"git"`, `"io"`) — tools appear as `@<server>/<tool_name>`

### Removing context bloat

1. Check agent resources for any `file://` pointing to steering docs → convert to skill reference
2. Check for wildcard globs (`**/*.md`) → replace with explicit `skill://` refs
3. Check for large `file://` entries that could be on-demand → move to skill

## Guardrails

- NEVER add steering markdown files as `file://` or `skill://` resources in standard agents (orchestrators excepted — see Exceptions)
- NEVER use wildcard globs for `.md` files in agent resource arrays (non-md globs like `*.yaml` are fine)
- NEVER combine unrelated tools into a single MCP server
- NEVER add a resource without considering its context budget impact
- NEVER skip the architecture invariant check before applying changes
- NEVER hardcode relative paths in MCP server commands — use absolute paths
- NEVER create a monolithic agent that loads all skills — scope skills to agent purpose
- NEVER duplicate skill content that belongs in a steering doc — use References pointers
- NEVER use `skill://` for sub-agent resources — sub-agents under `agents/` use `file://` for their single skill

## References

- `skills/create-kiro-skill.md` — creating new skills (schema, frontmatter, workflow structure)
- `skills/refactor-kiro-skill.md` — editing existing skill content (narrowing triggers, fixing overlap)
- `steering/conventions/frontend-pipeline-contract.md` — example of detailed steering kept out of agent context
