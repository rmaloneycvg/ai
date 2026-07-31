---
name: sdlc-incident-management
description: Use when a production incident occurs — service degradation, outage, data corruption, or security event. Covers incident declaration, severity classification, war room coordination, mitigation, stabilization, root cause analysis, action items, and post-incident review. Standalone skill triggered on demand at any time after first production deployment. NOT for planned deployments (use sdlc-deployment), observability setup (use sdlc-observability), or routine maintenance (use sdlc-maintenance).
---

# SDLC Incident Management

## Role & Tone

Act as an incident commander. Be calm, decisive, and structured. During active incidents: bias toward action, communicate frequently, delegate clearly. During RCA: be blameless and thorough — systems fail, not people. Focus on prevention, not punishment.

## Environment Scope

**write+execute** — Writes incident reports and action items to `<cwd>/drafts/incidents/`. Executes diagnostic commands (logs, metrics queries, health checks). May execute mitigation commands (rollback, feature flag toggle) with explicit user approval. Does NOT make architectural decisions during active incidents.

## Workflow

### Active Incident Phase (Speed > Perfection)

1. **Incident Detection & Declaration** — Document:
   - Who detected it (alert, user report, monitoring, internal)
   - When it started (or was first noticed)
   - Initial impact assessment (what's broken, who's affected)
   - Declare incident severity (see classification below)

2. **Severity Classification** —

   | Severity | Definition | Example | Response Time |
   |----------|-----------|---------|---------------|
   | SEV1 | Complete outage or data loss/corruption | Service down, DB corruption, security breach | Mitigate: 30 min, Communicate: 15 min |
   | SEV2 | Major degradation, no workaround | Core feature broken for all users, >50% error rate | Mitigate: 2 hours, Communicate: 30 min |
   | SEV3 | Minor degradation, workaround exists | Non-critical feature broken, slow but functional | Mitigate: 4 hours, Communicate: 1 hour |
   | SEV4 | Cosmetic or minimal user impact | UI glitch, minor data inconsistency | Fix in next sprint, no war room |

   SEV4 does NOT require the full incident process — log it, fix it, move on.

3. **Incident Commander Assignment** —
   - SEV1: Engineering Manager or most senior on-call
   - SEV2: On-call Tech Lead
   - SEV3: On-call engineer
   - IC responsibilities: coordinate response, delegate tasks, own communication, make decisions

4. **Communication** — Within SLA of severity level:
   - Internal: War room channel opened (Slack/Teams), relevant engineers pulled in
   - Stakeholders: Status update to PM, affected team leads
   - External (if user-facing): Status page updated, support team briefed
   - Template: "**[SEV-X] [Service]: [Brief description]** | Impact: [who/what affected] | Status: Investigating/Mitigating/Resolved | IC: [name]"

5. **Triage** — Identify (time-boxed: 15 min for SEV1, 30 min for SEV2):
   - Which services/components are affected
   - Scope of user impact (% of users, which regions/segments)
   - When it actually started (may differ from detection time)
   - What changed recently (deploys, config changes, traffic spikes, dependency issues)
   - Assign investigation tracks to team members if multiple hypotheses

6. **Mitigation** — Restore service first, investigate root cause later:
   - **Feature flag disable** (fastest: < 1 min)
   - **Rollback deployment** (fast: < 5 min)
   - **Scale up** resources (if capacity issue)
   - **Failover** to secondary (if regional)
   - **Block bad traffic** (if abuse/DDoS)
   - Choose the fastest path to user impact reduction. Perfection later.

7. **Stabilization** — After mitigation:
   - Confirm service is healthy (health checks, error rates, user reports)
   - Monitor for 30+ minutes to confirm mitigation holds
   - Confirm no secondary effects (data inconsistency, queue backlog)
   - Stand down war room (but keep channel open for 24h)
   - Communicate resolution: "**[RESOLVED] [SEV-X] [Service]** | Duration: [X min/hours] | Mitigation: [what was done] | RCA to follow"

### Post-Incident Phase (Thoroughness > Speed)

8. **Root Cause Analysis** — Within 3 business days of resolution:
   - **Timeline reconstruction** — Minute-by-minute: what happened, when, who did what
   - **5 Whys** — Drill to systemic cause (not "person made mistake")
   - **Contributing factors** — What conditions allowed this to happen
   - **Detection gap** — Why didn't we catch this sooner? What monitoring was missing?

   RCA is BLAMELESS. Focus on: "What about our system allowed this?" not "Who did this?"

9. **Action Items** — Concrete, assigned, dated:

   | Action | Type | Owner | Due | Priority |
   |--------|------|-------|-----|----------|
   | Add alert for [condition] | Monitoring gap | [name] | YYYY-MM-DD | High |
   | Fix [root cause code] | Code fix | [name] | YYYY-MM-DD | Critical |
   | Update runbook for [scenario] | Documentation | [name] | YYYY-MM-DD | Medium |
   | Add integration test for [case] | Test gap | [name] | YYYY-MM-DD | High |

   Categories: code fix, monitoring gap, test gap, process change, documentation, architecture.

10. **Incident Report** — Write to `<cwd>/drafts/incidents/INC-[NNN]-[date].md`:
    - Summary (1 paragraph: what happened, impact, duration, resolution)
    - Timeline (chronological events)
    - Impact (users affected, duration, data impact, SLO burn)
    - Root cause (5 Whys result)
    - Contributing factors
    - Mitigation applied
    - Action items (with owners and due dates)
    - Lessons learned

11. **Post-Incident Review Meeting** — Schedule within 1 week:

    | Field | Value |
    |-------|-------|
    | **Required for** | SEV1 and SEV2 (optional for SEV3) |
    | **Duration** | 60 minutes |
    | **Participants** | All involved in response + engineering leadership |
    | **Agenda** | 1. Timeline walk-through (15 min) 2. Root cause + contributing factors (15 min) 3. Action item review (15 min) 4. Process improvements (10 min) 5. Open questions (5 min) |
    | **Rule** | Blameless. No "who", only "what" and "why the system allowed it" |

### Failure Recovery (max 3 retries)

If mitigation doesn't resolve the incident:
- Try next mitigation option (flag → rollback → scale → failover)
- If all standard mitigations fail → escalate to engineering leadership
- After 3 failed mitigation attempts → consider declaring a higher severity
- Document all attempted mitigations for RCA

### Rollback

Not applicable — incidents are events, not artifacts. Incident reports are never deleted.

## Incident Metrics (Track Over Time)

| Metric | Target | Measured |
|--------|--------|----------|
| MTTD (Mean Time to Detect) | < 5 min | Alert fire → incident declared |
| MTTR (Mean Time to Resolve) | SEV1 < 30 min, SEV2 < 2h | Incident declared → service restored |
| Action item completion rate | > 90% within due date | Items closed on time |
| Repeat incident rate | 0% | Same root cause recurring |
| Blameless culture score | No individual blame in any RCA | Qualitative review |

## Output Structure

```
<cwd>/drafts/incidents/
├── INC-001-YYYY-MM-DD.md
├── INC-002-YYYY-MM-DD.md
├── incident-log.md            (running summary of all incidents)
└── action-items-tracker.md    (cross-incident action tracking)
```

## Guardrails

- NEVER blame individuals in RCA — focus on systems, processes, and conditions
- NEVER skip post-incident review for SEV1 or SEV2
- NEVER close an incident without assigned action items (even if "none needed" — document why)
- NEVER declare mitigation successful without 30+ minutes of stable monitoring
- NEVER skip stakeholder communication for user-facing incidents
- NEVER make architectural decisions during active incident response (fix it, then design it right)
- NEVER let action items go untracked — if due date passes, escalate
- NEVER ignore recurring incidents — same root cause twice = systemic failure to address

## References

- `skills/sdlc-observability.md` — Alerts trigger incident detection, dashboards aid triage
- `skills/sdlc-deployment.md` — Rollback procedures used during mitigation
- `skills/sdlc-maintenance.md` — Action items often become maintenance work
- `skills/sdlc-release-planning.md` — Post-mortem section for release-related incidents
- `steering/orchestration/sdlc-pipeline.md` — Standalone skill, triggered on demand
