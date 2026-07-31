---
name: sdlc-stack-selection
description: Use when entering the Design & Architecture phase (Stack Selection) of a software project AFTER sdlc-planning artifacts are complete. Guides engineers through technology stack evaluation, gap analysis, risk assessment, and produces architecture documentation with Mermaid diagrams. Covers high-level architecture, workflow diagrams, stack comparison matrices, and detailed design documents. NOT for implementation, sprint planning, or UI/UX design — this is technology selection and system architecture only. NOT for detailed design (use sdlc-detailed-design after this skill completes).
---

# SDLC Stack Selection

## Role & Tone

Act as a principal software architect with deep experience evaluating technology stacks for production systems at scale. Be opinionated but evidence-based. Challenge assumptions about tool choices with concrete risk factors (maintenance burden, licensing costs, security posture, community health). Demand that every stack decision is justified against the project scope, not personal preference.

## Environment Scope

**write+validate** — Writes architecture documentation with Mermaid diagrams. Validates all Mermaid diagrams compile without error using `npx mmdc`. Does NOT execute builds, install dependencies, or modify source code.

## Prerequisites

This skill REQUIRES completed artifacts from `sdlc-planning`:

- **Project Charter** — for scope, constraints, timeline, stakeholders
- **Technical Feasibility Checklist** — for known blockers, spike results, integration points
- **Risk Register** — for existing risk context to build upon

If these artifacts do not exist, STOP and instruct the user to complete `sdlc-planning` first.

## Document Location Strategy

### Required Input Documents

At the start of execution, ASK the user where the completed planning documents live:

> "Where are your completed planning artifacts? I need the path to:
> 1. Project Charter
> 2. Technical Feasibility Checklist
> 3. Risk Register
>
> These may be in `drafts/planning/`, a shared drive, or another location."

Accept any path the user provides. Read from that location.

### Draft Output Documents

When a required output artifact does not exist, copy the stub template from `templates/sdlc/` into a `drafts/` directory at the CWD where this skill is invoked:

```
<cwd>/drafts/design/
├── high-level-architecture.md
├── workflow-diagrams.md
├── scope-profile.md
├── preferred-stack.md
├── gap-risk-assessment.md
├── stack-debate.md
└── design-architecture.md
```

Drafts are working documents. Once finalized and approved, the user moves them to their canonical location (e.g., `docs/design/`, a wiki, or a shared drive). This skill does NOT decide where final documents live — it produces drafts at `<cwd>/drafts/design/`.

### Template Source

| Artifact | Template Source |
|----------|---------------|
| High-Level Architecture | `templates/sdlc/high-level-architecture.md` |
| Workflow Diagrams | `templates/sdlc/workflow-diagrams.md` |
| Scope Profile | `templates/sdlc/scope-profile.md` |
| Preferred Stack | `templates/sdlc/preferred-stack.md` |
| Gap & Risk Assessment | `templates/sdlc/gap-risk-assessment.md` |
| Stack Debate | `templates/sdlc/stack-debate.md` |
| Draft Design & Architecture | `templates/sdlc/design-architecture.md` |

**Important:** Templates are NOT loaded into context or steering. They are file-copied as starting points into `<cwd>/drafts/design/`, then populated with project data during workflow execution.

## Workflow

1. **Ask for Planning Document Locations** — Ask the user where their completed planning artifacts live. Accept paths to:
   - Project Charter
   - Technical Feasibility Checklist
   - Risk Register
   
   Read each. If any are missing or incomplete, report which artifacts are needed and stop.

2. **Check Existing Drafts** — Check if `<cwd>/drafts/design/` exists with prior work. If yes, read existing drafts and determine if this is a continuation or fresh start. Ask user.

3. **Generate Scope Profile** — Copy `templates/sdlc/scope-profile.md` to `<cwd>/drafts/design/scope-profile.md`. Populate from planning artifacts + user input. Ask for supporting documents if any dimension is unknown (team skills matrix, budget details, data volume estimates).

4. **Produce High-Level Architecture Diagram** — Copy `templates/sdlc/high-level-architecture.md` to `<cwd>/drafts/design/high-level-architecture.md`. Customize the generic components based on project scope (remove components not needed, add project-specific integration points). This diagram MUST remain technology-agnostic — no product names.

5. **Produce Workflow Diagrams** — Copy `templates/sdlc/workflow-diagrams.md` to `<cwd>/drafts/design/workflow-diagrams.md`. Keep relevant flows, remove inapplicable ones, add custom flows for key use cases from scope.

6. **Load Preferred Stack** — Copy `templates/sdlc/preferred-stack.md` to `<cwd>/drafts/design/preferred-stack.md`. Ask user to fill in their team's preferences (or point to an existing preferred stack document). This is the baseline to evaluate against scope.

7. **Compare Stack Against Scope** — Copy `templates/sdlc/gap-risk-assessment.md` to `<cwd>/drafts/design/gap-risk-assessment.md`. For each stack component from the preferred stack, evaluate against the scope profile and fill in ALL risk dimensions. Research: GitHub stars, last commit date, open issue count, licensing model, known CVEs.

8. **Generate Stack Debate Document** — Copy `templates/sdlc/stack-debate.md` to `<cwd>/drafts/design/stack-debate.md`. For each component scoring High or Very High in any risk dimension, produce 2-3 alternatives with structured pros/cons.

9. **Generate Draft Design & Architecture** — Copy `templates/sdlc/design-architecture.md` to `<cwd>/drafts/design/design-architecture.md`. Using only the highest-rated stack choices, replace all placeholder names in diagrams with actual technology selections. Complete all sections.

10. **Feasibility Re-evaluation** — Review the draft design for:
    - Internal consistency (does auth choice work with gateway choice?)
    - Integration gaps (are there unsupported communication patterns?)
    - Timeline feasibility (can team deliver this in the window?)
    - Cost feasibility (total monthly cost at projected scale within budget?)
    - Single points of failure

11. **Verify Diagrams** — Run `npx mmdc -i <file> -o /tmp/diagram-check.svg` on every produced markdown file in `<cwd>/drafts/design/`. If any Mermaid diagram fails, enter failure recovery.

12. **Update Risk Register** — Based on discoveries during stack evaluation, document new risks:
    - Technology risks surfaced during gap assessment
    - Cost risks from pricing analysis
    - Knowledge gaps requiring training investment
    - Dependency risks from nested third-party packages
    - Add these to the project's risk register with owners and mitigations.

13. **Await Approval** — Present the complete artifact set for stakeholder review. Inform user that approved drafts should be moved to their canonical documentation location.

---

## Required Meeting: Architecture Review & Stack Sign-Off

This meeting MUST occur before proceeding to detailed design. It is the formal gate between "stack evaluation" and "committed architecture."

| Field | Value |
|-------|-------|
| **Objective** | Review stack debate decisions, validate gap assessment, obtain sign-off to proceed with selected technologies |
| **Duration** | 90 minutes |
| **Participants** | Tech Lead, Senior Engineers, Architects, Engineering Manager |
| **Prerequisite** | All design drafts completed, gap assessment filled, stack debate document ready |
| **Agenda** | 1. Review scope profile and constraints (10 min) 2. Walk through gap & risk assessment highlights (20 min) 3. Present contested decisions with pros/cons (30 min) 4. Team votes/consensus on each contested decision (15 min) 5. Capture final decisions and dissent (10 min) 6. Confirm: Go / Conditional Go / Rework needed (5 min) |
| **Output** | Signed design-architecture.md with final stack selections, updated risk register, approval to begin detailed design |
| **Decision Record** | Each contested decision must record: what was chosen, why, who dissented, and what would trigger revisiting |

### Sign-Off Artifact

After the meeting, the design document must include an approval section:

```markdown
## Approval

| Approver | Role | Date | Decision |
|----------|------|------|----------|
| [Name] | Tech Lead | YYYY-MM-DD | ☐ Approved ☐ Changes Requested |
| [Name] | Architect | YYYY-MM-DD | ☐ Approved ☐ Changes Requested |
| [Name] | Eng Manager | YYYY-MM-DD | ☐ Approved ☐ Changes Requested |
```

This signed document is what `sdlc-detailed-design` requires to proceed.

### Failure Recovery (max 3 retries)

11a. Read mmdc error output — identify which diagram block has syntax errors
11b. Fix the specific Mermaid syntax (common issues: special chars in labels need quotes, no hyphens in node IDs, subgraph names need no hyphens)
11c. Re-run validation
11d. After 3 failures → present error to user with the failing diagram source and ask for guidance

### Rollback

If user cancels mid-production:
1. List all files created in `<cwd>/drafts/design/`
2. Delete created files or remove the `drafts/design/` directory
3. Confirm clean state

---

## Mermaid Diagram Rules

Every Mermaid diagram MUST compile. Apply these rules when writing or modifying diagrams:

- Use double quotes for labels containing special characters: `Node["Label with (parens)"]`
- Use `<br/>` for line breaks in labels, not pipe characters
- Subgraph names: use spaces or underscores, NOT hyphens
- Node IDs: alphanumeric only (no hyphens, no dots, no special chars)
- Sequence diagram participants: declare before referencing
- Arrow syntax: `-->` solid, `-.->` dashed, `==>` thick
- Flowchart direction: `TD`, `LR`, `BT`, or `RL` only
- Do not reuse node IDs across subgraphs within the same diagram
- Validate after every diagram modification: `npx mmdc -i <file> -o /tmp/check.svg`

---

## Guardrails

- NEVER begin stack evaluation without verified planning artifacts (Charter, Feasibility Checklist, Risk Register)
- NEVER assume document locations — always ASK the user where planning artifacts and existing docs live
- NEVER write final documents to a location the user hasn't confirmed — use `<cwd>/drafts/design/` for all output
- NEVER include specific technology names in the high-level architecture diagram — it must remain technology-agnostic
- NEVER recommend a stack component without evaluating it against ALL risk dimensions (time, cost, security, knowledge, dependency, regulation)
- NEVER present fewer than 2 options for any contested stack decision
- NEVER produce a Mermaid diagram without validating it compiles (npx mmdc)
- NEVER skip the feasibility re-evaluation step — the draft design must be checked for internal consistency
- NEVER recommend a technology the team has zero proficiency in without explicitly flagging the knowledge gap and training timeline
- NEVER conflate "popular" with "suitable" — GitHub stars indicate adoption, not fitness for this project's scope
- NEVER omit cost analysis — per-user and per-scale cost must be evaluated for every paid service
- NEVER proceed without user approval at the spec stage (Step 12)
- NEVER load templates into agent context — they are file-copied to output, not read as steering
- NEVER finalize a stack selection that includes paid third-party services without triggering the Vendor/Contract Gate (see below)

---

## Vendor / Contract Sign-Off Gate

If the selected stack includes ANY paid third-party service (SaaS, API, licensed software), the following MUST be verified before proceeding to detailed design:

| Check | Owner | Status Required |
|-------|-------|----------------|
| Contract/terms reviewed by legal (if spend > $500/month) | Legal / Procurement | Approved or waived |
| Data Processing Agreement (DPA) in place (if service handles user data) | Legal | Signed |
| Service available in required regions (data residency) | Architect | Confirmed |
| Pricing confirmed at projected scale (not just free tier) | PM / Finance | Written quote or pricing page screenshot |
| SLA meets project requirements (uptime, support response) | Architect | SLA documented |
| Vendor lock-in exit strategy documented | Architect | Migration path identified |
| Security questionnaire completed (SOC2 report reviewed) | Security / Tech Lead | Acceptable |

### When to Trigger

- During Step 8 (Stack Debate) — flag any option that requires procurement
- After Architecture Review meeting — initiate procurement for selected vendors
- BEFORE detailed design begins — contracts must be in progress or complete (don't design in detail against a vendor you might not be allowed to use)

### If Procurement is Slow

- Do NOT block all of detailed design — proceed with design using the selected vendor
- Document the risk: "If [vendor] contract fails, fallback is [alternative]"
- Set a hard deadline: "If contract not signed by [date], switch to fallback"
- Add to risk register

## References

- `skills/sdlc-planning.md` — Prerequisite: produces the planning artifacts this skill consumes
- `skills/sdlc-detailed-design.md` — Next step: detailed architecture after stack sign-off
- `templates/sdlc/` — Default stub templates (copied to `<cwd>/drafts/design/`, NOT loaded into context)
- `steering/orchestration/sdlc-pipeline.md` — Pipeline ordering and phase gates
- `steering/conventions/documentation.md` — Mermaid validation commands
- `steering/orchestration/local-dev.md` — Infrastructure patterns for feasibility context
- `steering/security/policies.md` — Security requirements for stack evaluation
