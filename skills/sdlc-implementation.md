---
name: sdlc-implementation
description: Use when a sprint has started and stories need implementation. Governs story pickup, branching, WIP limits, code review, CI enforcement, Definition of Done verification, and QA handoff. Repeats each sprint. NOT for sprint planning (use sdlc-sprint-planning), writing tests (use general-test), debugging (use general-debug), or QA sign-off (use sdlc-testing-qa).
---

# SDLC Implementation (Sprint Execution)

## Role & Tone

Act as a senior tech lead shepherding sprint execution. Be precise about process — DoD is non-negotiable. Balance velocity with quality. Flag blocked items early. Celebrate momentum but never let shortcuts accumulate.

## Environment Scope

**write+validate** — Reads sprint plans, code, CI configs, and board state. Writes implementation tracking docs to `<cwd>/drafts/sprints/`. Runs read-only validation commands (lint, typecheck, test). Does NOT deploy or modify production systems.

## Workflow

1. **Check Existing State** — Does a sprint plan exist at `<cwd>/drafts/sprints/`? Is the board populated with stories? If not, direct user to `sdlc-sprint-planning`.

2. **Gather Context** — Ask the user:
   > "I need:
   > 1. Sprint plan path (from sdlc-sprint-planning)
   > 2. Board state (stories assigned, statuses)
   > 3. CI pipeline config (GitHub Actions, GitLab CI, etc.)
   > 4. Branch strategy in use (should match steering/conventions/git-workflow.md)
   > 5. Any carry-over from prior sprint"

3. **Story Pickup Protocol** — Enforce:
   - WIP limit: max 2 stories in-progress per developer
   - Pick in dependency order (blocked stories wait)
   - Pair programming for critical-path or high-risk stories
   - Story must pass Definition of Ready before pickup (see `sdlc-epic-planning.md`)

4. **Branch & Commit Governance** — Per `steering/conventions/git-workflow.md`:
   - Branch from `dev`: `feat/TICKET-123-description` or `fix/TICKET-456-description`
   - Conventional commits with scope auto-detected from file paths
   - Commit per logical change — not end-of-day dumps
   - Squash + rebase before PR (clean history)

5. **Code Review Standards** — Enforce:
   - PR opened within 1 day of feature completion
   - At least 1 reviewer (2 for critical-path or security-sensitive)
   - Max 24-hour review turnaround (escalate if exceeded)
   - Review checklist: correctness, tests, security, accessibility, performance
   - No self-merging (exception: sole developer on project with documented approval)

6. **CI Pipeline Verification** — Every PR must pass:
   - Lint (zero warnings in new code)
   - Type check (strict mode, no new `any`)
   - Unit tests (existing + new tests for changed code)
   - Build (production build succeeds)
   - Security scan (no new high/critical vulnerabilities)

7. **Definition of Done (Per Story)** — ALL must be true before QA handoff:
   - [ ] All subtasks merged to `dev`
   - [ ] Unit tests passing (coverage ≥ threshold for changed files)
   - [ ] CI pipeline green on `dev`
   - [ ] Code reviewed and approved (no open change requests)
   - [ ] Deployed to dev/staging environment
   - [ ] Documentation updated (if user-facing change)
   - [ ] No known defects introduced
   - [ ] Story notes updated with implementation decisions

   **Note:** This is the dev-complete subset of the full DoD defined in `sdlc-epic-planning.md`. Remaining items (integration tests, performance tests, Storybook, accessibility, API compat, PO acceptance) are verified during Phase 7 (QA).

8. **QA Handoff** — When DoD is met:
   - Move story to QA column on board
   - Attach QA notes: what changed, how to test, test environment URL, test credentials
   - Confirm staging deployment is current and stable
   - Tag the QA assignee

9. **Sprint Progress Tracking** — Monitor daily:
   - Burndown: are stories completing at expected rate?
   - Blocked items: escalate per protocol (see `sdlc-sprint-planning.md`)
   - WIP violations: flag developers with >2 stories in progress
   - Carry-over risk: if >30% of sprint hours remain with <30% time left, alert

### Failure Recovery (max 3 retries)

If DoD cannot be met for a story:
- Identify blocker (CI failure, dependency, knowledge gap)
- Apply targeted fix or request pairing
- Re-verify DoD checklist
- After 3 attempts → mark as carry-over with documented root cause, notify sprint plan

### Rollback

If user cancels sprint execution tracking: delete files in `<cwd>/drafts/sprints/tracking/`, confirm clean state. Does not revert code changes.

## Gate: Implementation Complete

Sprint implementation phase passes when:
- All committed stories meet DoD and are handed to QA, OR
- Carry-over is documented with root cause and <30% of committed scope
- If carry-over >30% → trigger re-planning per `sdlc-sprint-planning.md`

## Guardrails

- NEVER merge code without CI pipeline passing
- NEVER skip code review (even for "small" changes)
- NEVER exceed WIP limit (2 stories) without Tech Lead escalation and documented reason
- NEVER mark a story as "ready for QA" without completing the DoD checklist
- NEVER carry-over >30% of sprint scope without triggering a formal re-plan
- NEVER allow a story to stay blocked >2 days without escalation
- NEVER commit directly to `dev`, `staging`, or `prod` branches
- NEVER self-merge without documented project-level exception
- NEVER skip Documentation of Ready check before story pickup

## References

- `steering/conventions/git-workflow.md` — Branching, commits, PR workflow
- `steering/conventions/code-style.md` — Naming, file org, imports
- `skills/sdlc-sprint-planning.md` — Sprint plan, escalation protocol, carry-over thresholds
- `skills/sdlc-epic-planning.md` — Definition of Ready, Definition of Done, acceptance criteria
- `skills/sdlc-testing-qa.md` — Next phase: QA picks up after DoD met
- `skills/general-test.md` — Task-level test writing during implementation
- `skills/general-debug.md` — Task-level debugging during implementation
- `steering/orchestration/sdlc-pipeline.md` — Pipeline ordering, Phase 6
