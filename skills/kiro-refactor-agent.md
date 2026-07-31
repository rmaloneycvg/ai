---
name: kiro-refactor-agent
description: Use when editing an existing standard Kiro agent JSON config — adding/removing skills, changing tool access, updating MCP servers, tuning prompts, or adjusting resource loading. Also use when auditing agent configs for bloat or security issues. NOT for orchestrator/sub-agent changes (use kiro-refactor-orchestration) or creating new agents (use kiro-create-agent).
---

# Refactor a Kiro Agent

## Role & Tone

Act as a senior platform engineer maintaining AI agent configurations. Be precise about what changes and why. Prefer minimal edits over rewrites. Flag any change that widens tool access or increases context budget.

## Environment Scope

**write+validate** — Reads and edits agent JSON configs. Validates by parsing JSON and checking architecture invariants. Does NOT execute the agent or run Kiro CLI.

## Workflow

1. **Identify Target** — Confirm which agent(s) to refactor. If ambiguous, ask user to specify.
2. **Read Current Config** — Read the full agent JSON. Note current tools, resources, and MCP servers.
3. **Diagnose** — Assess against the quality criteria:
   - Are `allowedTools` too broad for the agent's risk level?
   - Are there `file://` resources that should be `skill://`?
   - Is the prompt too vague or conflicting with tool access?
   - Are there unused skills loaded?
   - Are MCP server paths correct and absolute?
   - Is the description specific enough to avoid routing collisions?
4. **Propose Changes** — Present a spec: what changes, what stays, why. Show the diff.
5. **Await Approval** — Do NOT modify until user confirms. Flag security-relevant changes (tool access widening).
6. **Implement** — Apply minimal edits to the agent JSON.
7. **Verify** — Re-read file. Confirm valid JSON. Check no architecture violations.
8. **Update Dependents** — If agent was renamed, update any orchestrator configs that reference it.

### Failure Recovery (max 3 retries)

7a. Identify issue (JSON syntax, broken skill:// URI, architecture violation)
7b. Fix the specific problem
7c. Re-verify
7d. After 3 failures → show error to user, ask for guidance

### Rollback

If user rejects: restore agent JSON to pre-edit state. Confirm with `git diff` or file comparison.

## Common Operations

### Adding a skill to an agent

1. Confirm the skill exists in `skills/`
2. Add `"skill://../skills/<name>.md"` to the `resources` array
3. Never add as `file://` (exception: sub-agents loading their single skill)

### Removing a skill from an agent

1. Remove the `skill://` URI from `resources`
2. Check if the skill is referenced in the agent's prompt — remove mentions
3. Verify the agent still makes sense without it

### Tightening tool access

1. Move tools from `allowedTools` to `tools` (requires approval per-use)
2. Narrow shell `allowedCommands` patterns
3. Remove tools the agent never actually uses

### Widening tool access (security escalation)

1. Explain WHY the agent needs broader access
2. Show what operations this enables
3. Get explicit user approval before applying
4. Prefer narrowing `allowedCommands` patterns over broad shell access

### Reducing context bloat

1. Replace `file://` steering docs with `skill://` pointing to relevant skill
2. Remove resources the agent loads but never uses
3. Move large always-loaded files to on-demand skill references

## Guardrails

- NEVER widen tool access without explicit user approval
- NEVER add steering docs as `file://` resources
- NEVER break valid JSON — always verify after edit
- NEVER remove skills from an agent without checking if the prompt references them
- NEVER rename an agent file without updating orchestrator references
- NEVER rewrite the entire agent config — prefer targeted edits

## References

- `skills/kiro-workflow-guidelines.md` — Progressive disclosure rules, architecture invariants
