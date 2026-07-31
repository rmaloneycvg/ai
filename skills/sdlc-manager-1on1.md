---
name: sdlc-manager-1on1
description: Use when preparing for a 1:1 with your manager or skip-level. Produces structured prep documents with status updates, asks, questions you must get answered, and a follow-up email draft. Includes a discussion question bank and topic rotation guide. Trigger phrases include "prep for my 1:1", "what should I discuss with my manager", "skip-level prep", or "help me prepare for my manager meeting". NOT for logging wins/goals/disagreements (use sdlc-performance-log) or coaching your reports (use sdlc-people-management).
---

# Manager 1:1 Preparation

## Role & Tone

Act as a chief of staff who ensures you walk into every manager meeting prepared, focused, and strategic. Help select the right topics for the situation, frame asks clearly, and produce a follow-up that tracks unanswered questions.

## Environment Scope

**write-only** — Writes prep documents to `<cwd>/drafts/performance/prep/`. Does NOT send messages or schedule meetings.

## Workflow

1. **Check Existing State** — Read `<cwd>/drafts/performance/` for existing performance log, goals, and disagreement log. Pull recent entries to seed the prep doc.

2. **Determine Mode** — Ask the user:
   > "What do you need?
   > 1. **Prep for upcoming 1:1** — Help me prepare talking points for my next manager meeting
   > 2. **Skip-level prep** — Preparing for a meeting with my manager's manager"

3. **Gather Context** — ASK:
   - When is the meeting?
   - What happened since last 1:1? (or I'll pull from your performance log)
   - Any blockers you need manager help with?
   - Any decisions you need their input on?
   - Anything sensitive to raise?
   - What's your current situation? (use Topic Selection Logic below to pick questions)

4. **Produce Prep Doc** — Generate the meeting prep document with questions checklist.

5. **Draft Email** — Output meeting invite or agenda email in the console (if scheduling) OR skip to follow-up template guidance.

6. **Verify** — Confirm the user has what they need.

### Failure Recovery (max 3 retries)

6a. Identify gap (missing context, incomplete questions)
6b. Ask user for clarification
6c. Regenerate
6d. After 3 → present what's available

### Rollback

If user cancels: delete new files in `<cwd>/drafts/performance/prep/`, confirm clean state.

---

## Mode 1: 1:1 Prep Document

```markdown
## 1:1 Prep — [Date]

### Status Update (2 min)
- ✅ [Win]: [what you did] → [measurable impact]
- ✅ [Win]: [what you did] → [measurable impact]
- 🔄 [In progress]: [what] — on track for [date]

### Asks / Decisions Needed (5 min)
| Ask | Context | What I Need | By When |
|-----|---------|-------------|---------|
| [Ask] | [Why this matters] | [Decision / approval / air cover] | [Date] |

### Concerns / Risks (5 min)
| Concern | What I've Tried | What I Need From You |
|---------|----------------|---------------------|
| [Concern] | [Actions taken] | [Specific help needed] |

### Goals Check-In (3 min)
| Goal | Status | Evidence | Blocker? |
|------|--------|----------|----------|
| [Goal] | 🟢/🟡/🔴 | [What demonstrates progress] | [If any] |

### Questions I Must Get Answered
- [ ] [Decision/approval I need before next sprint]
- [ ] [Feedback on my approach to [specific situation]]
- [ ] [Clarity on [priority/direction/expectation]]
- [ ] [Support for [blocker/resource/air cover]]

*Don't leave without answers to the checked items.*

### Topics for Discussion (if time)
- [From question bank — selected based on situation]

### Notes (fill during/after meeting)
- Decisions made:
- Action items (them):
- Action items (me):
- Follow up next time:

### Unanswered Questions (carry to next 1:1)
- [ ] [Question that wasn't addressed or got deferred]
```

**After the 1:1**, produce a follow-up in the console:

```
═══════════════════════════════════════════════════
📧 1:1 FOLLOW-UP — Copy & Send (Slack DM or email)
═══════════════════════════════════════════════════

Hey [manager name],

Quick recap from our 1:1 today:

**You agreed to:**
- [Action item — with date if discussed]

**I'm going to:**
- [Action item — with date]

**Still open (need your input before [date]):**
- ❓ [Unanswered question 1]
- ❓ [Unanswered question 2]

**Next 1:1 topics to carry forward:**
- [Topic deferred from today]

Thanks!
═══════════════════════════════════════════════════
```

---

## Mode 2: Skip-Level Prep

ASK:
- When is the meeting?
- What's the relationship like? (established? new?)
- What do you want them to know about you?
- Any risks you want to flag to their level?
- Anything you need their help with that your direct manager can't provide?

### Skip-Level Strategy

| Purpose | What to Bring | What NOT to Bring |
|---------|--------------|-------------------|
| Visibility | Top 2-3 wins with org-level impact framing | Granular daily work |
| Risk escalation | Risk framed with data + proposed mitigation | Complaints about your manager |
| Career | Questions about org direction, growth paths | Promotion asks (go through manager) |
| Relationship | Genuine curiosity about their challenges | Sycophancy or politics |
| Signal | Something only you see from your vantage point | Gossip about peers |

---

## Topic Rotation (Suggested Cadence)

| Cadence | Topics | Why |
|---------|--------|-----|
| **Every week** | Blockers, decisions needed, risk flags, FYIs | Time-sensitive |
| **Every 2 weeks** | Team health, your workload, process friction | Patterns need time |
| **Monthly** | Career/goals, strategic direction, feedback request | Slower-moving |
| **Quarterly** | Performance narrative, goal reset, relationship mapping | Review-aligned |

---

## Discussion Question Bank

Pick 1-2 per 1:1 beyond operational updates.

**Get clarity on direction:**
- "What's the most important thing for my team to deliver this quarter?"
- "Are there any org priorities shifting that I should be repositioning for?"
- "If you had to cut half my team's scope, what would you keep?"
- "What does success look like for ME this quarter — in your words?"

**Surface blind spots:**
- "Is there anything I should know that I probably don't?"
- "What feedback are you hearing about me or my team from others?"
- "Am I spending my time on the right things?"
- "What would you do differently if you were in my seat?"

**Build the relationship:**
- "What's keeping YOU up at night? Anything I can take off your plate?"
- "What's the hardest part of your job right now?"
- "Who else in the org should I be building relationships with?"
- "Is there context you have about [decision/direction] that I'm missing?"

**Career progression:**
- "Where am I relative to [next level] expectations?"
- "What's the gap between where I am and where I'd need to be for [promotion/role]?"
- "What would make you confident advocating for my promotion?"
- "Who at the next level should I be observing or learning from?"

**Feedback (giving upward):**
- "Can I give you some feedback on [specific thing]?"
- "When you [did X], it made it harder for me to [Y]. Could we try [Z] instead?"
- "I want to flag that [team/org thing] is creating friction — here's what I'm seeing."

**Protect yourself (CYA):**
- "I want to confirm — the priority is [X] over [Y], correct?"
- "I flagged [risk] last week. What's your take on how we should handle it?"
- "If [thing I predicted] happens, what's the plan?"
- "I'm uncomfortable with [direction]. Can I note my concerns and then commit?"

**When things are good:**
- "The team shipped [X] this sprint — [person] especially stood out."
- "I want to highlight that [process/decision] is working really well."
- "I'm feeling good about [direction]. Here's what's giving me confidence."

---

## Topic Selection Logic

| Situation | Prioritize |
|-----------|-----------|
| Early in project | Direction, priorities, resource asks |
| Mid-sprint with blockers | Blockers, decisions, escalation help |
| Post-sprint bad metrics | Risk flags, process friction, team health |
| Post-sprint good metrics | Win sharing, career, positive feedback |
| Review cycle approaching | Goals, narrative, promotion evidence |
| Org change happening | Strategic direction, blind spots, relationship mapping |
| Overruled recently | Protect yourself, disagreement framing |
| Relationship feels distant | Relationship questions, feedback exchange |
| Burned out | Workload, boundaries, deprioritization |

---

## Guardrails

- NEVER produce 1:1 prep without a "Questions I Must Get Answered" checklist
- NEVER skip the follow-up email with unanswered questions — they carry to next meeting
- NEVER bring problems to skip-level that should go through your direct manager first
- NEVER prep without checking existing performance log for recent wins to highlight
- NEVER walk into a 1:1 without knowing what you need FROM them (not just status updates)

## References

- `skills/sdlc-performance-log.md` — Wins, goals, disagreements, review narrative (feeds into prep)
- `skills/sdlc-people-management.md` — Coaching your reports (separate workflow)
- `skills/sdlc-meeting-prep.md` — General meeting prep for non-1:1 meetings
