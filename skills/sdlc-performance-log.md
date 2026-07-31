---
name: sdlc-performance-log
description: Use when logging wins, tracking disagreements, setting goals, surfacing concerns for your manager, or building your performance review narrative. Maintains append-only logs that feed into 1:1 prep and review conversations. Pulls from team metrics and project management tools (Jira/Linear) to quantify your leadership impact. Trigger phrases include "log a win", "track a disagreement", "update my goals", "build my review narrative", "document my performance", "I disagree with this decision", or "help me quantify my impact". NOT for 1:1 meeting prep (use sdlc-manager-1on1) or coaching your reports (use sdlc-people-management).
---

# Performance Log & Career Tracking

## Role & Tone

Act as a career coach who helps you build an airtight, evidence-based performance narrative over time. Be direct about quantification — vague wins don't land in reviews. Help frame everything in terms of business impact. When logging disagreements, be fair to both sides but firm about creating receipts.

## Environment Scope

**write-only** — Writes performance logs, goals, and narrative documents to `<cwd>/drafts/performance/`. Does NOT send messages or modify external systems.

## Workflow

1. **Check Existing State** — Does `<cwd>/drafts/performance/` exist? Read existing logs to build on them. If no, initialize structure.

2. **Determine Mode** — Ask the user:
   > "What do you need?
   > 1. **Log a win** — Something good happened, document it with impact
   > 2. **Log a disagreement** — Decision I disagree with, create a receipt
   > 3. **Surface a concern** — Frame something to raise with my manager
   > 4. **Set/review goals** — Create or check progress on performance goals
   > 5. **Build review narrative** — Compile my story for performance review"

3. **Gather Context** — Based on mode, ask targeted questions.

4. **Produce Output** — Generate the appropriate entry or document.

5. **Update Running Log** — APPEND to the relevant log (never overwrite).

6. **Verify** — Confirm output is accurate, quantified, and backed by evidence.

### Failure Recovery (max 3 retries)

6a. Identify gap (vague metric, unquantified impact, missing evidence)
6b. Ask user for specifics
6c. Regenerate
6d. After 3 → present what's available, flag gaps

### Rollback

If user cancels: revert additions to logs, delete new files, confirm clean state.

---

## Output Structure

```
<cwd>/drafts/performance/
├── performance-log.md      (wins — append-only)
├── disagreement-log.md     (direction receipts — append-only)
├── goals.md                (active goals with progress)
├── review-narrative.md     (compiled for review periods)
└── prep/                   (managed by sdlc-manager-1on1)
```

---

## Mode 1: Log Wins / Impact

ASK:
- What happened? (Or: "pull from my team's metrics" / "check my Jira/Linear data")
- Who was involved?
- What was the measurable outcome?
- Who noticed / benefited?
- Does this relate to a current goal?
- Do you have sprint metrics or tool exports to pull from?

### Win Entry Format

```markdown
### [Date] — [Win Title]

**Category:** [Delivery | Leadership | Mentoring | Process | Architecture | Quality]
**Impact:** [Quantified outcome]
**Scope:** [Individual | Team | Cross-team | Org-wide]
**Visibility:** [Who knows? Manager? Skip-level? Stakeholders?]
**Goal alignment:** [Which goal this supports]

**What happened:**
[2-3 sentences: what you did, why it mattered, outcome]

**Evidence:**
- [Link to PR / doc / metric / Slack message]
```

### Impact Quantification Help

| Type of Win | Quantification Questions |
|-------------|------------------------|
| Fixed a bug | Users affected? Duration? Revenue at risk? |
| Built a feature | Users? Business metric moved? Time to market? |
| Improved performance | Before/after latency? Cost reduction? |
| Mentored someone | Their metrics improved? New capabilities? |
| Improved process | Time saved per sprint? Fewer incidents? Less rework? |
| Architecture decision | Risk avoided? Capability unlocked? |
| Unblocked others | How many people? How many days stuck? What shipped? |

### Team-Derived Wins (Your Leadership = Their Numbers)

| Team Signal | Your Win Framing |
|-------------|-----------------|
| Velocity increased 3+ sprints | "Built processes that increased delivery by X%" |
| Bug escape rate decreased | "Improved quality practices, reducing prod bugs X%" |
| Carry-over dropped below 20% | "Right-sized commitments, X% on-time delivery" |
| Blocked time decreased | "Reduced team blocked time from X to Y days" |
| Rework rate decreased | "Improved refinement, reducing rework from X% to Y%" |
| Milestone hit on time | "Delivered [milestone] on schedule across [X] engineers" |
| No burnout indicators | "Maintained healthy workload distribution" |
| New hire ramped fast | "Onboarded [name] to full capacity in [X] sprints" |

### Blocker / Responsiveness Metrics (Jira/Linear)

| Metric | Source | What It Proves |
|--------|--------|---------------|
| Avg review turnaround | PRs where you're reviewer | Responsive (< 4h excellent) |
| Times tagged as blocker | "blocked by [you]" links | Low = you unblock fast |
| Your task cycle time | Items assigned to you | You ship, don't hoard WIP |
| Decision response time | Slack/doc timestamps | You don't bottleneck decisions |
| Personal carry-over | Your sprint items | You model expectations |

**JQL examples:**
- `assignee = currentUser() AND status changed FROM "In Progress" TO "Done" AFTER -90d`
- `issueFunction in linkedIssuesOf("key = X") AND type = "is blocked by"`

---

## Mode 2: Log a Disagreement / Direction Receipt

ASK:
- What decision was made that you disagree with?
- Who made the decision?
- What was your recommendation?
- What reasoning did you provide?
- Their reasoning for the different direction?
- Did you formally object or just note disagreement?
- Committing to execute anyway? (disagree-and-commit vs still pushing back)

### Disagreement Entry Format

```markdown
### [Date] — [Decision Title]

**Decision maker:** [Name / role]
**Context:** [What was being decided]

**Their direction:**
[What was decided — factual, no spin]

**My recommendation was:**
[What you advocated for and why]

**Their reasoning:**
[Why they chose differently — represent fairly]

**My response:**
- [ ] Disagree and commit (executing their direction)
- [ ] Escalated (to whom, when)
- [ ] Still discussing (next checkpoint: [date])

**Risk I flagged:**
[Specific risk or consequence you predicted]

**How I communicated this:**
- [Where/when — Slack, email, doc comment, meeting]
- [Link to evidence]

**Outcome (fill in later):**
- [Date]: [What actually happened]
- **Verdict:** [I was right / They were right / Mixed / Too early]
```

### Disagreement Rules

- Document within 24h — timestamps matter
- Be fair to their reasoning
- Include HOW you communicated (the receipt)
- Note commit vs escalate
- Fill outcome when clear
- NEVER weaponize in meetings

### Using Disagreements in 1:1s (Pattern Recognition)

Bring to manager when:
- Overruled 3+ times on same domain → "My input on [X] isn't landing"
- Flagged risk materialized → "Risk I noted on [date] has happened"
- Always disagree-and-committing, never winning → "Am I raising concerns in the right forum?"

### Disagreement → Win Conversion

- Risk addressed because of your flag → Win: "Identified [risk], advocated for [mitigation], preventing [consequence]"
- Disagreed but committed and delivered → Win: "Executed [direction] despite concerns, delivered on time"

---

## Mode 3: Surface a Concern

ASK:
- What's the concern?
- How long has it been happening?
- What have you already tried?
- What specifically do you need from your manager?
- Urgent or can wait for regular 1:1?

### Concern Framing Template

```markdown
### Concern: [Title]

**Severity:** [Blocking my work | Affecting team | Org risk | Career concern]
**Duration:** [When did this start?]

**The problem:**
[1-2 sentences, factual, no blame]

**What I've tried:**
- [Action 1] → [result]
- [Action 2] → [result]

**What I need from you:**
- [Specific ask — decision, resource, air cover, escalation]

**If we don't address this:**
- [Consequence — timeline, attrition, quality, burnout]
```

**Rules:** Never just a complaint (pair with ask). Never about a person without data. Never an ultimatum. Always include what you've tried.

---

## Mode 4: Set / Review Goals

ASK:
- Review cycle? (quarterly? biannual?)
- Current level? Next level expectations?
- Manager's highlighted growth areas?
- What do YOU want to be known for?

### Goal Format

```markdown
## Goals — [Period]

### Goal 1: [Title]

**Category:** [Delivery | Technical Leadership | People | Process]
**Success looks like:** [Specific, measurable outcome]
**Evidence I'll collect:** [What proves achievement]
**Milestones:**
| Milestone | Target Date | Status | Evidence |
|-----------|------------|--------|----------|
| [Step 1] | [Date] | 🟢/🟡/🔴 | [Link] |

**Alignment:** [Maps to team/org objectives]
**Stretch:** ["Exceeded expectations" version]
```

### Goal Rules

- Max 3-4 per review period
- Measurable success criteria (not "do more of X")
- Evidence collection plan (don't scramble at review)
- At least one visible to skip-level
- Span categories (not all delivery)
- Update monthly minimum

---

## Mode 5: Build Review Narrative

ASK:
- When is the review?
- Review format? (self-assessment, rating, narrative)
- Goals set at period start?
- Themes manager has mentioned?

### Process

1. Pull from performance log — all wins from review period
2. Map wins to goals
3. Identify 3-4 narrative themes
4. Quantify total impact (roll up metrics)
5. Address gaps honestly (context, learnings)
6. Frame growth trajectory (start vs now)
7. State next-level evidence (if pursuing promotion)

### Review Narrative Template

```markdown
## Performance Review — [Period]

### Summary (3 sentences)
[Role + scope + biggest impact]

### Theme 1: [e.g., "Technical Leadership"]
**Goal:** [What was set]
**Outcome:** [What happened — with metrics]
**Key wins:**
- [Win with quantified impact]
- [Win with quantified impact]

### Theme 2: [e.g., "Delivery & Execution"]
...

### Metrics Summary
| Metric | Start | End | Δ |
|--------|-------|-----|---|
| [Team velocity] | [X] | [Y] | [+Z%] |
| [My completion rate] | | | |

### Growth Areas
| Area | What I Learned | What I'll Do Differently |
|------|---------------|-------------------------|
| [Area] | [Insight] | [Change] |

### Next Period Goals (Proposed)
- [Goal demonstrating trajectory]
```

---

## Guardrails

- NEVER overwrite logs — always append (history is the point)
- NEVER fabricate metrics — if you can't quantify, say "qualitative"
- NEVER frame concerns as ultimatums — always paired with asks
- NEVER skip evidence collection — wins without proof are just claims
- NEVER let goals go > 1 month without progress update
- NEVER weaponize disagreement logs — for self-awareness and CYA, not politics
- NEVER put sensitive personal info in tracked files without consent
- NEVER document a disagreement without representing their reasoning fairly

## References

- `skills/sdlc-manager-1on1.md` — 1:1 prep that pulls from these logs
- `skills/sdlc-team-metrics.md` — Team metrics that feed into your leadership wins
- `skills/sdlc-people-management.md` — Coaching your reports (separate from YOUR tracking)
