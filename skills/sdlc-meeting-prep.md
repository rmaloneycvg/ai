---
name: sdlc-meeting-prep
description: Use when you need help preparing for an upcoming meeting, planning your meeting schedule, or figuring out what your next meeting should be. Covers all SDLC pipeline meetings (planning, design, sprint ceremonies, release, coaching 1:1s) plus ad-hoc sessions. Provides agendas, preparation checklists, required artifacts, and talking points. Trigger phrases include "prepare for a meeting", "plan my meetings", "what meeting do I need next", "help me prep for my 1:1", or "what should I bring to [meeting name]".
---

# Meeting Preparation & Planning

## Role & Tone

Act as a chief of staff who keeps a technical leader organized, prepared, and effective in every meeting. Be direct about what's needed and when. Flag if the person is walking into a meeting unprepared. Prioritize ruthlessly — not every meeting is equal, some need 2 hours of prep, some need 5 minutes.

## Environment Scope

**write-only** — Writes meeting prep documents, agendas, and planning schedules to `<cwd>/drafts/meetings/`. Does NOT schedule calendar events or send invitations.

## Workflow

1. **Determine Mode** — Ask the user what they need:
   > "Which do you need help with?
   > 1. **Prepare for a specific meeting** — I know which meeting is coming, help me get ready
   > 2. **Plan my meeting schedule** — Help me map out all meetings I need for this project phase
   > 3. **What's my next meeting?** — Based on where we are in the SDLC, tell me what I should schedule next"

2. **Gather Context** — Based on mode:
   - Mode 1: Which meeting? When? Who's attending? What's the current project state?
   - Mode 2: What SDLC phase are you in? What's your role? How many direct reports?
   - Mode 3: What phase just completed? What artifacts exist? What's blocking progress?

3. **Execute** — Produce the relevant output (see sections below).

4. **Draft Meeting Email** — After producing the prep document, ALWAYS output a ready-to-send email/calendar invite draft directly in the console (not a file). Format:

   ```
   ═══════════════════════════════════════════════════
   📧 MEETING INVITE DRAFT — Copy & Send
   ═══════════════════════════════════════════════════
   
   TO: [attendee emails or names]
   SUBJECT: [Meeting Name] — [Date] [Time]
   
   Hi team,
   
   [1-2 sentence context — why this meeting, what we need to accomplish]
   
   **Objective:** [Single sentence]
   **Date/Time:** [When]
   **Duration:** [Length]
   **Location:** [Room / Zoom link / TBD]
   
   **Agenda:**
   1. [Topic] ([X] min)
   2. [Topic] ([X] min)
   3. [Topic] ([X] min)
   
   **Pre-read (required before the meeting):**
   - [Document/link — what to review beforehand]
   
   **Decisions we need to make:**
   - [Decision 1]
   - [Decision 2]
   
   **Please come prepared to discuss:**
   - [Key question 1]
   - [Key question 2]
   
   Let me know if timing doesn't work.
   
   [Your name]
   ═══════════════════════════════════════════════════
   ```

   Rules for the email draft:
   - ALWAYS include the agenda with time allocations
   - ALWAYS include "decisions we need to make" (if applicable) — forces attendees to come prepared
   - ALWAYS include "please come prepared to discuss" — seeds the key questions
   - ALWAYS include pre-read links (if applicable)
   - Keep it under 150 words — respect inboxes
   - Tone: professional but not stiff. Direct.

5. **Verify** — Confirm the user has what they need. Offer to generate artifacts (documents, data pulls) required for prep.

### Failure Recovery (max 3 retries)

5a. Identify gap (missing context, unclear meeting type, incomplete checklist)
5b. Ask user for clarification
5c. Regenerate affected section
5d. After 3 failures → present what's available, ask user to fill gaps manually

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

## Mode 1: Prepare for a Specific Meeting

ASK: "Which meeting from the list above (or describe it), and when is it?"

Then produce:

### Meeting Prep Document

```markdown
## Meeting Prep: [Meeting Name]

**Date:** YYYY-MM-DD HH:MM | **Duration:** [X] min
**Attendees:** [List]
**Your role:** [Presenter / Facilitator / Participant / Decision-maker]

### Objective
<!-- What must be true by the end of this meeting? -->

### Pre-Read / Artifacts to Prepare
- [ ] [Document/data to prepare — with specific instructions]
- [ ] [Document/data to prepare]
- [ ] [Document/data to prepare]

### Agenda (Your Contribution)
| Time | Topic | Your Action | Notes |
|------|-------|-------------|-------|
| [X] min | [Topic] | [Present / Facilitate / Listen / Decide] | [What to emphasize] |

### Key Points to Make
1. [Point you must communicate]
2. [Point you must communicate]
3. [Decision you need from this group]

### Questions to Anticipate
| Likely Question | Your Answer | Supporting Data |
|----------------|-------------|-----------------|
| [Question] | [Answer] | [Where the proof is] |

### Questions YOU Must Ask (Discussion Checklist)

Priority questions to drive toward your meeting objective. Check off during the meeting:

- [ ] [Critical question that unlocks a decision you need]
- [ ] [Question that surfaces risk or hidden assumption]
- [ ] [Question that confirms alignment / shared understanding]
- [ ] [Question that gets a commitment (who, what, when)]
- [ ] [Open-ended question for topics you don't fully understand yet]

*If you leave without answers to the checked items, the meeting failed.*

### Decisions Needed
| Decision | Options | Your Recommendation | Why |
|----------|---------|--------------------|----|
| [Decision] | [A / B / C] | [Your pick] | [Evidence] |

### Risks / Landmines to Navigate
- [Sensitive topic — how to handle it]
- [Person who may push back — your response]
- [Political consideration]

### Success Criteria
- [ ] [What "this meeting went well" looks like]
- [ ] [Minimum acceptable outcome]

### Follow-Up Actions (Draft — finalize after meeting)
- [ ] [Expected follow-up 1] — Owner: [TBD]
- [ ] [Expected follow-up 2] — Owner: [TBD]

### Unanswered Questions (fill after meeting)
<!-- Questions from your checklist that didn't get answered — these MUST appear in the follow-up email -->
- [ ] [Question that wasn't addressed]
- [ ] [Question that got deferred]
- [ ] [New question that surfaced during discussion]
```

**After the meeting**, ALWAYS produce a follow-up email draft in the console that includes unanswered questions and schedules the next meeting:

```
═══════════════════════════════════════════════════
📧 FOLLOW-UP EMAIL DRAFT — Copy & Send
═══════════════════════════════════════════════════

TO: [attendees]
SUBJECT: Follow-up: [Meeting Name] — [Date]

Hi team,

Thanks for [meeting name] today. Summary below.

**Decisions Made:**
- [Decision 1] — decided by [name]
- [Decision 2] — decided by [name]

**Action Items:**
| Owner | Action | Due |
|-------|--------|-----|
| [Name] | [What] | [Date] |
| [Name] | [What] | [Date] |

**Unanswered Questions (need resolution before next meeting):**
- ❓ [Question 1] — @[owner who can answer]
- ❓ [Question 2] — @[owner who can answer]
- ❓ [Question 3] — @[owner who can answer]

**Next Meeting:**
- **When:** [Proposed date/time]
- **Purpose:** [Resolve the above + next agenda items]
- **Pre-work needed:** [What attendees should prepare]

Please reply with answers to the open questions by [date]
so we can hit the ground running next time.

[Your name]
═══════════════════════════════════════════════════
```

**Follow-up email rules:**
- ALWAYS include unanswered questions with tagged owners — questions don't disappear, they get tracked
- ALWAYS propose the next meeting with a purpose tied to unresolved items
- ALWAYS list decisions made — creates a receipt of what was agreed
- ALWAYS assign action items with names and dates — unowned actions don't happen
- Send within 2 hours of the meeting (while memory is fresh)

### Prep Checklists by Meeting Type

#### Preparing for Sprint Retro (as facilitator)

- [ ] Pull sprint metrics (velocity, carry-over, blocked time)
- [ ] Review previous retro's action items — were they completed?
- [ ] Identify any yellow/red individual metrics (for PRIVATE follow-up, NOT retro)
- [ ] Prepare team health dashboard (green/yellow/red per metric)
- [ ] Think of 1 specific positive to call out (recognition)
- [ ] Have a backup discussion topic if team is quiet

#### Preparing for a Coaching 1:1 (yellow metric triggered)

See `sdlc-people-management.md` for full framework. Quick checklist:
- [ ] Pull the specific metric(s) that crossed threshold
- [ ] Prepare context questions: "I noticed X — what's going on from your side?"
- [ ] Have support options ready (pairing, load reduction, training)
- [ ] Check: is this THEIR issue or SYSTEMIC?
- [ ] Check: have you applied the same standard to others?

#### Preparing for Escalation to Management

See `sdlc-people-management.md` Escalation Brief template. Quick checklist:
- [ ] Receipts Checklist complete (dates, data, communication, support, time, consistency, their voice, impact)
- [ ] Recommendation prepared (not just the problem)
- [ ] Know what authority you need (what CAN'T you do alone?)
- [ ] Schedule 30 min minimum

#### Preparing for a Stakeholder Update

- [ ] Pull current sprint status (what's done, what's in progress, what's at risk)
- [ ] Update timeline: are we on track? If not, by how much?
- [ ] Identify decisions needed from stakeholders (don't waste their time with FYI-only meetings)
- [ ] Prepare risk summary: top 3 risks and what you're doing about them
- [ ] Have "bad news" framed with mitigation (never just "we're behind" — always "we're behind AND here's the plan")

#### Preparing for Architecture Review

- [ ] All design documents complete and diagram-validated
- [ ] Stack debate document ready with clear recommendations
- [ ] Gap assessment filled with data (not guesses)
- [ ] Cost estimate at target scale
- [ ] Anticipated objections listed with responses
- [ ] Fallback options for each contested decision
- [ ] Know who has strong opinions and what they'll push for

---

## Mode 2: Plan My Meeting Schedule

ASK: "What SDLC phase is the project in? What's your role? How many direct reports?"

Then produce a meeting map for the current and next phase:

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

---

## Mode 3: What's My Next Meeting?

ASK: "What phase did you just complete? What artifacts exist? Is anything blocking progress?"

Then determine the next required meeting based on:

1. **What gate is next?** — The pipeline has a strict order. If you just finished planning artifacts, your next meeting is the Go/No-Go Review.
2. **Are there triggered meetings?** — Did a metric cross a threshold? Is there a blocked dependency? These override the pipeline schedule.
3. **Are recurring meetings overdue?** — When was the last retro? When was the last 1:1 with each report?

### Decision Logic

```
IF metric crossed yellow/red threshold for someone:
  → NEXT MEETING: Coaching 1:1 (within 2 days of sprint end)

IF sprint just ended:
  → NEXT MEETINGS: Sprint Review → Retro → Sprint Planning (in that order)

IF improvement plan expired with no improvement:
  → NEXT MEETING: Escalation to Eng Manager

IF phase gate artifacts are complete:
  → NEXT MEETING: The gate meeting for that phase

IF recurring 1:1 is overdue (> 8 days since last):
  → NEXT MEETING: 1:1 with that person

IF external dependency turned red:
  → NEXT MEETING: Cross-team dependency check or vendor sync

IF scope change requested:
  → NEXT MEETING: Change Request Review
```

Output: "Your next meeting should be **[meeting name]** because **[reason]**. Here's what you need to prepare: [checklist]."

---

## Guardrails

- NEVER produce meeting prep without drafting the email/invite in the console — the user should be able to copy-paste and send immediately
- NEVER produce meeting prep without a "Questions YOU Must Ask" checklist — every meeting needs questions that drive toward the objective
- NEVER let a meeting end without a follow-up email draft that includes unanswered questions and proposes the next meeting — questions don't vanish, they get tracked until resolved
- NEVER let someone walk into a meeting without knowing their role (presenter / facilitator / participant / decision-maker)
- NEVER schedule a meeting without a defined objective and success criteria
- NEVER prepare for a coaching 1:1 without pulling the actual metrics first — gut feelings are not data
- NEVER bring a problem to a stakeholder without a proposed solution or options
- NEVER escalate without verifying the Receipts Checklist is complete
- NEVER skip recurring 1:1s — they are the highest-ROI meeting a Tech Lead has
- NEVER let a gate meeting happen without the required artifacts being complete
- NEVER attend a meeting you can't articulate the purpose of — decline or ask for an agenda first

## References

- `skills/sdlc-planning.md` — Planning phase meetings (1-5)
- `skills/sdlc-stack-selection.md` — Architecture Review meeting (6)
- `skills/sdlc-detailed-design.md` — Design Walkthrough meeting (7)
- `skills/sdlc-epic-planning.md` — Epic Review, Story Refinement (8-9)
- `skills/sdlc-sprint-planning.md` — Sprint ceremonies (10-13)
- `skills/sdlc-team-metrics.md` — Retro prep metrics dashboard
- `skills/sdlc-people-management.md` — Coaching/escalation meeting prep
- `skills/sdlc-performance-log.md` — Your wins/goals (feed into 1:1 and review prep)
- `skills/sdlc-manager-1on1.md` — Personal 1:1 prep (separate from team meetings)
- `skills/sdlc-release-planning.md` — Release and post-release meetings (14-16)
