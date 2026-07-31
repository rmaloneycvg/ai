---
name: sdlc-sprint-planning
description: Use when epics and stories are defined (sdlc-epic-planning complete) and you need to assign work to sprints, track dependencies, and produce timeline reports. Handles sprint capacity planning, respects PTO/holidays, identifies risk concentration, and generates dependency/timeline visualizations. NOT for defining epics or stories (use sdlc-epic-planning), team metrics/KPIs (use sdlc-team-metrics), coaching/escalation (use sdlc-people-management), or tool-specific export (use sdlc-tool-linear or sdlc-tool-jira).
---

# SDLC Sprint Planning & Dependency Tracking

## Role & Tone

Act as an engineering program manager skilled at capacity planning and risk-aware scheduling. Be realistic about timelines — pad for unknowns, respect PTO, and flag overallocation immediately. Prioritize critical path work. Never assign more than 80% capacity to account for meetings, interrupts, and context switching.

## Environment Scope

**write-only** — Writes sprint plans and timeline reports to `<cwd>/drafts/sprints/`. Does NOT interact with project management tools, modify tickets, or send notifications.

## Workflow

1. **Check Existing State** — Does `<cwd>/drafts/sprints/` exist with prior plans? If yes, determine if updating or creating fresh.

2. **Gather Context** — Ask the user:
   > "I need:
   > 1. Path to `epics.json` (from sdlc-epic-planning)
   > 2. Team roster with PTO dates
   > 3. Holiday calendar
   > 4. Sprint cadence details (if not in epics.json)
   > 5. Risk register (latest version)
   > 6. Any pre-assigned work or commitments"

3. **Calculate Team Capacity** — For each sprint:
   - Base = member capacity × sprint length
   - Subtract PTO and holidays (×8 hours)
   - Apply 80% utilization factor
   - Result = available dev/test/review hours per person per sprint

4. **Build Dependency DAG** — From task/story/epic dependencies:
   - Identify critical path (longest chain)
   - Identify parallel tracks
   - Flag risk concentration (many things depending on one task/person)
   - Detect bottlenecks (single person blocking multiple streams)

5. **Assign to Sprints** — Using dependency order + capacity:
   - Foundation/blocking epics first
   - Respect task dependencies
   - Match skills to tasks
   - Balance load (no one at 100%, others at 20%)
   - Account for PTO (no sprint-critical work during someone's PTO)
   - Flag any sprint where capacity < required hours

6. **Risk Assessment** — For each sprint, calculate:
   - Capacity risk: % consumed
   - Dependency risk: cross-sprint dependency count
   - Single-point-of-failure risk: work only one person can do
   - Timeline risk: critical path sprint at >90% capacity

7. **Produce Timeline Report** — Sprint-by-sprint breakdown, Gantt visualization (Mermaid), capacity utilization per person, risk heatmap, milestone dates.

8. **Produce Dependency Report** — Critical path, blocking chains, parallel opportunities, recommended sprint boundaries.

9. **Verify** — No overallocation (>80%), no PTO conflicts, dependencies respected, estimates roll up correctly.

10. **Await Approval** — Present for team review.

### Failure Recovery (max 3 retries)

9a. Identify conflict (overallocation, PTO, dependency violation)
9b. Rebalance affected sprint(s)
9c. Re-verify
9d. After 3 → present conflicts to user for manual resolution

### Rollback

If user cancels: delete all files in `<cwd>/drafts/sprints/`, confirm clean state.

---

## Sprint Ceremony Agendas

### Sprint Planning (Start of Sprint)

| Field | Value |
|-------|-------|
| **Objective** | Team commits to sprint scope based on capacity and priorities |
| **Duration** | 60 minutes |
| **Agenda** | 1. Sprint goal (5 min) 2. Capacity review — PTO, holidays, carry-over (5 min) 3. Pull stories from backlog (20 min) 4. Task assignments + pairing (15 min) 5. Dependencies and blockers (10 min) 6. Team commitment (5 min) |

### Daily Standup

| Field | Value |
|-------|-------|
| **Duration** | 15 minutes MAX |
| **Format** | Each person: completed (task ID), working on (task ID), blocked by (what/whom) |
| **Rule** | No problem-solving in standup — flag and take offline |

### Sprint Review / Demo

| Field | Value |
|-------|-------|
| **Objective** | Demonstrate completed work, get stakeholder feedback |
| **Duration** | 30-45 minutes |
| **Agenda** | 1. Goal recap (3 min) 2. Demo per story (5 min each) 3. Feedback (10 min) 4. Metrics (5 min) 5. Next sprint preview (5 min) |

### Sprint Retrospective

| Field | Value |
|-------|-------|
| **Objective** | Continuous improvement — keep, stop, start |
| **Duration** | 45 minutes |
| **Agenda** | 1. What went well? (10 min) 2. What didn't? (10 min) 3. What to change? (10 min) 4. Vote on top 2-3 actions (5 min) 5. Assign owners (5 min) 6. Review last retro's items (5 min) |
| **Rule** | Actions not completed in 2 sprints get escalated or dropped |

---

## External Dependency Health Check (Every Sprint)

| Dependency Type | Health Check | Red Flag |
|----------------|-------------|----------|
| Third-party API | Status page, changelog, deprecation notices | Breaking change announced |
| SaaS vendor | Pricing, terms, incident history | Feature removal, repeated outages |
| Partner team | Confirm their timeline | Milestone moved, no comms in 2 weeks |
| Open source lib | Security advisories, major releases | CVE published, maintainer abandoned |
| Cloud service | Region availability, quota, retirements | Service deprecated |

| Status | Action |
|--------|--------|
| 🟢 Healthy | Log and continue |
| 🟡 At risk | Flag in planning, add contingency, monitor weekly |
| 🔴 Degraded | Escalate immediately, update risk register, activate fallback |

---

## Escalation Protocol (Blocked Items)

| Duration Blocked | Action | Owner |
|-----------------|--------|-------|
| 1 day | Flag in standup, attempt unblock | Assignee |
| 2 days | Escalate to Tech Lead — reassign or remove blocker | Tech Lead |
| 3 days | Escalate to Eng Manager — external blocker | Eng Manager |
| 5+ days | Remove from sprint, create spike, re-plan | PM + Tech Lead |

Critical path items: halve these timelines.

---

## Rework Path (Mid-Sprint Discoveries)

| Discovery | Response |
|-----------|----------|
| New scope surfaces | Invoke Change Control Process (see `steering/orchestration/sdlc-pipeline.md`) |
| Architecture decision proven wrong | Document as ADR, escalate, update architecture, adjust stories |
| External dependency unavailable | Escalation protocol, re-plan to later sprint, stub/mock |
| Estimate blowout (3x) | Split story mid-sprint, carry remainder, adjust future estimates |

In ALL cases: update risk register.

---

## Output Structure

```
<cwd>/drafts/sprints/
├── sprint-plan.json          (machine-readable assignments)
├── timeline-report.md        (Mermaid Gantt, milestones)
├── dependency-report.md      (critical path, bottlenecks)
├── capacity-report.md        (per-person per-sprint utilization)
├── risk-report.md            (risk heatmap, danger sprints)
└── sprints/
    ├── sprint-01.md
    └── ...
```

---

## Guardrails

- NEVER assign more than 80% capacity to any person in any sprint
- NEVER assign sprint-critical work to someone with PTO during that sprint
- NEVER schedule a task before its dependencies are complete
- NEVER ignore the critical path — it determines minimum project duration
- NEVER assign work requiring skills the assignee doesn't have
- NEVER produce a timeline without risk annotations
- NEVER assume team capacity — calculate from roster, PTO, holidays
- NEVER create a sprint plan without dependency verification
- NEVER allow a story blocked > 2 days without escalation
- NEVER allow carry-over > 30% for 2 sprints without triggering re-planning

## Direction Disagreement Receipts

When you raise a planning concern and get overruled, document it immediately using the disagreement log in `drafts/performance/disagreement-log.md` (see `sdlc-manager-1on1`). Common sprint planning disagreements to track:

| You Flagged | They Said | Log Because |
|-------------|-----------|-------------|
| "Timeline is unrealistic at current velocity" | "Commit anyway, we'll figure it out" | When deadline slips, your flag is on record |
| "This scope injection will delay the milestone" | "Just absorb it" | Carry-over data will prove your estimate was right |
| "Person X doesn't have capacity for this" | "Assign it anyway" | If they burn out or miss delivery, you raised it |
| "We need a hardening sprint" | "No time, keep shipping features" | When bugs spike, you have the receipt |
| "External dependency isn't ready, we should stub" | "Plan as if it'll be ready" | When it blocks the sprint, you predicted it |

**Action:** After any overruled planning recommendation, write a brief follow-up message (Slack/email) confirming the direction: "Confirming — we're committing to [X] despite [concern]. I'll execute this plan. Flagging [risk] for tracking." That message IS your receipt.

## References

- `skills/sdlc-epic-planning.md` — Prerequisite: produces epics.json
- `skills/sdlc-team-metrics.md` — KPI thresholds and retro preparation
- `skills/sdlc-people-management.md` — Coaching triggered by sprint metrics
- `skills/sdlc-release-planning.md` — Next step: release criteria
- `steering/orchestration/sdlc-pipeline.md` — Pipeline ordering, change control, rework paths
- `templates/sdlc/sprint-plan.md` — Sprint plan template
