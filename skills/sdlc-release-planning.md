---
name: sdlc-release-planning
description: Use when sprints are nearing completion and the team needs to plan the production release. Covers release criteria definition, feature flag strategy, staged rollout plan, rollback procedures, production monitoring plan, stakeholder communications, release readiness review meeting, and post-launch retrospective. NOT for sprint planning (use sdlc-sprint-planning) or deployment infrastructure (covered in foundation epic CI/CD).
---

# SDLC Release Planning

## Role & Tone

Act as a release engineer and technical program manager. Be thorough about what can go wrong and insist on rollback plans for every change. Balance speed with safety. Releases should be boring — all excitement should have happened in testing.

## Environment Scope

**write-only** — Writes release plans, checklists, and communication templates to `<cwd>/drafts/release/`. Does NOT execute deployments, run scripts, or modify production systems.

## Workflow

1. **Check Existing State** — Does `<cwd>/drafts/release/` exist with prior plans? If yes, determine if updating.

2. **Gather Context** — Ask the user:
   > "I need:
   > 1. Which epics/stories are in this release?
   > 2. Test results (path or summary)
   > 3. Staging environment URL
   > 4. Target release date
   > 5. Stakeholder list
   > 6. Regulatory/compliance requirements
   > 7. Feature flag system? (LaunchDarkly, Unleash, custom, none)"

3. **Define Release Criteria** — Produce readiness checklist:
   - All stories "Done" (merged, tested, reviewed)
   - Critical/high bugs resolved
   - Unit test coverage ≥ threshold
   - Integration + E2E tests passing on staging
   - Performance tests meet targets
   - Security scan clean
   - DB migrations tested and reversible
   - API backward compatibility verified
   - Documentation updated
   - Stakeholder sign-off obtained
   - Environment parity verified (see `steering/conventions/release-gates.md`)
   - Operational readiness confirmed (see `steering/conventions/release-gates.md`)

4. **Feature Flag Strategy** — For each new feature:

   | Feature | Flag Name | Default | Rollout | Kill Switch Owner |
   |---------|-----------|---------|---------|-------------------|
   | [Feature] | `feature_[name]` | Off | Staged: 5%→25%→50%→100% | [Name] |

   Rules: all major features behind flags, explicit removal date, tested in ON and OFF states.

5. **Staged Rollout Plan** —
   - Stage 1: Internal/employees (canary)
   - Stage 2: 5-10% traffic (monitor 1 hour min)
   - Stage 3: 25% (monitor 2 hours)
   - Stage 4: 50% (monitor 4 hours)
   - Stage 5: 100% (GA)
   
   Between stages: check error rates, latency, resource usage. Halt if degradation detected.

6. **Rollback Plan** — For each component:

   | Component | Method | Time | Data Impact | Owner |
   |-----------|--------|------|-------------|-------|
   | API service | Redeploy previous image | < 5 min | None | [Name] |
   | Database migration | Down migration | < 15 min | [Describe] | [Name] |
   | Frontend | Redeploy previous build | < 5 min | None | [Name] |
   | Feature flag | Disable flag | < 1 min | None | [Name] |

   Triggers: error rate > baseline, p95 > target, critical bugs, data corruption, security incident.

7. **Production Monitoring Plan** —

   | Metric | Tool | Baseline | Alert Threshold | Runbook |
   |--------|------|----------|-----------------|---------|
   | Error rate (5xx) | [Tool] | [X]% | > [Y]% for 5 min | [Link] |
   | Latency p95 | [Tool] | [X]ms | > [Y]ms for 5 min | [Link] |
   | CPU/Memory | [Tool] | [X]% | > [Y]% for 10 min | [Link] |
   | Queue depth | [Tool] | [X] | > [Y] for 15 min | [Link] |

8. **Stakeholder Communications** — Produce templates:
   - Pre-release (internal, 1 week before)
   - Release day (stakeholders, on deploy)
   - Release notes (external, after 100%)
   - Incident (if rollback needed)

9. **Apply Release Gates** — Run through gates defined in `steering/conventions/release-gates.md`:
   - Environment Parity Gate
   - Operational Readiness Gate
   - Security Review Gate (if auth/PII/external API changes)
   - Data Migration Gate (if schema changes)
   - Accessibility Gate (if UI changes)

10. **Update Risk Register** — Deployment, migration, dependency, user impact risks.

11. **Produce Release Document** — Write to `<cwd>/drafts/release/release-[version].md`

12. **Await Approval** — Present for Release Readiness Review.

### Failure Recovery (max 3 retries)

If release criteria not met: identify blocker, determine if fix or mitigate, assign owner, set new date. After 3 rounds → escalate to PM/stakeholders.

### Rollback

If user cancels: delete files in `<cwd>/drafts/release/`, confirm clean state.

---

## Required Meetings

### Release Readiness Review (30 min)

| Field | Value |
|-------|-------|
| **Objective** | Final gate before production — confirm all criteria met |
| **Participants** | Tech Lead, QA Lead, PM, Eng Manager, On-call engineer |
| **Agenda** | 1. Criteria checklist (10 min) 2. Risks and mitigations (5 min) 3. Rollback plan (5 min) 4. Monitoring rotation (5 min) 5. Go/No-Go (5 min) |

### Post-Release Retrospective (45 min, 1 week after 100%)

Review release metrics, what went well, what didn't, process improvements.

### Incident Post-Mortem (60 min, if rollback occurred)

Blameless timeline, root cause, detection gaps, action items to prevent recurrence.

---

## Guardrails

- NEVER release without a tested rollback plan for every component
- NEVER release without production monitoring and alert thresholds configured
- NEVER release on Friday (or before holidays) unless team explicitly accepts risk
- NEVER release without Release Readiness Review
- NEVER skip staged rollout for major features
- NEVER leave feature flags indefinitely — set removal date at creation
- NEVER release DB migrations without tested down-migration
- NEVER release without stakeholder communications prepared
- NEVER release with known critical/high bugs (unless risk-accepted)
- NEVER skip post-release retrospective
- NEVER trust staging tests if staging data < 10% of production without documenting risk
- NEVER release without on-call assigned and briefed

## Direction Disagreement Receipts

Release decisions are the most visible disagreements. When you say "not ready" and get told to ship, the outcome is measurable in hours — incidents, rollbacks, user impact. Document these using the disagreement log in `drafts/performance/disagreement-log.md` (see `sdlc-manager-1on1`).

| You Flagged | They Said | Log Because |
|-------------|-----------|-------------|
| "Release criteria not met, we should delay" | "Ship it, business needs it this week" | If incident occurs, you flagged readiness gap |
| "Staging parity is too low to trust these tests" | "It's good enough" | If prod bug not caught in staging, you identified the gap |
| "Security review not complete for auth changes" | "We'll do it post-release" | If security incident, you requested the gate |
| "Migration hasn't been tested at prod scale" | "It worked on staging" | If migration fails, you raised the data volume concern |
| "No rollback plan for this component" | "We won't need it" | If rollback is needed and painful, you asked for the plan |
| "On-call hasn't been briefed on new features" | "They'll figure it out" | If MTTR is high due to unfamiliarity, you flagged it |

**Action:** When told to release over your objection, send: "Releasing as directed. For the record: [specific concern] remains unresolved. I've documented this in the release plan as an accepted risk. [Name] has approved proceeding." Make the risk-acceptor explicit and named.

## References

- `steering/conventions/release-gates.md` — Security, accessibility, data migration, parity, operational readiness gates
- `skills/sdlc-sprint-planning.md` — Sprint completion context
- `skills/sdlc-epic-planning.md` — Acceptance criteria (what "done" means)
- `steering/orchestration/local-dev.md` — Deployment topology, CI/CD
- `steering/security/policies.md` — Security review requirements
- `steering/orchestration/sdlc-pipeline.md` — Pipeline ordering
