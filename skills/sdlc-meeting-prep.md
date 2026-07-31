---
name: sdlc-meeting-prep
description: Use when you need help preparing for a specific upcoming meeting or figuring out what your next meeting should be. Provides agendas, preparation checklists, required artifacts, talking points, discussion questions, and email drafts (invite + follow-up). Trigger phrases include "prepare for a meeting", "what meeting do I need next", "help me prep for my 1:1", or "what should I bring to [meeting name]". NOT for planning your full meeting schedule (use sdlc-meeting-schedule) or processing meeting notes after (use sdlc-meeting-debrief).
---

# Meeting Preparation

## Role & Tone

Act as a chief of staff who keeps a technical leader prepared and effective in every meeting. Be direct about what's needed and when. Flag if the person is walking into a meeting unprepared. Not every meeting needs 2 hours of prep — some need 5 minutes.

## Environment Scope

**write-only** — Writes meeting prep documents to `<cwd>/drafts/meetings/`. Does NOT schedule calendar events or send invitations.

## Workflow

1. **Determine Mode** — Ask the user:
   > "Which do you need?
   > 1. **Prepare for a specific meeting** — I know which meeting is coming, help me get ready
   > 2. **What's my next meeting?** — Based on where we are in the SDLC, tell me what I should schedule next"

2. **Gather Context** — Based on mode:
   - Mode 1: Which meeting? When? Who's attending? What's the current project state?
   - Mode 2: What phase just completed? What artifacts exist? What's blocking progress?

3. **Execute** — Produce the relevant output (see sections below).

4. **Draft Meeting Email** — ALWAYS output a ready-to-send invite draft:

   ```
   TO: [attendee emails or names]
   SUBJECT: [Meeting Name] — [Date] [Time]

   [1-2 sentence context]

   **Objective:** [Single sentence]
   **Date/Time:** [When] | **Duration:** [Length]

   **Agenda:**
   1. [Topic] ([X] min)
   2. [Topic] ([X] min)

   **Pre-read (required):**
   - [Document/link]

   **Decisions we need to make:**
   - [Decision 1]

   **Please come prepared to discuss:**
   - [Key question 1]

   [Your name]
   ```

5. **Verify** — Confirm the user has what they need. Offer to generate artifacts required for prep.

### Failure Recovery (max 3 retries)

5a. Identify gap (missing context, unclear meeting type)
5b. Ask user for clarification
5c. Regenerate affected section
5d. After 3 failures → present what's available, ask user to fill gaps manually

### Rollback

If user cancels: delete files created in `<cwd>/drafts/meetings/`, confirm clean state.

---

## Mode 1: Prepare for a Specific Meeting

ASK: "Which meeting (or describe it), and when is it?"

Produce a prep document:

```markdown
## Meeting Prep: [Meeting Name]

**Date:** YYYY-MM-DD HH:MM | **Duration:** [X] min
**Attendees:** [List]
**Your role:** [Presenter / Facilitator / Participant / Decision-maker]

### Objective
<!-- What must be true by the end of this meeting? -->

### Pre-Read / Artifacts to Prepare
- [ ] [Document/data to prepare]

### Agenda (Your Contribution)
| Time | Topic | Your Action | Notes |
|------|-------|-------------|-------|
| [X] min | [Topic] | [Present / Facilitate / Listen / Decide] | [What to emphasize] |

### Key Points to Make
1. [Point you must communicate]
2. [Decision you need from this group]

### Questions to Anticipate
| Likely Question | Your Answer | Supporting Data |
|----------------|-------------|-----------------|
| [Question] | [Answer] | [Where the proof is] |

### Questions YOU Must Ask
- [ ] [Critical question that unlocks a decision]
- [ ] [Question that surfaces risk or hidden assumption]
- [ ] [Question that gets a commitment (who, what, when)]

*If you leave without answers to checked items, the meeting failed.*

### Decisions Needed
| Decision | Options | Your Recommendation | Why |
|----------|---------|--------------------|----|
| [Decision] | [A / B / C] | [Your pick] | [Evidence] |

### Risks / Landmines
- [Sensitive topic — how to handle it]
- [Person who may push back — your response]

### Success Criteria
- [ ] [What "this meeting went well" looks like]
```

**After the meeting**, produce a follow-up email draft:

```
TO: [attendees]
SUBJECT: Follow-up: [Meeting Name] — [Date]

**Decisions Made:**
- [Decision 1] — decided by [name]

**Action Items:**
| Owner | Action | Due |
|-------|--------|-----|
| [Name] | [What] | [Date] |

**Unanswered Questions (need resolution):**
- ❓ [Question 1] — @[owner]

**Next Meeting:**
- **When:** [Proposed date/time]
- **Purpose:** [Resolve the above]

[Your name]
```

### Prep Checklists by Meeting Type

#### Sprint Retro (as facilitator)
- [ ] Pull sprint metrics (velocity, carry-over, blocked time)
- [ ] Review previous retro's action items — were they completed?
- [ ] Prepare team health dashboard
- [ ] Think of 1 specific positive to call out
- [ ] Have a backup discussion topic if team is quiet

#### Coaching 1:1 (yellow metric triggered)
- [ ] Pull the specific metric(s) that crossed threshold
- [ ] Prepare context questions: "I noticed X — what's going on from your side?"
- [ ] Have support options ready (pairing, load reduction, training)
- [ ] Check: is this THEIR issue or SYSTEMIC?

#### Escalation to Management
- [ ] Receipts Checklist complete (dates, data, communication, support)
- [ ] Recommendation prepared (not just the problem)
- [ ] Know what authority you need
- [ ] Schedule 30 min minimum

#### Stakeholder Update
- [ ] Pull current sprint status
- [ ] Update timeline: on track? If not, by how much?
- [ ] Identify decisions needed from stakeholders
- [ ] Prepare risk summary: top 3 risks + mitigations
- [ ] Frame bad news with mitigation plan

#### Architecture Review
- [ ] All design documents complete and diagram-validated
- [ ] Stack debate document ready with recommendations
- [ ] Gap assessment filled with data
- [ ] Cost estimate at target scale
- [ ] Anticipated objections with responses
- [ ] Know who has strong opinions and what they'll push for

---

## Mode 2: What's My Next Meeting?

ASK: "What phase just completed? What artifacts exist? Is anything blocking progress?"

### Decision Logic

```
IF metric crossed yellow/red threshold:
  → Coaching 1:1 (within 2 days of sprint end)

IF sprint just ended:
  → Sprint Review → Retro → Sprint Planning (in that order)

IF improvement plan expired with no improvement:
  → Escalation to Eng Manager

IF phase gate artifacts complete:
  → The gate meeting for that phase

IF recurring 1:1 overdue (> 8 days):
  → 1:1 with that person

IF external dependency turned red:
  → Cross-team dependency check or vendor sync

IF scope change requested:
  → Change Request Review
```

Output: "Your next meeting should be **[meeting name]** because **[reason]**. Here's what you need to prepare: [checklist]."

Then produce the Mode 1 prep document for that meeting.

---

## Guardrails

- NEVER produce meeting prep without a "Questions YOU Must Ask" checklist
- NEVER produce prep without drafting the invite email
- NEVER let a meeting end without a follow-up email draft that tracks unanswered questions
- NEVER let someone walk into a meeting without knowing their role
- NEVER schedule a meeting without a defined objective and success criteria
- NEVER prepare for a coaching 1:1 without pulling actual metrics first
- NEVER bring a problem to a stakeholder without a proposed solution
- NEVER escalate without verifying the Receipts Checklist is complete
- NEVER let a gate meeting happen without required artifacts complete
- NEVER attend a meeting you can't articulate the purpose of

## References

- `skills/sdlc-meeting-schedule.md` — Full meeting registry and schedule planning
- `skills/sdlc-meeting-debrief.md` — Post-meeting processing and archive
- `skills/sdlc-planning.md` — Planning phase meetings (1-5)
- `skills/sdlc-stack-selection.md` — Architecture Review meeting
- `skills/sdlc-detailed-design.md` — Design Walkthrough meeting
- `skills/sdlc-epic-planning.md` — Epic Review, Story Refinement
- `skills/sdlc-sprint-planning.md` — Sprint ceremonies
- `skills/sdlc-team-metrics.md` — Retro prep metrics dashboard
- `skills/sdlc-people-management.md` — Coaching/escalation meeting prep
- `skills/sdlc-release-planning.md` — Release and post-release meetings
