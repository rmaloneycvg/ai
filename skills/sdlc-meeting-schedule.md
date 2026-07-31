---
name: sdlc-meeting-schedule
description: Use when you need to plan your meeting schedule for the current project phase, map out all meetings needed, or understand the full SDLC meeting registry. Trigger phrases include "plan my meetings", "what meetings do I need this phase", "map my meeting schedule", or "show me all SDLC meetings". NOT for preparing for a specific meeting (use sdlc-meeting-prep) or figuring out what's next (use sdlc-meeting-prep).
---

# Meeting Schedule Planning

## Role & Tone

Act as a chief of staff who keeps a technical leader's meeting cadence organized and intentional. Prioritize ruthlessly — not every meeting is equal. Flag gaps in meeting coverage (e.g., no retro scheduled, 1:1s overdue). Be direct about what's overdue.

## Environment Scope

**write-only** — Writes meeting schedules and planning documents to `<cwd>/drafts/meetings/`. Does NOT schedule calendar events or send invitations.

## Workflow

1. **Gather Context** — Ask the user:
   > "I need:
   > 1. What SDLC phase is the project in?
   > 2. What's your role? (Tech Lead, EM, IC, PM)
   > 3. How many direct reports?
   > 4. Sprint cadence (length, start day)
   > 5. Any meetings already scheduled?"

2. **Determine Meeting Set** — Based on phase and role, select from the registry (below) which meetings are required, recurring, or triggered.

3. **Produce Schedule** — Generate meeting plan:

   ```markdown
   ## Meeting Plan: [Phase] → [Next Phase]

   ### This Week
   | Day | Meeting | Prep Needed By | Priority |
   |-----|---------|---------------|----------|
   | [Day] | [Meeting] | [Date/time] | [Critical/High/Normal] |

   ### This Sprint
   | Meeting | When | Prep Time | Status |
   |---------|------|-----------|--------|
   | [Meeting] | [Date] | [X] hours | [Not started / In progress / Ready] |

   ### Recurring (Every Sprint)
   | Meeting | Day/Time | Prep Needed | Prep Time |
   |---------|----------|-------------|-----------|
   | Story Refinement | [Day] | Review upcoming stories | 30 min |
   | Sprint Planning | [Day] | Capacity calc, backlog priority | 30 min |
   | Daily Standup | Daily | Blockers list | 5 min |
   | Sprint Review | [Day] | Demo prep or facilitate | 30 min |
   | Sprint Retro | [Day] | Metrics, action items review | 30 min |
   | 1:1s × [N] reports | [Day(s)] | Per-person performance log check | 15 min each |

   ### One-Time (Gate Meetings for Next Phase)
   | Meeting | Target Date | Prep Time | Blocker For |
   |---------|------------|-----------|-------------|
   | [Meeting] | [Date] | [X] hours | [What it unlocks] |
   ```

4. **Flag Gaps** — Identify:
   - Overdue recurring meetings (retro > sprint length, 1:1 > 8 days)
   - Missing gate meetings (artifacts complete but gate not scheduled)
   - Triggered meetings not yet scheduled (metric crossed threshold)

5. **Verify** — Confirm schedule with user. Offer to produce prep docs for upcoming meetings via `sdlc-meeting-prep`.

### Failure Recovery (max 3 retries)

5a. Identify gap (missing phase info, role unclear)
5b. Ask user for clarification
5c. Regenerate schedule
5d. After 3 failures → present partial schedule, note what's missing

### Rollback

If user cancels: delete files created in `<cwd>/drafts/meetings/`, confirm clean state.

---

## Meeting Registry (All SDLC + Coaching Meetings)

### SDLC Pipeline Meetings

| # | Meeting | Phase | Your Role | Prep Time | Frequency |
|---|---------|-------|-----------|-----------|-----------|
| 1 | Project Kickoff | Planning | Present vision, set tone | 2-4 hours | Once |
| 2 | Scope & Requirements Workshop | Planning | Facilitate decisions | 1-2 hours | Once |
| 3 | Technical Feasibility Sync | Planning | Lead technical debate | 2-3 hours | Once |
| 4 | Risk Assessment Workshop | Planning | Identify + own mitigations | 1-2 hours | Once |
| 5 | Go / No-Go Review | Planning | Present recommendation | 1-2 hours | Once |
| 6 | Architecture Review & Stack Sign-Off | Design | Present decisions, defend choices | 3-4 hours | Once |
| 7 | Detailed Design Walkthrough | Design | Walk team through architecture | 2-3 hours | Once |
| 8 | Epic Review & Estimation | Epic Planning | Present epics, facilitate estimation | 2-3 hours | Once |
| 9 | Story Refinement | Sprint (recurring) | Clarify stories, validate readiness | 30-60 min | Every sprint |
| 10 | Sprint Planning | Sprint (recurring) | Commit to scope, assign work | 30-60 min | Every sprint |
| 11 | Daily Standup | Sprint (recurring) | Listen for blockers, unblock | 5 min | Daily |
| 12 | Sprint Review / Demo | Sprint (recurring) | Demo or facilitate demos | 30-60 min | Every sprint |
| 13 | Sprint Retrospective | Sprint (recurring) | Facilitate or participate | 30 min prep | Every sprint |
| 14 | Release Readiness Review | Release | Present release criteria status | 1-2 hours | Per release |
| 15 | Post-Release Retrospective | Release | Facilitate lessons learned | 30 min | Per release |
| 16 | Incident Post-Mortem | Release (if needed) | Lead blameless analysis | 1-2 hours | As needed |

### People & Coaching Meetings

| # | Meeting | Context | Your Role | Prep Time | Frequency |
|---|---------|---------|-----------|-----------|-----------|
| 17 | Weekly 1:1 (direct report) | Ongoing | Coach, listen, unblock | 15-30 min per person | Weekly |
| 18 | Coaching / Yellow Metric 1:1 | Triggered by metric | Surface concern, offer support | 30-60 min | As triggered |
| 19 | Formal Remediation 1:1 | Triggered by red metric | Present data, set improvement plan | 1-2 hours | As triggered |
| 20 | Escalation to Eng Manager | Triggered by plan failure | Present case, recommend action | 2-3 hours | As triggered |
| 21 | Promotion Advocacy | Triggered by sustained excellence | Present evidence, make the case | 2-4 hours | As earned |
| 22 | Skip-level (your manager's manager) | Relationship building | Share wins, flag risks early | 15-30 min | Monthly/quarterly |
| 23 | Stakeholder Update | Project communication | Status, risks, decisions needed | 30-60 min | Biweekly/as needed |

### Ad-Hoc Meetings

| # | Meeting | Context | Prep Time |
|---|---------|---------|-----------|
| 24 | Vendor/partner sync | Procurement, integration coordination | 30-60 min |
| 25 | Cross-team dependency check | Another team owns something you need | 15-30 min |
| 26 | Architecture Decision (ADR) | Mid-project technical pivot | 1-2 hours |
| 27 | Change Request Review | Scope change evaluation | 30-60 min |
| 28 | Hiring kickoff / interview debrief | Team growth | 30 min |

---

## Phase → Meeting Mapping

| Phase Just Completed | Next Gate Meeting | Prep Skill |
|---------------------|-------------------|------------|
| Planning artifacts done | Go/No-Go Review | `sdlc-meeting-prep` |
| Stack selection done | Architecture Review & Sign-Off | `sdlc-meeting-prep` |
| Detailed design done | Design Walkthrough | `sdlc-meeting-prep` |
| Epic planning done | Epic Review & Estimation | `sdlc-meeting-prep` |
| Sprint planning done | Sprint ceremonies begin | `sdlc-meeting-prep` |
| QA sign-off done | Release Readiness Review | `sdlc-meeting-prep` |
| Deployment done | Post-Release Retro (1 week later) | `sdlc-meeting-prep` |

## Guardrails

- NEVER plan a schedule without knowing the current phase and role
- NEVER omit recurring meetings from the schedule (they're easy to forget)
- NEVER let gate meetings go unscheduled when artifacts are complete
- NEVER skip 1:1s in the schedule — they are the highest-ROI meeting a Tech Lead has
- NEVER schedule meetings without time allocated for prep
- NEVER leave triggered meetings (metrics, incidents) unscheduled for >2 days

## References

- `skills/sdlc-meeting-prep.md` — Prepare for a specific meeting from this schedule
- `skills/sdlc-sprint-planning.md` — Sprint ceremony timing
- `skills/sdlc-team-metrics.md` — Metric thresholds that trigger coaching meetings
- `skills/sdlc-people-management.md` — Coaching meeting context
- `steering/orchestration/sdlc-pipeline.md` — Phase ordering determines meeting sequence
