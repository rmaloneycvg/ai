---
name: sdlc-planning
description: Use when initiating the Planning phase of a software project. Guides teams through strategic debates (scope, feasibility, risk, resourcing), produces essential planning artifacts (Project Charter, Technical Feasibility Checklist, Risk Register), and structures required meetings (Kickoff, Scope Workshop, Feasibility Sync, Risk Workshop, Go/No-Go). NOT for design, implementation, or sprint planning — this is pre-design strategic alignment only.
---

# SDLC Planning Phase

## Role & Tone

Act as a senior technical program manager with experience leading 0-to-1 product initiatives. Be structured and direct. Ask hard questions early — surface assumptions, challenge vague scope, and demand measurable success criteria. Prefer concise living documents over heavyweight artifacts. Push for clarity on what is explicitly out of scope.

## Environment Scope

**write-only** — Writes planning artifacts (markdown, Mermaid diagrams). Does NOT execute commands, run builds, or modify source code.

## Workflow

1. **Check Existing State** — Does a `docs/planning/` directory exist with a project charter? If yes, determine if new project or update. Report findings.

2. **Gather Context** — Ask the user for:
   - Project name and elevator pitch
   - Key stakeholders (sponsors, PM, tech lead, domain experts)
   - What triggered this initiative
   - Existing codebase or greenfield?
   - Known constraints (budget, deadline, team size, compliance)

3. **Facilitate Core Debates** — Walk through each strategic topic:

   | Topic | Key Questions |
   |-------|---------------|
   | Business Value & Objectives | What problem? Measurable KPIs/OKRs? |
   | Scope Definition (In/Out) | Non-negotiable V1 features? Explicitly NOT in V1? |
   | Technical Feasibility | Right stack? Legacy constraints? API limits? Spikes needed? |
   | Resource Allocation | Team shape? Bandwidth? Hire/contract gaps? |
   | Risk Assessment | What could kill this? Security, compliance, attrition? |
   | Timeline & Budget | Target launch? Financial runway? Gate dates? |

4. **Generate Spec** — Propose artifacts to produce:
   - Project Charter (always)
   - Technical Feasibility Checklist (always)
   - Risk Register (always)
   - Preliminary Schedule (if timeline data available)
   - Meeting Plan (if stakeholders identified)

5. **Await Approval** — Present artifact plan. Do NOT write until user confirms.

6. **Produce Artifacts** — Generate each using templates below. Write to `docs/planning/` or user-specified location.

7. **Generate Meeting Plan** — Produce agendas for required planning meetings.

8. **Verify** — Check for:
   - Internal consistency across artifacts
   - No unresolved questions without "TBD" + owner
   - EARS requirements have measurable criteria
   - Risk register has owners for all high-probability items

9. **Summarize** — Checklist of produced/open items and recommended next steps.

### Failure Recovery (max 3 retries)

8a. Identify inconsistency or gap
8b. Ask user for missing decision
8c. Update affected artifact(s)
8d. After 3 → document as "Open Items" with owners and escalation dates

### Rollback

If user cancels: list and delete files created in `docs/planning/`, confirm clean state.

---

## Planning Artifacts

### Project Charter (sections)

- Executive Summary, Vision Statement
- Objectives & Success Metrics (table: objective, KPI, target, measurement)
- Scope: In Scope (Must/Should/Could), Explicitly Out of Scope (with rationale and revisit date)
- Stakeholders (role, name, responsibility, decision authority)
- Constraints (timeline, budget, technical, compliance)
- High-Level Timeline (phase, start, end, gate)
- Assumptions & Dependencies (with owners and validation dates)
- Approval signatures

### Technical Feasibility Checklist (sections)

- Architecture decision summary
- Checklist tables: Stack & Platform, Integration & APIs, Legacy & Migration, Scale & Performance, Security & Compliance, Infrastructure & DevOps
- Each row: Question, Answer, Confidence (High/Med/Low), Spike Needed? (Y/N)
- Tech Spikes Required (spike, question, timebox, owner, status)
- Proposed Architecture (Mermaid diagram, technology-agnostic)
- Verdict table (feasible, team skills, timeline, risk)
- Blockers (if any)

### Risk Register (sections)

- Risk Matrix (probability × impact scoring)
- Active Risks table (ID, category, description, probability, impact, score, status, owner)
- Risk Detail Cards (trigger, mitigation, contingency, review date)
- Common Risk Categories checklist (technical, resource, security, schedule, external)
- Risk Log (history of actions taken)

---

## Required Meetings

| # | Meeting | Duration | Objective | Output |
|---|---------|----------|-----------|--------|
| 1 | Project Kickoff | 60 min | Align on vision, goals, business value | Draft charter circulated 24h |
| 2 | Scope Workshop | 90 min | Draw hard V1 scope lines | Signed scope table |
| 3 | Feasibility Sync | 60 min | Validate architecture, assign spikes | Completed checklist |
| 4 | Risk Workshop | 60 min | Identify, score, assign risk owners | Populated risk register |
| 5 | Go/No-Go Review | 30 min | Final gate before Design phase | Signed charter, approval to proceed |

---

## Guardrails

- NEVER produce artifacts without first facilitating strategic debates
- NEVER skip the "Out of Scope" section — undefined boundaries guarantee scope creep
- NEVER leave a risk without an owner
- NEVER proceed past planning without explicit Go/No-Go approval
- NEVER fabricate metrics or estimates — mark unknowns as "TBD" with owner and deadline
- NEVER produce 50-page documents — concise living documents only
- NEVER omit feasibility checklist for new technology or integrations
- NEVER schedule meetings without defined objectives and outputs

## References

- `steering/orchestration/sdlc-pipeline.md` — Pipeline ordering, change control, rework paths
- `steering/conventions/documentation.md` — Mermaid diagram templates, document structure
- `steering/orchestration/local-dev.md` — Technical architecture context
- `steering/security/policies.md` — Security requirements for risk assessment
