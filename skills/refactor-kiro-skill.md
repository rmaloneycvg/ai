---
name: refactor-kiro-skill
description: Use when refactoring, splitting, merging, or improving an existing Kiro skill file. Covers narrowing activation triggers, fixing overlap, adding missing schema elements (failure recovery, environment scope, rollback, idempotency), and splitting oversized skills. Also use when auditing skills for staleness or anti-patterns.
---

# Refactor a Kiro Skill

## Role & Tone

Act as a senior platform engineer specializing in agentic workflow design. Be precise about what changes and why. Prefer minimal diffs over rewrites — preserve working sections.

## Environment Scope

**write+validate** — Reads and rewrites skill files. Validates by checking schema completeness and running overlap detection against other skills. Does NOT execute any skill workflows.

## File Path Resolution

All paths are relative to `cwd` (current working directory). The Kiro directory structure:

```
<cwd>/
└── .kiro/
    ├── agents/           # Agent JSON configs referencing skills via skill:// URIs
    │   ├── dev.json
    │   ├── frontend.json
    │   └── infra.json
    ├── skills/           # Skill markdown files (this is where refactored files live)
    │   └── *.md
    ├── steering/         # Detailed steering documents referenced by skills
    │   └── **/*.md
    └── settings/
        └── mcp.json      # MCP server configs (update if skill renamed MCP tools)
```

**When updating references after rename/split/merge:**

1. Search `<cwd>/.kiro/agents/*.json` for `skill://` URIs containing the old filename
2. Update those URIs to the new filename(s)
3. Search `<cwd>/.kiro/skills/*.md` for References sections pointing to the old filename
4. Update those paths
5. Search `<cwd>/README.md` (project root) for mentions of the old skill name
6. Update or remove those mentions

**Never guess paths.** If `.kiro/` does not exist at `cwd`, check if it's symlinked from another location (`ls -la .kiro`). If it doesn't exist at all, ask the user where their Kiro config lives.

## Workflow

1. **Identify Target** — Confirm which skill file(s) to refactor. If ambiguous, ask user to specify.
2. **Read Target & Check State** — Read the full content of the target skill. Run `git status --porcelain` on the `.kiro/` directory. If the target skill or any agent configs have unstaged changes, WARN the user that a rollback might overwrite their manual work and require explicit permission to proceed.
3. **Bounded Overlap Check** — List skills/ directory (names only). Identify up to 3 potentially related skills by name. Read only those to understand boundaries.
4. **Diagnose Issues** — Assess the skill against the quality checklist (below). Report findings to user.
5. **Propose Changes** — Present a spec of what will change, what stays, and why. List affected files.
6. **Await Approval** — Do NOT modify files until user confirms the proposed changes.
7. **Implement** — Apply changes to the skill file(s). Minimal diffs preferred.
8. **Verify** — Run the quality checklist again on the result. If issues remain, enter failure loop.
9. **Update References** — If skill was renamed/split, update per File Path Resolution above: `<cwd>/.kiro/agents/*.json` (skill:// URIs), sibling skills (References sections), and `<cwd>/README.md`.

### Failure Recovery (max 3 retries)

8a. Identify which checklist item still fails
8b. Apply targeted fix
8c. Re-verify against checklist
8d. After 3 failures → present remaining issues to user, ask for guidance

### Rollback

If user rejects changes mid-implementation:

1. Restore the skill file at `<cwd>/.kiro/skills/<name>.md` to its pre-refactor state
2. If any `<cwd>/.kiro/agents/*.json` files were modified, revert those too
3. If any sibling `<cwd>/.kiro/skills/*.md` References sections were updated, revert those
4. Confirm revert with `git diff --stat` or report which files were restored

## Quality Checklist

Assess every skill against these criteria during diagnosis:

### Schema Completeness

| Element | Present? | Quality? |
|---------|----------|----------|
| `name` in frontmatter | ✓/✗ | kebab-case, matches filename |
| `description` in frontmatter | ✓/✗ | Hyper-specific, no false-positive triggers |
| Role & Tone | ✓/✗ | Only if needed — adds value vs default agent |
| Environment Scope | ✓/✗ | Declares write-only / write+validate / write+execute |
| Workflow | ✓/✗ | Phased with approval gate before implementation |
| Failure Recovery | ✓/✗ | Max retries defined, escalation path exists |
| Rollback | ✓/✗ | Tracks modified files, revert procedure documented |
| Guardrails | ✓/✗ | Absolute ("NEVER"), not aspirational ("try to") |
| References | ✓/✗ | Points to steering, not duplicating it inline |

### Behavioral Quality

- [ ] **Idempotent** — Re-running produces same result, no duplication
- [ ] **Bounded context** — Reads only relevant files, never entire directories
- [ ] **Non-overlapping trigger** — Description doesn't collide with other skills
- [ ] **Non-overlapping write targets** — No file conflicts with sibling skills
- [ ] **Under 200 lines** — If over, can it be split? (Meta-skills exempt at 300)
- [ ] **No stale references** — All referenced steering/skill files still exist
- [ ] **Guardrails enforceable** — Each guardrail maps to a concrete violation the agent could actually commit

## Refactoring Operations

### Narrow a Trigger

When a skill's description is too broad:

1. Identify which requests are misfiring to this skill
2. Add specificity: mention the exact technology, file type, or workflow stage
3. Add negative boundaries if needed: "NOT for... use [other-skill] instead"

Before:
```yaml
description: Use when working on the backend.
```

After:
```yaml
description: Use when adding a new REST API endpoint to a Node.js Express service with Zod validation. NOT for cron jobs (use backend-cron-feature) or database migrations.
```

### Split an Oversized Skill

When a skill exceeds 200 lines or covers multiple distinct workflows:

1. Identify the natural seams (usually at workflow boundaries)
2. Each split must have its own trigger, approval gate, and verification
3. Partition write targets — each new skill owns distinct files
4. Cross-reference between the splits in their References sections

### Merge Overlapping Skills

When two skills have colliding triggers or write targets:

1. Confirm with user which skill is the "primary"
2. Move unique content from the secondary into the primary
3. Delete the secondary file from `<cwd>/.kiro/skills/`
4. Search `<cwd>/.kiro/agents/*.json` for `skill://` URIs referencing the deleted file — update to the primary
5. Search `<cwd>/.kiro/skills/*.md` References sections for the deleted filename — update or remove
6. Update `<cwd>/README.md` if it lists skills
7. Verify the merged skill still passes the quality checklist

### Add Missing Schema Elements

When a skill is missing failure recovery, rollback, or environment scope:

1. Determine the skill's execution model from its workflow steps
2. Add Environment Scope based on whether it runs commands
3. Add Failure Recovery with appropriate max_retries for the domain
4. Add Rollback if the skill modifies more than one file

### Remove Stale Content

When a skill references dead code, removed files, or deprecated patterns:

1. Check each Reference path — does the file still exist?
2. Check guardrails — do they reference tools or commands that are no longer used?
3. Check workflow steps — do they mention files/dirs that were restructured?
4. Remove or update stale lines. Don't leave dead references.

## Clarification & Anti-Pattern Detection

This skill MUST ask for clarification when:

- The user says "refactor" but the skill has no obvious issues (ask what they want improved)
- A proposed merge would lose guardrails from one of the skills being merged
- Splitting would create two skills with ambiguous trigger boundaries
- The refactored description would now overlap with a different existing skill
- The user wants to change environment scope from write+validate to write+execute (security escalation)

## Guardrails

- NEVER delete a skill file without explicit user approval
- NEVER merge skills without confirming which is primary
- NEVER remove guardrails during refactoring unless user explicitly agrees
- NEVER widen a skill's scope (broader trigger) without overlap check
- NEVER escalate environment scope (write-only → write+execute) without user approval
- NEVER leave broken references in agent configs after renaming/splitting a skill
- NEVER rewrite a working skill from scratch — prefer minimal targeted edits

## Anti-Patterns in Refactoring

- ❌ Rewriting the entire file when only the description needs narrowing
- ❌ Splitting a 150-line skill just because it's "getting long" (it's under threshold)
- ❌ Merging skills that share a technology but have different workflows
- ❌ Removing Role & Tone because "it's optional" when it actually changes behavior
- ❌ Adding environment scope of write+execute to avoid telling users to run commands manually
- ❌ Reading all skill files to "understand the landscape" (use listing + targeted reads)

## References

- `skills/create-kiro-skill.md` — Schema definition, EARS format, idempotency principle, full quality standards
- `steering/orchestration/local.md` — Infrastructure context for infra-related skills
- `steering/preferences/stack/react/dependency-graph.md` — Frontend context for React-related skills
