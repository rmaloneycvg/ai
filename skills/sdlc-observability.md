---
name: sdlc-observability
description: Use after deployment to establish production monitoring, or when SLO tracking needs review. Implements the SLOs defined during detailed design (Phase 3) — creates dashboards, configures alerts, writes runbooks, tracks error budgets, and establishes SLO review cadence. NOT for defining SLOs (done in sdlc-detailed-design), deploying infrastructure (use sdlc-deployment), or responding to incidents (use sdlc-incident-management).
---

# SDLC Observability

## Role & Tone

Act as an SRE. Be data-driven and proactive about reliability. Dashboards should answer questions before they're asked. Alerts should be actionable — never noisy. Every alert that fires must lead to a clear action.

## Environment Scope

**write+validate** — Writes dashboard configs, alert rules, runbooks, and observability docs to `<cwd>/drafts/observability/`. Validates configs parse correctly. Does NOT deploy monitoring infrastructure or modify production alerting directly.

## Prerequisites

This skill REQUIRES:
- SLO definitions from Phase 3 (`<cwd>/drafts/design/detailed/observability/slo-definitions.md`)
- Production deployment live (Phase 9 complete)
- Monitoring stack identified (Prometheus, Grafana, Datadog, CloudWatch, etc.)

## Workflow

1. **Check Existing State** — Does `<cwd>/drafts/observability/` exist? Are there prior dashboards or alert rules? Is this initial setup or a review/update?

2. **Gather Context** — Ask the user:
   > "I need:
   > 1. SLO definitions path (from sdlc-detailed-design)
   > 2. Monitoring stack (Prometheus+Grafana, Datadog, CloudWatch, etc.)
   > 3. Alerting tool (PagerDuty, OpsGenie, Slack, etc.)
   > 4. On-call rotation info
   > 5. Service list with metric endpoints
   > 6. Historical baseline data (if available — or note this is a new service)"

3. **Dashboard Design** — Per service, create dashboards covering:
   - **SLI Overview** — Current value vs SLO target for each SLI
   - **Error Budget** — Remaining budget, burn rate (1h, 6h, 24h, 7d windows)
   - **Dependency Health** — Upstream/downstream service status
   - **Resource Utilization** — CPU, memory, disk, network (with scaling thresholds)
   - **Request Flow** — Throughput, latency distribution, error breakdown by type

   Dashboard hierarchy: Team overview → Service detail → SLI deep-dive.

4. **Alert Rule Definition** — Per SLO:

   | SLO | Warning (ticket) | Critical (page) | Routing | Runbook |
   |-----|-----------------|-----------------|---------|---------|
   | Availability 99.9% | < 99.7% over 1h | < 99.5% over 5 min | On-call | runbook-availability.md |
   | Latency p95 < 200ms | > 300ms over 15 min | > 500ms over 5 min | On-call | runbook-latency.md |
   | Error rate < 0.1% | > 0.5% over 15 min | > 1% over 5 min | On-call | runbook-errors.md |

   Rules for alerts:
   - Every alert MUST have a runbook linked
   - Warning = create ticket, investigate during business hours
   - Critical = page on-call, immediate response required
   - Use multi-window burn rate alerts to reduce false positives

5. **Error Budget Policy** — Define team response when budget is consumed:

   | Budget Remaining | Team Response |
   |-----------------|---------------|
   | > 50% | Normal development velocity |
   | 25-50% | Increased monitoring, no risky changes |
   | 10-25% | Feature freeze for affected service, reliability work only |
   | < 10% | All hands on reliability until budget recovers |
   | Exhausted (0%) | Mandatory incident review, no deploys until budget positive |

6. **Runbook Creation** — Per alert, document:
   - **What fired:** Alert name, meaning, severity
   - **Likely causes:** Top 3-5 causes ranked by probability
   - **Diagnostic steps:** Commands/queries to run, what to look for
   - **Remediation:** Step-by-step fix for each likely cause
   - **Escalation:** When and to whom if you can't resolve in 15 min (warning) or 5 min (critical)

7. **Health Check Validation** — Verify:
   - All services expose `/health` or `/healthz` endpoint
   - Metrics endpoints are scraped at expected interval
   - Data flows from service → collector → storage → dashboard
   - Synthetic monitors configured for critical user flows

8. **SLO Review Cadence** — Establish:
   - **Monthly:** Review SLO performance, error budget status, false positive rate
   - **Quarterly:** Adjust targets based on actual performance (tighten if consistently met, loosen if unrealistic)
   - **After incidents:** Review whether SLOs detected the issue before users reported it

9. **Capacity Planning Signals** — Define:
   - Auto-scaling triggers (CPU > 70%, memory > 80%, queue depth > threshold)
   - Growth trending (request rate projection at 30/60/90 days)
   - Cost projection alerts (if spend > budget by > 20%)

10. **Produce Observability Documentation** — Write to `<cwd>/drafts/observability/`:
    - Dashboard catalog (URLs, owners, purpose)
    - Alert catalog (name, severity, routing, runbook link)
    - SLO tracking summary (current status per service)
    - Error budget report
    - On-call quick-reference (escalation paths, key dashboards, common procedures)

### Failure Recovery (max 3 retries)

If observability setup is incomplete (missing metrics, broken dashboards):
- Identify gap (missing endpoint, misconfigured scrape, broken query)
- Fix configuration
- Re-validate data flow
- After 3 failures → escalate: service may need code changes to expose metrics

### Rollback

If user cancels: delete files in `<cwd>/drafts/observability/`, confirm clean state.

## Gate: Observability Readiness

Observability passes when:
- Every defined SLO has a dashboard with current data
- Every alert has a linked, reviewed runbook
- On-call engineer can demonstrate finding any service's health status within 60 seconds
- Error budget policy is documented and team-acknowledged
- SLO review cadence is scheduled

## Output Structure

```
<cwd>/drafts/observability/
├── dashboards/
│   ├── team-overview.json (or .yaml per tool)
│   └── service-[name].json
├── alerts/
│   ├── alert-rules.yaml
│   └── routing-config.yaml
├── runbooks/
│   ├── runbook-availability.md
│   ├── runbook-latency.md
│   ├── runbook-errors.md
│   └── runbook-[custom].md
├── error-budget-policy.md
├── slo-tracking-summary.md
├── capacity-plan.md
└── oncall-quickref.md
```

## Guardrails

- NEVER go live without dashboards for every defined SLO
- NEVER create an alert without a linked runbook
- NEVER set SLO targets without historical baseline (use first 2 weeks as baseline for new services)
- NEVER ignore error budget exhaustion — enforce the policy
- NEVER create noisy alerts (if it fires and requires no action, remove it)
- NEVER skip the monthly SLO review
- NEVER leave on-call without a quick-reference document
- NEVER rely solely on reactive alerting — include proactive capacity signals

## References

- `skills/sdlc-detailed-design.md` — SLO definitions (Phase 3 output)
- `skills/sdlc-deployment.md` — Prior phase: production must be live
- `skills/sdlc-maintenance.md` — Ongoing: capacity planning feeds into maintenance
- `skills/sdlc-incident-management.md` — Triggered when alerts escalate to incidents
- `steering/orchestration/local-dev.md` — Telemetry stack (otel-collector, jaeger, prometheus, grafana)
- `steering/orchestration/sdlc-pipeline.md` — Pipeline ordering, Phase 10
