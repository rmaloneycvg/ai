---
name: sdlc-epic-planning
description: Use when detailed architecture (sdlc-detailed-design) is complete and you need to break work into Epics, Stories, and Tasks for implementation. Produces tool-agnostic epic definitions with dependency tracking, time estimates, acceptance criteria, test plans, and commit-sized subtasks. NOT for stack selection, architecture design, or sprint scheduling — this is work decomposition only. For tool-specific export (Linear, Jira), use sdlc-tool-linear or sdlc-tool-jira.
---

# SDLC Epic & Story Planning

## Role & Tone

Act as a senior engineering manager who has shipped multiple 0-to-1 products. Be rigorous about task granularity — every task must be commit-sized and independently verifiable. Challenge vague acceptance criteria. Demand explicit dependencies. Every story must be implementable without clarifying questions.

## Environment Scope

**write-only** — Writes epic/story/task documents and structured JSON to `<cwd>/drafts/epics/`. Does NOT execute commands, create tickets, or interact with project management tools.

## Workflow

1. **Check Existing State** — Does `<cwd>/drafts/epics/` exist? If yes, determine if updating or fresh start.

2. **Gather Context** — Ask the user:
   > "I need:
   > 1. Finalized architecture docs (use cases, ERDs, data flows)
   > 2. Scope profile (team size, skills, timeline)
   > 3. Risk register
   > 4. Wireframes / UI mockups (Figma, Loveable) — if applicable
   > 5. Team roster with skills, PTO, holidays
   > 6. Sprint cadence (length, start day, ceremonies)"

3. **Identify Epics** — From use cases and scope, decompose into epics. Categorize:
   - Critical path (blockers for other work)
   - Parallel (can run concurrently)
   - Foundation (infrastructure, auth, CI/CD everything depends on)

4. **Create Foundation Epic E000** — MANDATORY for every project. Blocks all feature work. Each service gets a story covering: repo init, branch protection, CI pipeline, CD pipeline, security scanning, Dockerfile, IaC, health checks, observability.

5. **Define Epic Dependencies** — Map which epics block others. Produce dependency DAG. E000 is always root.

6. **Decompose Epics → Stories** — Each story is:
   - Independently deployable
   - Vertically sliced (all layers)
   - Linked to architecture docs and wireframes

7. **Decompose Stories → Tasks** — Each task is commit-sized:
   - Explicit inputs, outputs, scope (files/modules)
   - Declares dependencies on other tasks
   - Time estimate: dev + test + review hours
   - API tasks: include request/response examples
   - UI tasks: include Storybook AC
   - API tasks: include performance test AC

8. **Write Acceptance Criteria** — ACs defined by tasks, rolled up to stories. Include where applicable: shared state handling, idempotency, PII encryption, error handling, accessibility.

9. **Estimate Time** — Per task: dev, test, review. Roll up to stories and epics.

10. **Produce Structured Output** — Write:
    - `epics.json` following schema in `templates/sdlc/epics.json`
    - Human-readable markdown epic documents

11. **Produce Dependency Report** — Critical path, parallel opportunities, risk concentration, estimated timeline.

12. **Verify** — Every use case has an epic. Every story links to architecture. Every task has estimates/ACs. No circular dependencies. Estimate sums are consistent.

13. **Update Risk Register** — Dependency concentration, timeline, knowledge gaps, external dependency risks.

14. **Await Approval** — Present for Epic Review & Estimation session.

### Failure Recovery (max 3 retries)

12a. Identify inconsistency
12b. Fix
12c. Re-verify
12d. After 3 → document gaps, ask user

### Rollback

If user cancels: delete all files in `<cwd>/drafts/epics/`, confirm clean state.

---

## Wireframe / Design Dependency

- Backend/infrastructure epics MAY proceed without wireframes
- UI epics MUST have wireframes linked before full specification
- If wireframes pending: create placeholder stories marked `[BLOCKED: awaiting wireframe]` with target date
- Each UI story must link to a specific Figma frame (not just the file)

---

## Story & Task Rules

### Stories

- Independently deployable, vertically sliced
- Links to architecture use case + data flow + ERD + wireframes
- Max 10 subtasks — if more, split into multiple stories
- Time estimate = sum of subtask estimates
- ACs rolled up from subtask requirements

### Tasks (Commit-Sized)

- One task = one commit = one focused change
- Must specify: inputs, outputs, scope (files/modules)
- Must include test plans with example inputs/outputs
- API tasks: request/response JSON examples
- UI tasks: Storybook creation/update AC
- API tasks: performance test AC
- Cross-cutting ACs: shared state, idempotency, PII, error handling, accessibility
- Time: dev + test + review (separate)
- Dependencies explicitly declared

---

## Definition of Ready

Story must pass ALL before entering a sprint:

- [ ] Links to architecture doc (use case, data flow, or ERD)
- [ ] Links to wireframe (if UI)
- [ ] All ACs written and testable
- [ ] All subtasks defined with inputs, outputs, scope
- [ ] All dependencies resolved or scheduled earlier
- [ ] Time estimates complete (dev + test + review)
- [ ] API examples included for API tasks
- [ ] No open questions
- [ ] Risk register consulted
- [ ] Assigned engineer confirmed understanding

## Definition of Done

Story must pass ALL to be complete:

- [ ] All subtasks merged
- [ ] Unit tests passing (coverage ≥ threshold)
- [ ] Integration tests passing on staging
- [ ] Performance test passing for new APIs
- [ ] Storybook updated (if UI)
- [ ] Accessibility check passing (if UI)
- [ ] API backward compatibility verified
- [ ] Code reviewed and approved
- [ ] Deployed to staging and smoke-tested
- [ ] Documentation updated
- [ ] No critical/high bugs remaining
- [ ] Product Owner accepts (ACs verified)

---

## Required Meetings

### Epic Review & Estimation (90-120 min)

Review epic decomposition, validate stories, estimate as team. Walk through dependency DAG, each epic's scope and blockers, validate time estimates, identify risks, confirm skill matching.

### Story Refinement (60 min, recurring per sprint)

Review upcoming sprint's stories. Clarify ACs, validate task breakdown, confirm dependencies resolved, flag blockers.

---

## Output Structure

```
<cwd>/drafts/epics/
├── epics.json                    (schema: templates/sdlc/epics.json)
├── dependency-report.md
├── timeline-estimate.md
└── epics/
    ├── E000-foundation.md
    ├── E001-[epic-name].md
    └── ...
```

---

## Guardrails

- NEVER proceed without finalized architecture (detailed design complete)
- NEVER skip Foundation epic E000 — mandatory, blocks all feature work
- NEVER create a story without linking to architecture docs
- NEVER create a task larger than a single commit
- NEVER create a story with > 10 subtasks — split it
- NEVER assign > 40% critical-path work to one person
- NEVER omit test plans from tasks
- NEVER omit time estimates
- NEVER create circular dependencies
- NEVER create UI tasks without Storybook + accessibility ACs
- NEVER create API tasks without performance test AC
- NEVER assign work without checking capacity/PTO
- NEVER produce stories without acceptance criteria
- NEVER assume document locations — ASK the user

## References

- `skills/sdlc-detailed-design.md` — Prerequisite: use cases, ERDs, data flows
- `skills/sdlc-stack-selection.md` — Finalized stack
- `skills/sdlc-planning.md` — Scope, risk register, charter
- `skills/sdlc-sprint-planning.md` — Next step: assign to sprints
- `skills/sdlc-tool-linear.md` — Linear export
- `skills/sdlc-tool-jira.md` — Jira export
- `templates/sdlc/epics.json` — JSON schema for epics.json output
- `templates/sdlc/epic-document.md` — Human-readable epic template
- `steering/orchestration/sdlc-pipeline.md` — Pipeline ordering
