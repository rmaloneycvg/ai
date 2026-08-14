---
inclusion: manual
---

# SDLC Pipeline Orchestration

## Why This Exists

The SDLC pipeline has a mandatory execution order with gates between phases. This cross-cutting governance applies to ALL SDLC skills and is referenced (not duplicated) by each. It defines phase ordering, skip prevention, parallel allowances, cadence rules, and rework paths.

---

## Mandatory Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│ PLANNING (once per project)                                     │
├─────────────────────────────────────────────────────────────────┤
│ 1. sdlc-planning           → Gate: Go/No-Go Review             │
│ 2. sdlc-stack-selection    → Gate: Architecture Review          │
│ 3. sdlc-detailed-design    → Gate: Design-Complete              │
│ 4. sdlc-epic-planning      → Gate: Epic Review & Estimation    │
│ 5. sdlc-sprint-planning    → Gate: Sprint Commitment            │
├─────────────────────────────────────────────────────────────────┤
│ EXECUTION (per-sprint, repeats each sprint)                     │
├─────────────────────────────────────────────────────────────────┤
│ 6. sdlc-implementation     → Gate: DoD Met (ready for QA)      │
│ 7. sdlc-testing-qa         → Gate: QA Sign-Off                  │
├─────────────────────────────────────────────────────────────────┤
│ RELEASE (per-release, once when sprints complete)               │
├─────────────────────────────────────────────────────────────────┤
│ 8. sdlc-release-planning   → Gate: Release Readiness Review    │
│ 9. sdlc-deployment         → Gate: Deployment Verified          │
│10. sdlc-observability      → Gate: Observability Readiness      │
├─────────────────────────────────────────────────────────────────┤
│ OPERATIONS (ongoing, recurring cadence)                         │
├─────────────────────────────────────────────────────────────────┤
│11. sdlc-maintenance        → No gate (monthly/quarterly review) │
├─────────────────────────────────────────────────────────────────┤
│ STANDALONE (triggered on demand)                                │
├─────────────────────────────────────────────────────────────────┤
│  sdlc-incident-management  → Triggered by production incidents  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase Cadence Rules

| Phase Group | Cadence | When |
|-------------|---------|------|
| Planning (1–5) | Once per project | Project kickoff through sprint commitment |
| Execution (6–7) | Per sprint | Repeats every sprint during implementation |
| Release (8–10) | Per release | After final sprint completes, before GA |
| Operations (11) | Ongoing | Monthly maintenance reviews, quarterly deep audits |
| Incident Management | On demand | Triggered by production incidents at any time |

### Per-Sprint Cycle (Phases 6–7)

Within each sprint, stories flow through:
```
Sprint Backlog → Implementation (Phase 6) → QA (Phase 7) → Done
```

- Phase 6 and 7 run concurrently within a sprint (QA tests completed stories while dev implements remaining ones)
- End-of-sprint: all committed stories must pass through both phases or be documented as carry-over

### Per-Release Cycle (Phases 8–10)

After the final implementation sprint:
```
Release Planning (Phase 8) → Deployment (Phase 9) → Observability (Phase 10)
```

- These phases are sequential — each gate must pass before the next begins
- Multiple sprints may feed into a single release

---

## Gate Definitions

| Phase | Gate Name | Pass Criteria |
|-------|-----------|---------------|
| 1 | Go/No-Go Review | Signed charter, stakeholder alignment |
| 2 | Architecture Review | Stack signed off, gap assessment complete |
| 3 | Design-Complete | All diagrams validated, team walkthrough done, SLOs defined |
| 4 | Epic Review & Estimation | Team validates estimates, dependencies mapped |
| 5 | Sprint Commitment | Team agrees to scope within capacity |
| 6 | DoD Met | All subtasks merged, CI green, code reviewed, unit tests passing, deployed to staging |
| 7 | QA Sign-Off | All ACs verified, no critical/high bugs, regression passing, coverage thresholds met |
| 8 | Release Readiness Review | Release criteria met, rollback tested, on-call briefed |
| 9 | Deployment Verified | Health checks passing, monitoring confirmed, smoke tests passing, no rollback triggered |
| 10 | Observability Readiness | All SLOs have dashboards, all alerts have runbooks, on-call can find any metric in 60s |

---

## Phase Skipping Prevention

- You CANNOT skip Phase 1 (planning). No design without a charter.
- You CANNOT skip Phase 2 (stack selection). No detailed design without a finalized stack.
- You CANNOT skip Phase 3 (detailed design). No epic planning without use cases and ERDs.
- You CANNOT skip Phase 6 (implementation). No QA without code that meets DoD.
- You CANNOT skip Phase 7 (testing/QA). No release planning without QA sign-off.
- You CANNOT skip Phase 9 (deployment). No observability setup without a running production system.
- You CAN skip Phase 8 (release planning) for internal tools or prototypes — but NEVER for user-facing production systems.
- You CAN skip Phase 10 (observability) for throwaway prototypes — but NEVER for production systems with users.
- Phase 11 (maintenance) is ongoing and cannot be "skipped" — it begins automatically after first deployment.
- The tool-specific skills (Linear, Jira) can run at any point after Phase 4.
- Incident management is standalone — triggers at any point after first deployment.

---

## Parallel Phase Allowances

| Situation | What Can Run in Parallel | Rule |
|-----------|-------------------------|------|
| Wireframes not ready | Backend/infra epic planning (Phase 4) can proceed. UI epic planning waits. | UI stories marked `[BLOCKED: wireframe]` with target date |
| Multiple services in architecture | Phase 3 (detailed design) can be parallelized per service | Each service needs its own use case + ERD + SLO set |
| Foundation epic obvious | E000 (repo/CI/CD) tasks can begin during Phase 4 planning | Does not require full epic plan to start repo setup |
| Spike needed mid-design | Timeboxed spike can run during Phase 2/3 without completing the phase | Spike results feed back into the phase that spawned it |
| Long procurement process | Vendor/license procurement starts during Phase 2 | Don't wait for procurement to complete all of Phase 2 — just that decision |
| QA and dev within sprint | QA tests completed stories while dev works on remaining sprint stories | Stories flow individually through Phase 6 → 7 within a sprint |
| Observability prep during release planning | Dashboard configs and alert rules can be drafted during Phase 8 | Cannot be validated until Phase 9 deployment is live |
| Maintenance overlaps everything | Phase 11 runs alongside active sprints after first deployment | Maintenance work competes for sprint capacity (default 20% allocation) |

---

## Rework Paths

If a gate rejects work, the path is ALWAYS backward to the prior phase:

| Rejection At | Rework Target | Scope of Rework |
|-------------|---------------|-----------------|
| Architecture Review rejects stack decision | Redo Phase 2 gap assessment for rejected component(s) only | Don't redo entire Phase 2 — targeted fix |
| Design Walkthrough reveals missing use case | Add use case to Phase 3, update ERD/data flow | May require Phase 2 re-evaluation if new component needed |
| Epic Review finds infeasible story | Back to Phase 3 to validate architecture supports the requirement | Or simplify the story if architecture is correct |
| Sprint carry-over > 50% for 2 sprints | Back to Phase 4/5 — re-estimate remaining work with actual velocity | Update timeline, notify stakeholders |
| DoD not met (Phase 6 gate fails) | Story stays in implementation — fix CI, tests, or code review issues | Does not move to QA until DoD checklist complete |
| QA rejects story (Phase 7 gate fails) | Back to Phase 6 — defect assigned to developer, fix + re-verify DoD | Story re-enters QA after fix. Sprint may carry over if late. |
| Release Readiness fails | Fix and re-run release criteria checks | Do not re-plan sprints — fix the specific failure |
| Deployment fails (Phase 9 gate fails) | Execute rollback, diagnose, fix, re-deploy | If root cause is code: back to Phase 6-7 for the fix |
| Observability gate fails | Add missing dashboards/alerts/runbooks | Does not require re-deployment unless metrics endpoints are missing |

---

## Change Control Process

Once the Project Charter is signed off and the project enters Design or Implementation, ALL scope changes must follow this process.

### When Change Control Applies

- New feature requested that wasn't in the charter's "In Scope" list
- Existing feature significantly expanded beyond original description
- New integration point or third-party dependency added
- Timeline change (moving the launch date)
- Budget increase request
- Team composition change (adding/removing members)

### Change Request Process

1. **Document the Request** — Requester fills out: what, why, impact if not done.
2. **Impact Analysis** — Tech Lead + PM assess: timeline, budget, dependency, risk impacts. What existing work gets delayed?
3. **Decision** — Accept (adjust timeline/budget), Defer (V2 backlog), or Reject (out of vision).
4. **If Accepted** — Update: charter scope table, epics.json, sprint plan, risk register. Communicate to full team.

### Change Request Template

```markdown
## Change Request: [CR-001] [Title]

**Requested by:** [Name] | **Date:** YYYY-MM-DD
**Priority:** Critical / High / Medium / Low

### Description
<!-- What is being requested? -->

### Business Justification
<!-- Why is this needed? What happens if we don't do it? -->

### Impact Analysis
| Dimension | Impact |
|-----------|--------|
| Timeline | +[X] sprint-days |
| Budget | +$[X]/month |
| Dependencies | [What it blocks/unblocks] |
| New Risks | [List] |
| Displaced Work | [What gets pushed back] |

### Decision
| Decision | By | Date |
|----------|-----|------|
| ☐ Accept ☐ Defer ☐ Reject | [Name] | YYYY-MM-DD |

### Rationale
<!-- Why this decision was made -->
```
