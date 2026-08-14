---
inclusion: manual
---

# Kiro Skill Schema & Patterns

## Why This Exists

This document consolidates all skill authoring patterns, quality standards, and refactoring operations into a single authoritative reference. Both `kiro-create-skill` and `kiro-refactor-skill` reference this source of truth rather than duplicating schema definitions, quality checklists, and structural guidance inline.

---

## Skill File Structure

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

---

## Idempotent Scope Principle

Every skill must aspire to **idempotent scope** — running the skill multiple times on the same input should produce the same result without side effects or duplication. This means:

- A skill's output is deterministic given the same project state
- Re-running a skill doesn't create duplicate files, duplicate tests, or duplicate config entries
- The skill checks for existing artifacts before creating new ones
- If the target already exists in the expected state, the skill reports "already satisfied" and exits cleanly

**Test:** If a user accidentally triggers this skill twice in a row, does anything break or duplicate? If yes, add existence checks to the workflow.

```markdown
## Workflow (idempotent example)

1. **Check Existing State** — Does the target artifact already exist? If yes and it matches spec, report "already exists" and stop.
2. **Gather Context** — ...
```

---

## Activation Triggers

Write a `description` that is hyper-specific about activation conditions:

- ❌ `"helps with code"` — too vague, will misfire
- ❌ `"use for backend work"` — overlaps with multiple concerns
- ✅ `"Use when adding a new REST API endpoint to a Node.js Express service. Covers route definition, Zod validation, handler implementation, and integration test scaffolding."`
- ✅ `"Use when scaffolding a new containerized microservice for the Tilt local development environment. Covers Dockerfile, k8s manifest, Tiltfile entry, and nginx route."`

**Test:** Read the description and ask — "Could this accidentally match a request meant for a different skill?" If yes, narrow it.

---

## Role & Tone

```markdown
## Role & Tone

Act as a senior [domain] engineer. Be concise and technical.
Prefer working code over explanations. Ask clarifying questions
before making assumptions about [specific ambiguity area].
```

Only include if the skill needs behavior materially different from the default agent.

---

## Workflow Structure

Always enforce **phased execution** with human checkpoints, failure recovery, and clear environment boundaries:

```markdown
## Workflow

1. **Check Existing State** — Does the target artifact already exist? If yes and matches spec, report "already satisfied" and stop.
2. **Gather Context** — Read relevant existing code/config. Identify integration points. (Bounded: read only files directly relevant to the task, never entire directories.)
3. **Generate Spec** — Output requirements in EARS format (see below). List ALL files that will be created or modified.
4. **Await Approval** — Present the spec. Do NOT proceed until user confirms.
5. **Implement** — Execute the approved spec step by step. Write config/code files only.
6. **Verify** — Run validation (see Environment Boundaries below). If verification fails, enter Failure Recovery loop.
7. **Document** — Update README/docs if the change is user-facing.
```

### Failure Recovery Loop

Between Implement and Document, if verification fails:

```markdown
6a. **Diagnose** — Read the error output. Identify root cause.
6b. **Fix** — Apply a targeted fix to the failing artifact.
6c. **Re-verify** — Run verification again.
6d. **Iterate** — Repeat 6a–6c up to 3 times max.
6e. **Escalate** — If still failing after 3 attempts, present the error to the user with diagnosis and ask for guidance. Do NOT continue silently.
```

Skills must specify `max_retries` (default: 3) in their workflow. After exhausting retries, the agent stops and reports.

### Environment Boundaries

Every skill must declare its execution scope:

| Scope | Agent behavior |
|-------|---------------|
| **write-only** | Agent writes files (configs, code, manifests). Does NOT execute commands. Instructs user what to run. |
| **write+validate** | Agent writes files AND runs read-only validation commands (lint, typecheck, dry-run). No side effects. |
| **write+execute** | Agent writes files AND runs commands that produce side effects (build, deploy, migrate). Must list commands in spec for approval. |

Default scope is **write+validate**. If a skill needs write+execute (e.g., `terraform apply`, `tilt up`, `docker build`), it must:
- List every command in the spec phase
- Get explicit user approval for execution
- Set a timeout expectation (e.g., "docker build may take 2-5 minutes")
- Never block indefinitely — if a command hasn't returned in the expected time, report status and ask user

### Rollback on Rejection

If the user rejects a change mid-implementation (after some files are already modified):

```markdown
## Rollback Procedure

1. Track all files modified during this skill execution
2. If user says "stop", "cancel", or "revert":
   - Restore all modified files to their pre-skill state (use git checkout or cached originals)
   - Report which files were reverted
3. If only SOME changes are rejected:
   - Revert only the rejected files
   - Re-run verification on the remaining changes
   - If remaining changes are broken without the reverted ones, revert everything
```

A skill in a partially-applied broken state is worse than no change at all.

### EARS Requirement Format

Use for spec outputs:

```
WHEN <trigger condition>
THE SYSTEM SHALL <expected behavior>
SO THAT <value delivered>
```

Example:
```
WHEN a POST request is received at /api/widgets with a valid body
THE SYSTEM SHALL create a widget record and return 201 with the created resource
SO THAT clients can programmatically create widgets
```

---

## Guardrails

```markdown
## Guardrails

- NEVER begin writing code until the spec is explicitly approved
- NEVER modify files outside the scope defined in the spec
- NEVER skip test creation — every new feature has at least one test
- NEVER introduce a new dependency without stating it in the spec
- NEVER overwrite existing tests without explaining why
```

Add domain-specific guardrails based on what the skill touches:
- Infrastructure skills: "NEVER apply terraform without showing plan output first"
- Database skills: "NEVER run destructive migrations without backup confirmation"
- Auth skills: "NEVER weaken security constraints without explicit approval"
- All skills: "NEVER create artifacts without first checking if they already exist"
- All skills: "NEVER proceed if semantic overlap with an existing skill is detected — ask for clarification"

---

## References Section

```markdown
## References

- `steering/path/to/relevant.md` — detailed patterns for [topic]
- `skills/related-skill.md` — companion skill for [adjacent workflow]
```

Only reference files that provide context the skill's own content doesn't cover.

---

## Quality Checklist

Assess every skill against these criteria:

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

---

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

---

## Overlap Detection

Before saving a new skill or widening an existing skill's scope, check for conflicts using this bounded approach:

### Overlap Audit Checklist

1. **List existing skill filenames** — `ls skills/` (names only, don't read contents)
2. **Identify candidates** — Pick up to 3 files whose names suggest overlap with the proposed skill
3. **Read only those candidates** — Compare descriptions and write targets
4. **Check steering files** — Is this workflow already covered by a steering doc loaded at startup?
5. **Check agent resources** — Will this skill be loaded alongside a conflicting one?
6. **Test activation** — Mentally simulate 5 user prompts. Does the right skill activate each time?

### Resolving Overlap

| Problem | Fix |
|---------|-----|
| Two skills with similar descriptions | Narrow both descriptions to non-overlapping scopes |
| Skill duplicates steering content | Remove from skill, add pointer to steering |
| Skill loads for wrong requests | Make description more specific, add negative conditions |
| Multiple skills modify same files | Partition file access or merge into one skill |

### Clarification Prompts

When overlap or ambiguity is detected, the skill MUST ask for clarification. Example prompts:

- "The proposed skill 'add-api-route' overlaps with `backend-rest-api-feature.md` which already covers REST endpoint creation. Should this be merged into that skill, or does it cover a distinct scope? If distinct, what differentiates it?"
- "This skill would write to `Tiltfile` and `deploy/`, which `backend-cron-feature.md` also targets. Should we partition file ownership or enforce serial execution?"
- "The workflow doesn't include an existence check — if the user runs this twice, it would create duplicate entries in the Tiltfile. Adding an idempotency gate to step 1."

**Clarification is required when:**

- The proposed skill's description is semantically close to an existing skill's description
- The proposed workflow overlaps with an existing skill's file write targets
- The proposed scope violates idempotency (e.g., appends without checking existing state)
- The user's request is ambiguous about whether this should be a new skill or an extension of an existing one
- The proposed guardrails conflict with guardrails in related skills

**Never read all skill files into context.** Directory listing + targeted reads keeps the token budget bounded.

---

## Anti-Patterns

- ❌ Skill that tries to do everything (scaffold + test + deploy + document)
- ❌ Description that matches common prompts unrelated to the workflow
- ❌ Workflow that jumps from idea to code without spec/approval gate
- ❌ Loading broad steering docs inline instead of using References pointers
- ❌ Guardrails that are aspirational ("try to...") instead of absolute ("NEVER...")
- ❌ Multiple skills with overlapping write targets (file collisions in parallel execution)
- ❌ Non-idempotent workflows (appending without existence checks, creating without checking for prior runs)
- ❌ Proceeding without clarification when overlap with existing skills is detected
- ❌ Reading entire directories into context ("read ALL files in X") — use listing + targeted reads
- ❌ Workflow without a failure recovery loop (verify fails → agent gives up or loops forever)
- ❌ Executing long-running commands without timeout expectations or user status updates
- ❌ No rollback procedure for partial failures (3 files modified, 4th fails → broken state persists)
- ❌ Ambiguous environment scope (unclear if agent writes files, runs commands, or both)
- ❌ Rewriting the entire file when only the description needs narrowing
- ❌ Splitting a 150-line skill just because it's "getting long" (it's under threshold)
- ❌ Merging skills that share a technology but have different workflows
- ❌ Removing Role & Tone because "it's optional" when it actually changes behavior
- ❌ Adding environment scope of write+execute to avoid telling users to run commands manually
- ❌ Reading all skill files to "understand the landscape" (use listing + targeted reads)

---

## Example: Complete Skill File

```markdown
---
name: add-tilt-service
description: Use when adding a new containerized service to the Tilt local development environment. Covers Dockerfile creation, k8s manifest, Tiltfile entry, nginx route configuration, and live_update setup.
---

# Add Tilt Service

## Role & Tone

Act as a senior platform engineer. Be concise. Prefer working configs over explanations.

## Environment Scope

**write+validate** — Writes config files (Dockerfile, manifests, Tiltfile entries). Runs `tilt ci --only=<service>` for validation (dry-run, no deploy). Does NOT run `tilt up` — instructs user to do so.

## Workflow

1. **Check Existing State** — Read Tiltfile. If service name already exists, report "already configured" and stop.
2. **Gather Context** — Read Tiltfile, nginx.conf, deploy/ directory. Note existing resource groups and port allocations.
3. **Generate Spec** — EARS requirements for the new service: ports, dependencies, resource group, live_update paths. List all files to create/modify.
4. **Await Approval** — Present spec. Wait for user confirmation.
5. **Implement** — Create Dockerfile, k8s manifest, add to Tiltfile, add nginx upstream/location.
6. **Verify** — Run `tilt ci --only=<service>` (expected: <30s). If fails, enter failure loop.
7. **Document** — Update project README architecture diagram.

### Failure Recovery (max 3 retries)

6a. Read tilt ci error output → identify misconfiguration
6b. Fix the specific file (usually Dockerfile or k8s manifest)
6c. Re-run `tilt ci --only=<service>`
6d. After 3 failures → report error + diagnosis to user, ask for guidance

### Rollback

If user cancels mid-implementation: revert Tiltfile, remove created Dockerfile and manifests, remove nginx route entry. Verify Tiltfile still loads cleanly after revert.

## Guardrails

- NEVER modify existing service configs without stating the change in the spec
- NEVER expose a service port publicly without explicit approval
- NEVER skip live_update configuration — all services must support hot reload
- NEVER add a service without a health check endpoint
- NEVER run `tilt up` — that's user-initiated, only validate with `tilt ci`

## References

- `steering/orchestration/local-dev.md` — Tilt topology, nginx patterns, Docker multi-stage builds
- `skills/general-documentation.md` — README update after adding service
```

---

## Context Budget Tips

- Keep skill files under 200 lines — they're loaded into context on demand
- Put detailed patterns in steering docs, reference them from skills
- Use `skill://` URI (not `file://`) so only metadata loads at startup
- If a skill exceeds 300 lines, split it into two skills with narrower triggers
- Exception: meta-skills (like kiro-create-skill) that teach skill creation may be larger since they're referenced infrequently and contain the full schema
