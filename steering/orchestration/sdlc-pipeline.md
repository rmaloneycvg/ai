# SDLC Pipeline Orchestration

## Why This Exists

The SDLC pipeline has a mandatory execution order with gates between phases. This cross-cutting governance applies to ALL SDLC skills and is referenced (not duplicated) by each. It defines phase ordering, skip prevention, parallel allowances, and rework paths.

---

## Mandatory Sequence

```
1. sdlc-planning           → Gate: Go/No-Go Review (signed charter)
2. sdlc-stack-selection    → Gate: Architecture Review & Stack Sign-Off
3. sdlc-detailed-design    → Gate: Design-Complete (checklist + team walkthrough)
4. sdlc-epic-planning      → Gate: Epic Review & Estimation (team validates)
5. sdlc-sprint-planning    → Gate: Sprint Commitment (team agrees)
6. [Implementation sprints with ceremonies]
7. sdlc-release-planning   → Gate: Release Readiness Review
```

---

## Phase Skipping Prevention

- You CANNOT skip Phase 1 (planning). No design without a charter.
- You CANNOT skip Phase 2 (stack selection). No detailed design without a finalized stack.
- You CANNOT skip Phase 3 (detailed design). No epic planning without use cases and ERDs.
- You CAN skip Phase 7 (release planning) for internal tools or prototypes — but NEVER for user-facing production systems.
- The tool-specific skills (Linear, Jira) can run at any point after Phase 4.

---

## Parallel Phase Allowances

| Situation | What Can Run in Parallel | Rule |
|-----------|-------------------------|------|
| Wireframes not ready | Backend/infra epic planning (Phase 4) can proceed. UI epic planning waits. | UI stories marked `[BLOCKED: wireframe]` with target date |
| Multiple services in architecture | Phase 3 (detailed design) can be parallelized per service | Each service needs its own use case + ERD set |
| Foundation epic obvious | E000 (repo/CI/CD) tasks can begin during Phase 4 planning | Does not require full epic plan to start repo setup |
| Spike needed mid-design | Timeboxed spike can run during Phase 2/3 without completing the phase | Spike results feed back into the phase that spawned it |
| Long procurement process | Vendor/license procurement starts during Phase 2 | Don't wait for procurement to complete all of Phase 2 — just that decision |

---

## Rework Paths

If a gate rejects work, the path is ALWAYS backward to the prior phase:

| Rejection At | Rework Target | Scope of Rework |
|-------------|---------------|-----------------|
| Architecture Review rejects stack decision | Redo Phase 2 gap assessment for rejected component(s) only | Don't redo entire Phase 2 — targeted fix |
| Design Walkthrough reveals missing use case | Add use case to Phase 3, update ERD/data flow | May require Phase 2 re-evaluation if new component needed |
| Epic Review finds infeasible story | Back to Phase 3 to validate architecture supports the requirement | Or simplify the story if architecture is correct |
| Sprint carry-over > 50% for 2 sprints | Back to Phase 4/5 — re-estimate remaining work with actual velocity | Update timeline, notify stakeholders |
| Release gate fails | Fix and re-run release criteria checks | Do not re-plan sprints — fix the specific failure |

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
