---
name: sdlc-team-metrics
description: Use when you need to define, track, or analyze sprint performance metrics for your team. Covers individual and team KPI thresholds (carry-over, velocity, estimate accuracy, blocked time, rework rate), retro preparation with metric dashboards, and estimate accuracy calibration. Trigger phrases include "set up team metrics", "prepare retro data", "our sprints keep slipping", or "how do I track team performance". NOT for coaching conversations or improvement plans (use sdlc-people-management) or sprint capacity planning (use sdlc-sprint-planning).
---

# SDLC Team Metrics & Performance Tracking

## Role & Tone

Act as an engineering analytics specialist. Be precise about thresholds — metrics are inputs to conversations, not verdicts. Frame everything as "the system flagged something" rather than judgment. Distinguish between systemic issues (process) and individual issues (coaching).

## Environment Scope

**write-only** — Writes metric definitions, dashboard specs, and retro prep documents to `<cwd>/drafts/metrics/`. Does NOT query project management tools or modify tickets.

## Workflow

1. **Check Existing State** — Does `<cwd>/drafts/metrics/` exist with prior metric definitions? If yes, determine if updating or creating fresh. Report findings.

2. **Gather Context** — Ask the user:
   > "What do you need?
   > 1. **Define metrics** — Set up KPI thresholds for my team
   > 2. **Retro prep** — Generate a metrics report for an upcoming retrospective
   > 3. **Calibrate estimates** — Our estimates are off, help me recalibrate
   > 4. **Analyze trend** — Something is slipping, help me diagnose"

3. **Execute** — Based on mode, produce the relevant output (see sections below).

4. **Verify** — Confirm all thresholds are internally consistent and actionable.

5. **Await Approval** — Present for user review.

### Failure Recovery (max 3 retries)

4a. Identify inconsistency (threshold too tight/loose, missing metric source)
4b. Adjust based on user feedback
4c. Re-verify
4d. After 3 failures → present options to user

### Rollback

If user cancels: delete files in `<cwd>/drafts/metrics/`, confirm clean state.

---

## Individual Metrics (Triggers Private 1:1 — NEVER Discussed in Retro)

| Metric | How to Measure | Yellow (coaching 1:1) | Red (formal remediation) | Measured Over |
|--------|---------------|----------------------|--------------------------|---------------|
| Personal carry-over rate | Unfinished hours / committed hours × 100 | > 30% for 1 sprint | > 30% for 2 consecutive sprints | Per sprint |
| Estimate accuracy ratio | Actual hours / estimated hours per task | Avg > 1.5× across 5+ tasks | Avg > 2× across 5+ tasks | Rolling 2 sprints |
| Completion rate | Tasks completed / tasks committed | < 70% for 1 sprint | < 70% for 2 consecutive sprints | Per sprint |
| Review revision cycles | "Changes requested" rounds per PR | Avg > 2 across 3+ PRs | Avg > 3 across 5+ PRs | Rolling 2 sprints |
| Blocked duration (self) | Avg days person's tasks in "blocked" state | > 1.5 days avg | > 2.5 days avg | Per sprint |
| WIP violations | Days with > 2 tasks simultaneously "in progress" | > 3 days in sprint | > 5 days in sprint | Per sprint |
| Blocking others | Times this person's incomplete work blocked a teammate | > 2 per sprint | > 3 (critical path) | Per sprint |
| Scope expansion | Hours added to tasks after sprint start (by this person) | > 20% of committed | > 40% of committed | Per sprint |

## Team Metrics (Triggers Retro Discussion or Re-Plan)

| Metric | How to Measure | Yellow (retro topic) | Red (formal re-plan) | Measured Over |
|--------|---------------|---------------------|---------------------|---------------|
| Velocity trend | Delivered hours ÷ committed hours (rolling avg) | Declining 2 sprints | Declining 3 sprints | Rolling 3 |
| Sprint carry-over % | Carried hours / committed hours × 100 | > 20% | > 30% for 2 consecutive | Per sprint |
| Bug escape rate | Bugs found in staging/prod per story | > 1 per story avg | > 2 per story avg | Per sprint |
| Scope injection rate | Hours added mid-sprint / committed × 100 | > 10% | > 20% | Per sprint |
| Average blocked time | Avg days stories spend blocked (team-wide) | > 1 day avg | > 2 days avg | Per sprint |
| DoR violations | Stories pulled without passing Definition of Ready | > 1 per sprint | > 3 per sprint | Per sprint |
| Rework rate | Tasks returned to "in progress" after review/QA | > 15% | > 25% | Per sprint |
| Critical path slip | Days the critical path milestone moved vs plan | > 2 days | > 5 days | Per sprint |

## Conversation Routing

| Metric Color | Who Initiates | Format | Timing |
|-------------|---------------|--------|--------|
| Individual Yellow | Tech Lead | Informal 1:1, 15 min | Within 2 days of sprint end |
| Individual Red | Tech Lead + Eng Manager | Formal 1:1, 30 min | Within 2 days of sprint end |
| Team Yellow | Scrum Master / Tech Lead | Retro agenda item, 10 min | In sprint retro |
| Team Red | Tech Lead + PM + Eng Manager | Dedicated meeting, 45 min | Within 3 days of sprint end |

## Metric Collection Sources

| Source | Who Collects | When | Tool |
|--------|-------------|------|------|
| Hours actual vs estimated | Each engineer logs time | Daily (end of day) | Linear/Jira time tracking |
| PR revision cycles | Automated from SCM | Per PR merge | GitHub/GitLab API |
| Blocked duration | Automated from board transitions | Continuous | Linear/Jira workflow |
| Bugs escaped | QA or automated from bug labels | Per sprint | Bug tracker |
| Scope injection | PM tracks mid-sprint additions | Per addition | Change log |
| Carry-over | Sprint plan vs actuals diff | End of sprint | Sprint review prep |
| WIP violations | Board state snapshot | Daily | Linear/Jira board |

## Retro Prep Document Template

```markdown
## Sprint [X] Metrics Report

### Team Health Dashboard

| Metric | Value | Status | Trend (last 3 sprints) |
|--------|-------|--------|----------------------|
| Velocity | [X]h / [X]h = [X]% | 🟢/🟡/🔴 | ↑ / → / ↓ |
| Carry-over | [X]% | 🟢/🟡/🔴 | ↑ / → / ↓ |
| Bug escape rate | [X] per story | 🟢/🟡/🔴 | ↑ / → / ↓ |
| Avg blocked time | [X] days | 🟢/🟡/🔴 | ↑ / → / ↓ |
| Rework rate | [X]% | 🟢/🟡/🔴 | ↑ / → / ↓ |
| DoR violations | [X] | 🟢/🟡/🔴 | ↑ / → / ↓ |
| Scope injection | [X]% | 🟢/🟡/🔴 | ↑ / → / ↓ |
| Critical path | [on track / +X days] | 🟢/🟡/🔴 | |

### Flagged Items

| Metric | Value | Threshold | Proposed Discussion |
|--------|-------|-----------|---------------------|
| [metric] | [value] | [yellow/red] | [retro topic] |
```

## Estimate Accuracy Tracking

After each sprint, record:

| Sprint | Committed | Delivered | Accuracy % | Velocity Trend |
|--------|-----------|-----------|------------|----------------|
| Sprint N | [X]h | [X]h | [X]% | Baseline |

### Recalibration Rules

- Accuracy < 70% for 2 consecutive sprints → over-estimating capacity or under-estimating tasks
- Apply correction factor: `actual_velocity / planned_velocity`
- Use rolling 3-sprint average for capacity planning
- Feed into risk report: low accuracy = timeline risk

## Carry-Over Thresholds

| Carry-Over % | Action |
|--------------|--------|
| ≤ 20% | Normal — log in retro |
| 21-30% | Warning — retro must identify root cause |
| 31-50% | Re-plan — next sprint lighter, adjust velocity |
| > 50% | Emergency — stop sprint, rerun planning |
| > 30% for 2+ sprints | Formal re-planning, adjust timeline, notify stakeholders |

## Guardrails

- NEVER discuss individual metrics in group retro — private 1:1 only
- NEVER use metrics as punishment — frame as support and obstacle removal
- NEVER cite metrics in a review that weren't tracked transparently from the start
- NEVER use a single sprint's data for performance decisions — minimum 2-sprint pattern
- NEVER compare individuals to each other — compare to own trajectory and role expectations
- NEVER skip metric collection — inconsistent data makes thresholds meaningless

## Direction Disagreement Receipts

When you flag a metric concern and get told to ignore it, document it using the disagreement log in `drafts/performance/disagreement-log.md` (see `sdlc-manager-1on1`). Common metric disagreements to track:

| You Flagged | They Said | Log Because |
|-------------|-----------|-------------|
| "Person X has been red for 2 sprints, needs remediation" | "They're fine, leave it" | If performance worsens, you flagged early and were overruled |
| "Team velocity is declining, we need to re-plan" | "Just push through" | When timeline slips, your data was there |
| "Carry-over is at 35%, we need lighter sprints" | "Commit the same, we can't slip" | When carry-over hits 50%+, your recommendation is timestamped |
| "This metric threshold needs adjustment, it's too lenient" | "It's fine as-is" | When bugs escape or quality drops, you proposed the fix |
| "We need a retro focused on [root cause]" | "Skip it this sprint" | Pattern continues, you tried to intervene |

**Action:** When a metric crosses a threshold and you're told to take no action, send a brief message: "Noting that [metric] crossed [threshold] this sprint. Per our conversation, we're monitoring but not intervening. I'll track for next sprint." That's your CYA without being adversarial.

## References

- `skills/sdlc-sprint-planning.md` — Sprint capacity and ceremony context
- `skills/sdlc-people-management.md` — Coaching and escalation workflows triggered by these metrics
- `steering/orchestration/sdlc-pipeline.md` — Pipeline ordering and rework paths
