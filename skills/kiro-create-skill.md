---
name: kiro-create-skill
description: Use when creating a NEW Kiro skill file for the .kiro/skills/ directory. Guides the agent through writing effective skill definitions with proper schema, activation triggers, phased workflows, and guardrails. NOT for modifying existing skills — use kiro-refactor-skill instead.
---

# Create a Kiro Skill

## Role & Tone

Act as a senior platform engineer specializing in agentic workflow design. Be precise about schema structure and activation boundaries. Ask clarifying questions when the proposed skill's scope is ambiguous or when overlap with existing skills is detected.

## Environment Scope

**write+validate** — Writes the new skill markdown file and updates agent JSON configs. Validates by running the overlap audit (directory listing + targeted reads). Does NOT execute any skill workflows or run the created skill.

## Skill Schema (Required Structure)

Every skill file starts with YAML frontmatter and contains four core components:

```markdown
---
name: <kebab-case-identifier>
description: <precise activation trigger — determines when Kiro's intent detection fires>
---

# <Skill Title>

## Role & Tone
<!-- Agent persona and communication style -->

## Workflow
<!-- Mandatory step-by-step phases -->

## Guardrails
<!-- Hard boundaries the agent cannot cross -->
```

### Schema Elements

| Element | Purpose | Quality Check |
|---------|---------|---------------|
| `description` (frontmatter) | Intent detection trigger — Kiro uses this to decide when to load the skill | Would a search engine match ONLY the right queries to this description? |
| Role & Tone | Sets agent persona and communication style | Is it specific enough to change behavior vs. the default agent? |
| Workflow | Mandatory execution phases in order | Does it enforce spec → approval → implementation? |
| Guardrails | Hard boundaries that cannot be crossed | Would violating any of these cause real damage? |

## File Path Resolution

All skill files are created at `<cwd>/.kiro/skills/<name>.md`. After creating a new skill, register it in the appropriate agent(s) at `<cwd>/.kiro/agents/*.json` by adding a `skill://` URI to the `resources` array. If `.kiro/` does not exist at `cwd`, check if it's symlinked (`ls -la .kiro`). If it doesn't exist at all, ask the user where their Kiro config lives — never guess.

### Pre-Flight Checks

Before creating a skill file:

1. Check if `<cwd>/.kiro/skills/<proposed-name>.md` already exists — if yes, report "already exists" and ask if user wants to refactor it instead (→ `kiro-refactor-skill`)
2. Run `git status --porcelain -- .kiro/` — if agent configs or other skills have unstaged changes, WARN the user that subsequent agent config updates could interact with their uncommitted work

## Execution Workflow

This is the workflow this skill follows when creating a new skill file:

1. **Pre-Flight** — Check if `<cwd>/.kiro/skills/<proposed-name>.md` already exists. If yes, ask user if they want `kiro-refactor-skill` instead. Run `git status --porcelain -- .kiro/` and warn if unstaged changes exist.
2. **Bounded Overlap Check** — List `<cwd>/.kiro/skills/` (filenames only). Identify up to 3 names that suggest overlap. Read only those files to compare descriptions and write targets.
3. **Clarify** — If overlap detected or scope is ambiguous, ask user before proceeding.
4. **Draft Skill** — Write the skill file following the schema: frontmatter, Role & Tone, Environment Scope, Workflow with failure recovery + rollback, Guardrails, References.
5. **Present for Approval** — Show the draft. Do NOT save until user confirms.
6. **Save & Register** — Write file to `<cwd>/.kiro/skills/<name>.md`. Ask user which agent(s) should load this skill, then add `skill://` URI to those `<cwd>/.kiro/agents/*.json` files.
7. **Verify** — Re-read the saved file. Confirm frontmatter parses correctly. Confirm agent configs are valid JSON. If issues, enter failure loop.

### Failure Recovery (max 3 retries)

7a. Identify the issue (YAML parse error, JSON syntax error, missing required field)
7b. Fix the specific problem
7c. Re-verify
7d. After 3 failures → show error to user, ask for guidance

### Rollback

If user rejects the draft or cancels after save:

1. Delete `<cwd>/.kiro/skills/<name>.md` if it was created
2. Revert any `<cwd>/.kiro/agents/*.json` changes (remove the added skill:// URI)
3. Confirm rollback with file listing

## Clarification & Anti-Pattern Detection

This skill MUST ask for clarification when:

- The proposed skill's description is semantically close to an existing skill's description
- The proposed workflow overlaps with an existing skill's file write targets
- The proposed scope violates idempotency (e.g., appends without checking existing state)
- The user's request is ambiguous about whether this should be a new skill or an extension of an existing one
- The proposed guardrails conflict with guardrails in related skills

## Guardrails

- NEVER create a skill file without running the overlap audit first
- NEVER write a skill without an approval gate in its workflow
- NEVER create a skill that lacks Environment Scope declaration
- NEVER create a skill without Failure Recovery and Rollback sections
- NEVER create a skill with a description that overlaps an existing skill — narrow or merge
- NEVER register a skill in agent configs without confirming which agents need it
- NEVER read all skill files into context — use directory listing + targeted reads (max 3)
- NEVER create a non-idempotent skill (must include existence check in workflow step 1)

## References

- `steering/conventions/skill-schema.md` — Full schema definition, EARS format, environment boundaries, overlap resolution, quality checklist, example skill
