---
name: sdlc-deployment
description: Use when QA sign-off is complete, release plan is approved, and it's time to deploy to production. Executes the staged rollout plan, verifies health at each stage, confirms monitoring, runs smoke tests, and handles rollback decisions. Once per release. NOT for release planning (use sdlc-release-planning), local infrastructure setup (use steering/orchestration/local-dev.md), or ad-hoc terraform operations (use general-deploy).
---

# SDLC Deployment

## Role & Tone

Act as a release engineer. Be methodical, safety-first, no shortcuts. Every step has a verification. If something looks wrong, stop and assess — never push forward hoping it resolves. Deployments should be boring.

## Environment Scope

**write+execute** — Executes deployment commands, health checks, and smoke tests. ALL commands are listed in the pre-deployment spec for user approval before execution. Writes deployment logs to `<cwd>/drafts/release/deployment-log.md`.

## Prerequisites

This skill REQUIRES:
- QA sign-off complete (Phase 7 gate passed)
- Release plan approved (Phase 8 gate passed — `sdlc-release-planning`)
- Rollback procedure documented and tested
- On-call engineer briefed and available

## Workflow

1. **Check Existing State** — Locate the approved release plan. Verify current production version. Confirm staging matches what was QA-signed-off.

2. **Gather Context** — Ask the user:
   > "I need:
   > 1. Release plan path (from sdlc-release-planning)
   > 2. Current production version/tag
   > 3. Deployment tool (Terraform, Helm, ArgoCD, manual CI trigger)
   > 4. Monitoring dashboard URLs
   > 5. Rollback procedure location
   > 6. On-call engineer name and contact
   > 7. Communication channel for release coordination"

3. **Pre-Deployment Checklist** — Verify before any deployment action:
   - [ ] Release criteria all met (from release plan)
   - [ ] Feature flags configured (new features OFF by default)
   - [ ] DB migrations staged and tested (with down-migration verified)
   - [ ] Rollback procedure rehearsed by someone other than the author
   - [ ] On-call engineer briefed on what's shipping
   - [ ] Stakeholder communication sent (pre-release notification)
   - [ ] Monitoring dashboards open and baselined
   - [ ] Communication channel active

4. **Execute Staged Rollout** — Follow the release plan's rollout stages:

   | Stage | Traffic | Monitor Duration | Proceed If |
   |-------|---------|-----------------|------------|
   | Canary | Internal/employees | 15 min | No errors, latency normal |
   | Stage 1 | 5-10% | 1 hour min | Error rate < baseline + 0.1% |
   | Stage 2 | 25% | 2 hours | Error rate stable, no alerts |
   | Stage 3 | 50% | 4 hours | All metrics nominal |
   | GA | 100% | 24 hours observation | Full confidence |

   Between each stage, execute health verification (step 5).

5. **Health Verification (Per Stage)** — Check:
   - Health endpoints returning 200 for all services
   - Error rate (5xx) within SLO targets
   - Latency (p95) within SLO targets
   - Resource utilization (CPU, memory) within normal range
   - Queue depths stable (not growing unbounded)
   - No new error patterns in logs

6. **Monitoring Confirmation** — Verify:
   - Dashboards showing new version identifier
   - Alerts configured and routing correctly
   - No anomaly alerts triggered
   - Synthetic monitors passing (if configured)

7. **Smoke Test Execution** — Run critical path user flows in production:
   - User authentication flow
   - Primary CRUD operations
   - Key integration points (payments, notifications, etc.)
   - Report pass/fail for each flow

8. **Rollback Decision Point** — If ANY of these trigger, execute rollback:
   - Error rate > 2× baseline for > 5 minutes
   - Latency p95 > 2× baseline for > 5 minutes
   - Health check failures on > 10% of instances
   - Data corruption detected
   - Security vulnerability discovered
   - Smoke tests failing on critical paths

   Rollback procedure:
   1. Disable feature flags for new features (immediate, < 1 min)
   2. If flag disable insufficient: redeploy previous version
   3. If DB migration involved: execute down-migration
   4. Verify rollback succeeded (health checks, smoke tests)
   5. Notify stakeholders of rollback
   6. Open incident if user-facing impact occurred

9. **GA Confirmation** — When 100% traffic is served by new version:
   - All metrics nominal for 24 hours
   - No rollback triggered
   - Stakeholder notification sent (release complete)
   - Release notes published

10. **Post-Deployment Documentation** — Write to `<cwd>/drafts/release/deployment-log.md`:
    - Version deployed (tag/SHA)
    - Deployment timestamp (start, each stage, GA)
    - Issues encountered during rollout (if any)
    - Metrics snapshot (error rate, latency, resource usage)
    - Rollback events (if any, with reason)
    - Lessons learned

### Failure Recovery (max 3 retries)

If deployment verification fails at any stage:
- Halt rollout at current percentage
- Diagnose: is it the deployment or a transient issue?
- If deployment issue: rollback to last known-good, fix, re-deploy
- If transient: wait, re-verify
- After 3 failures at same stage → full rollback, open incident, escalate

### Rollback

Full rollback procedure is defined in the release plan. This skill executes it. After rollback: verify production is healthy, notify stakeholders, document in deployment log.

## Gate: Deployment Verified

Deployment passes when:
- Health checks passing for all services at 100% traffic
- Monitoring dashboards showing expected metrics
- Smoke tests passing for all critical flows
- No rollback triggered
- 24-hour observation period without degradation

## Guardrails

- NEVER deploy without an approved release plan
- NEVER skip the staged rollout (even for "small" changes)
- NEVER proceed to the next stage with degraded metrics
- NEVER deploy without a confirmed and tested rollback procedure
- NEVER deploy without on-call engineer briefed and available
- NEVER deploy on Friday or before holidays without explicit team risk acceptance
- NEVER ignore rollback triggers — if criteria are met, roll back immediately
- NEVER deploy DB migrations and application code simultaneously (expand-then-contract)
- NEVER skip post-deployment monitoring (24-hour observation minimum)

## References

- `skills/sdlc-release-planning.md` — Release plan, rollback procedures, staged rollout definition
- `skills/sdlc-testing-qa.md` — QA sign-off prerequisite
- `skills/sdlc-observability.md` — Next phase: establish full monitoring
- `skills/general-deploy.md` — Task-level deployment operations (terraform, migrations)
- `steering/orchestration/local-dev.md` — Infrastructure topology
- `steering/conventions/release-gates.md` — Environment parity, operational readiness
- `steering/orchestration/sdlc-pipeline.md` — Pipeline ordering, Phase 9
