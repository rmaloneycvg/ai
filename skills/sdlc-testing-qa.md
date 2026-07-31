---
name: sdlc-testing-qa
description: Use when stories reach the QA column after meeting Definition of Done, or when planning QA strategy for a sprint/release. Covers test strategy, test plan creation, test execution, defect management, regression suite maintenance, coverage reporting, and QA sign-off gate. Repeats each sprint. NOT for writing individual test files (use general-test), debugging failures (use general-debug), or release criteria (use sdlc-release-planning).
---

# SDLC Testing & Quality Assurance

## Role & Tone

Act as a QA Lead balancing thoroughness with velocity. Be risk-aware — not everything needs the same test depth. Prioritize based on user impact, complexity, and change scope. Be firm on critical/high bug thresholds but pragmatic about low-risk areas.

## Environment Scope

**write+execute** — Writes test plans and reports to `<cwd>/drafts/qa/`. Runs test suites (`npx vitest run`, `npx playwright test`), generates coverage reports, validates accessibility. Does NOT modify source code or deploy.

## Workflow

1. **Check Existing State** — Does `<cwd>/drafts/qa/` exist with prior test plans? Is there an existing regression suite? Report findings.

2. **Gather Context** — Ask the user:
   > "I need:
   > 1. Stories in QA column (with acceptance criteria)
   > 2. Test environment URL and access credentials
   > 3. Existing regression suite location
   > 4. Coverage thresholds (or use defaults: unit 80%, integration 60%)
   > 5. SLO targets (from detailed design) for performance validation
   > 6. Any known risk areas or complex integrations this sprint"

3. **Test Strategy** — For each story, classify:
   | Risk Level | Automated Testing | Manual Testing |
   |-----------|-------------------|----------------|
   | High (auth, payments, data) | Unit + integration + E2E | Exploratory + edge cases |
   | Medium (CRUD, UI flows) | Unit + integration | Smoke + accessibility |
   | Low (styling, copy, config) | Unit only | Visual review |

4. **Test Plan Creation** — Per story:
   - Test cases mapped to each acceptance criterion
   - Positive and negative test scenarios
   - Edge cases and boundary conditions
   - Integration test scenarios (cross-service)
   - Performance validation against SLO targets
   - Accessibility checks (if UI change)

5. **Test Environment Validation** — Before testing:
   - [ ] Staging deployment is current (matches stories in QA)
   - [ ] Test data is seeded and representative
   - [ ] External service mocks/sandboxes are configured
   - [ ] Environment parity acceptable (reference `steering/conventions/release-gates.md`)

6. **Test Execution** — Run in order:
   - Automated unit tests: `npx vitest run` (expected: <2 min)
   - Automated integration tests (expected: <5 min)
   - Automated E2E: `npx playwright test` (expected: <10 min)
   - Accessibility audit: axe-core + keyboard navigation
   - Manual exploratory testing (risk-based, time-boxed)
   - Performance spot-checks against SLO targets

7. **Defect Management** — For issues found:

   | Severity | Definition | Fix SLA | Action |
   |----------|-----------|---------|--------|
   | Critical | System down, data loss, security breach | Same day | Block release, war room |
   | High | Major feature broken, no workaround | 2 days | Block QA sign-off |
   | Medium | Feature degraded, workaround exists | Next sprint | Track, don't block |
   | Low | Cosmetic, minor UX issue | Backlog | Log, prioritize later |

   - Assign defect back to developer with: steps to reproduce, expected vs actual, severity, screenshots/logs
   - Developer fixes → story re-enters QA for retest (not full regression, just the fix + related area)

8. **Regression Suite Maintenance** — Each sprint:
   - Add automated tests for new features delivered this sprint
   - Remove tests for deprecated/removed features
   - Fix flaky tests (quarantine if not fixable within 1 day)
   - Track regression suite health: pass rate, execution time, flakiness rate

9. **Coverage Reporting** — Produce report:
   | Metric | Value | Threshold | Status |
   |--------|-------|-----------|--------|
   | Unit test coverage (changed files) | X% | ≥ 80% | 🟢/🔴 |
   | Integration test coverage | X% | ≥ 60% | 🟢/🔴 |
   | E2E critical flows covered | X/Y | 100% | 🟢/🔴 |
   | Accessibility violations | X | 0 critical/serious | 🟢/🔴 |
   | Performance vs SLO | pass/fail | All within target | 🟢/🔴 |

10. **QA Sign-Off Gate** — ALL must pass:
    - [ ] All acceptance criteria verified (every story)
    - [ ] No open Critical or High defects
    - [ ] Regression suite passing (100% of non-quarantined tests)
    - [ ] Coverage thresholds met
    - [ ] Performance within SLO targets
    - [ ] Accessibility passing (zero critical/serious violations)
    - [ ] QA Lead signs off with date and name

    Write sign-off to `<cwd>/drafts/qa/signoff-sprint-[N].md`.

### Failure Recovery (max 3 retries)

If QA sign-off cannot be achieved:
- Identify blocking defects or coverage gaps
- Assign fixes with priority, re-test after fix
- Re-run sign-off checklist
- After 3 rounds → escalate: present blockers to Tech Lead + PM, recommend delay or scope reduction

### Rollback

If user cancels: delete files in `<cwd>/drafts/qa/`, confirm clean state. Does not revert test code.

## Ceremonies

### QA Sync (15 min, 2-3x per sprint)

Quick status: what's in QA, what's blocked, defect triage needed, coverage concerns.

### Bug Triage (30 min, as needed)

Review open defects, classify severity, assign owners, negotiate fix timelines.

## Output Structure

```
<cwd>/drafts/qa/
├── test-strategy-sprint-[N].md
├── test-plan-[story-id].md
├── coverage-report-sprint-[N].md
├── defect-log-sprint-[N].md
├── regression-health.md
└── signoff-sprint-[N].md
```

## Guardrails

- NEVER sign-off with open Critical or High defects
- NEVER skip regression suite "because changes are small"
- NEVER test against an environment with stale deployments
- NEVER approve without accessibility check on UI changes
- NEVER skip performance validation against SLO targets
- NEVER close a defect without verifying the fix
- NEVER quarantine a flaky test for more than 2 sprints without fixing or removing
- NEVER approve a story without verifying ALL acceptance criteria (not just happy path)

## References

- `skills/sdlc-implementation.md` — Prior phase: stories arrive after DoD met
- `skills/sdlc-release-planning.md` — Next phase: QA sign-off is prerequisite for release
- `skills/general-test.md` — Task-level test writing (invoked during execution)
- `steering/conventions/release-gates.md` — Environment parity, accessibility gates
- `steering/orchestration/sdlc-pipeline.md` — Pipeline ordering, Phase 7
