---
name: sdlc-maintenance
description: Use on a recurring cadence (monthly/quarterly) or when maintenance concerns arise — dependency audits, security patching, tech debt assessment, deprecation tracking, and capacity planning. Produces actionable maintenance reports that feed into sprint planning. NOT for incident response (use sdlc-incident-management), deploying patches (use sdlc-deployment), or SLO monitoring (use sdlc-observability).
---

# SDLC Maintenance

## Role & Tone

Act as a senior platform engineer. Be proactive and systematic — maintenance debt compounds exponentially when ignored. Quantify risk in business terms (SLO impact, security exposure window, cost growth). Recommend concrete actions with effort estimates so sprint planning can allocate capacity.

## Environment Scope

**write+validate** — Writes maintenance reports and plans to `<cwd>/drafts/maintenance/`. Runs read-only audit commands (`npm audit`, `pip audit`, `terraform plan`, `trivy image`). Does NOT apply patches, modify production, or execute upgrades.

## Workflow

1. **Check Existing State** — Does `<cwd>/drafts/maintenance/` exist with prior reports? When was the last audit? Report findings and any overdue items.

2. **Gather Context** — Ask the user:
   > "I need:
   > 1. Package manifests (package.json, pyproject.toml, go.mod, etc.)
   > 2. Last security scan report (or I'll run one)
   > 3. Current SLO performance (from sdlc-observability)
   > 4. Cloud cost dashboard access or recent bill
   > 5. Team capacity for next sprint (% available for maintenance)
   > 6. Known tech debt items (if tracked somewhere)"

3. **Dependency Audit** — For each service:

   | Package | Current | Latest | Severity | EOL? | Action |
   |---------|---------|--------|----------|------|--------|
   | [pkg] | v1.2.3 | v2.0.0 | High CVE | No | Upgrade (breaking) |
   | [pkg] | v3.1.0 | v3.2.1 | Patch | No | Upgrade (safe) |
   | [pkg] | v1.0.0 | v1.0.0 | None | Yes | Replace or remove |

   Categorize: security patches (urgent), minor updates (safe), major updates (breaking, needs planning), EOL (replace).

4. **Security Patching Priority** — Triage by severity and exposure:

   | Severity | Exposure | SLA | Action |
   |----------|----------|-----|--------|
   | Critical | Public-facing | 48 hours | Emergency patch, deploy immediately |
   | Critical | Internal only | 1 week | Prioritize in current sprint |
   | High | Public-facing | 1 week | Current or next sprint |
   | High | Internal only | 2 weeks | Next sprint |
   | Medium | Any | 1 month | Backlog, batch with other updates |
   | Low | Any | Quarterly | Batch in maintenance window |

5. **Tech Debt Assessment** — Categorize existing debt:

   | Category | Examples | SLO Impact | Effort |
   |----------|----------|------------|--------|
   | Code | Duplicated logic, missing abstractions, dead code | Low (maintainability) | S/M/L |
   | Architecture | Tight coupling, missing service boundaries | Medium (scalability) | L/XL |
   | Test | Low coverage areas, flaky tests, missing E2E | High (bug escape risk) | M/L |
   | Infrastructure | Manual processes, outdated images, scaling limits | High (availability) | M/L |
   | Documentation | Stale READMEs, missing runbooks, outdated diagrams | Low (onboarding) | S/M |

6. **Tech Debt Prioritization** — Score each item:
   - **Impact** (1-5): How much does this hurt SLOs, velocity, or security?
   - **Effort** (1-5): How much work to resolve? (1=hours, 5=multiple sprints)
   - **Priority** = Impact / Effort (higher = do first)
   - Link to SLO where possible: "fixing X would improve p95 latency by ~Y ms"

7. **Deprecation Management** — Track:

   | Dependency | Deprecation Date | EOL Date | Migration Plan | Owner | Status |
   |-----------|-----------------|----------|----------------|-------|--------|
   | [lib/API] | YYYY-MM-DD | YYYY-MM-DD | [link to plan] | [name] | Not started / In progress / Done |

8. **Capacity Planning Review** — Assess:
   - Current resource utilization vs provisioned (are we over/under?)
   - Growth trend (requests/day, storage, compute at 30/60/90 day projection)
   - Scaling triggers adequacy (will auto-scaling keep up with projected growth?)
   - Cost trending (monthly burn rate, projected vs budget)
   - Recommendations: scale up, optimize, or accept current state

9. **Maintenance Sprint Allocation** — Recommend:
   - Default: 20% of sprint capacity allocated to maintenance
   - If security patches pending: increase to 30-40% until resolved
   - If tech debt is impacting velocity: propose a dedicated hardening sprint
   - Never: 0% allocation (debt accumulates, SLOs degrade, incidents increase)

10. **Produce Maintenance Report** — Write to `<cwd>/drafts/maintenance/report-YYYY-MM.md`:
    - Executive summary (1 paragraph: health status, urgent items)
    - Dependency audit results with action items
    - Security patch status and SLA compliance
    - Tech debt backlog (prioritized)
    - Deprecation timeline and migration status
    - Capacity forecast and cost projection
    - Recommended sprint allocation for next period

### Failure Recovery (max 3 retries)

If audit commands fail or produce incomplete results:
- Verify tool installation and configuration
- Try alternative audit approach (different tool, manual check)
- Document gaps in report ("unable to audit X, reason: Y")
- After 3 failures → report partial results, note what couldn't be audited

### Rollback

If user cancels: delete files in `<cwd>/drafts/maintenance/`, confirm clean state.

## Ceremonies

### Monthly Maintenance Review (30 min)

Review maintenance report, triage urgent items, confirm sprint allocation for next month.

### Quarterly Tech Debt Prioritization (60 min)

Deep review of debt backlog, re-score priorities, plan hardening initiatives, review deprecation timelines.

## Output Structure

```
<cwd>/drafts/maintenance/
├── report-YYYY-MM.md           (monthly report)
├── dependency-audit-YYYY-MM.md
├── security-patch-log.md       (running log of patches applied)
├── tech-debt-backlog.md        (prioritized list)
├── deprecation-tracker.md
└── capacity-forecast.md
```

## Guardrails

- NEVER let critical security patches wait more than 48 hours
- NEVER skip dependency audit for more than 1 month
- NEVER allocate 0% sprint capacity to maintenance work
- NEVER ignore EOL or deprecated dependencies past their announced date
- NEVER batch critical security patches with routine updates (deploy separately, faster)
- NEVER skip testing patched dependencies in staging before production
- NEVER let tech debt backlog grow unbounded without quarterly review
- NEVER ignore capacity warnings from observability dashboards

## References

- `skills/sdlc-observability.md` — SLO performance data, capacity signals
- `skills/sdlc-deployment.md` — Deploying patches follows deployment process
- `skills/sdlc-sprint-planning.md` — Maintenance allocation competes for sprint capacity
- `skills/sdlc-incident-management.md` — Incidents often reveal maintenance gaps
- `steering/security/policies.md` — Dependency security, container hardening requirements
- `steering/orchestration/sdlc-pipeline.md` — Pipeline ordering, Phase 11
