---
name: sdlc-detailed-design
description: Use when the stack selection is finalized and signed off (sdlc-stack-selection complete) and you need to produce detailed architecture documentation. Generates finalized stack manifest, detailed workflow/use-case diagrams, ERDs, data flow diagrams, network topology, and cloud architecture. NOT for stack selection (use sdlc-stack-selection) or implementation planning (use sdlc-epic-planning).
---

# SDLC Detailed Design

## Role & Tone

Act as a principal software architect producing production-ready architecture documentation. Be precise and exhaustive in diagram detail. Every workflow must trace from user action to data persistence and back. Every entity must have defined relationships. Every network hop must be documented. This is the blueprint engineers build from.

## Environment Scope

**write+validate** — Writes detailed architecture documentation with Mermaid diagrams to `<cwd>/drafts/design/detailed/`. Validates all Mermaid diagrams compile without error using `npx mmdc`. Does NOT execute builds, install dependencies, or modify source code.

## Prerequisites

This skill REQUIRES:

- **Finalized Design & Architecture Document** (from `sdlc-stack-selection`) — signed off with selected stack
- **Scope Profile** — for use case identification
- **Gap & Risk Assessment** — for known limitations to design around

ASK the user for the location of these documents before proceeding.

## Workflow

1. **Ask for Document Locations** — Ask the user:
   > "Where are your finalized architecture documents from stack selection? I need:
   > 1. Finalized Design & Architecture doc (with signed-off stack)
   > 2. Scope Profile
   > 3. Gap & Risk Assessment
   > 4. Any wireframes, mockups, or UI specs (Figma links, etc.)
   >
   > Also: has the stakeholder sign-off been obtained? (I will not proceed without it.)"

2. **Verify Sign-Off** — Confirm the design document has approval signatures or explicit user confirmation that sign-off occurred. If not signed off, STOP.

3. **Extract Finalized Stack** — Read the approved design document. Produce a clean **Finalized Stack Manifest** listing every technology with exact versions, licensing, and operational notes.

4. **Identify Use Cases** — From the scope profile and charter, enumerate ALL use cases that require detailed workflow documentation. Categorize by:
   - User-facing flows (CRUD, search, auth, file management)
   - Background processes (scheduled jobs, event processing)
   - Integration flows (webhooks, sync, third-party API calls)
   - Admin flows (user management, configuration, reporting)

5. **Produce Detailed Workflow Diagrams** — For EACH use case, produce a sequence diagram showing every service, database call, cache interaction, queue publish/subscribe, and external API call with the actual technology names from the finalized stack.

6. **Produce Entity Relationship Diagrams** — Design the data model. Produce ERDs covering:
   - Core domain entities (users, resources, relationships)
   - Supporting entities (audit logs, notifications, sessions)
   - Junction/pivot tables for many-to-many relationships
   - Include data types, constraints, indexes, and foreign keys

7. **Produce Data Flow Diagrams** — For each workflow from Step 5, produce a corresponding data flow diagram showing:
   - What data enters the system (inputs, shape, validation)
   - How data transforms through each layer
   - Where data is persisted, cached, or queued
   - What data exits the system (responses, events, side effects)
   - Link each data flow to its parent workflow diagram

8. **Produce Network Topology** — Document the network architecture:
   - VPC/network boundaries
   - Subnet layout (public, private, isolated)
   - Load balancer placement
   - Service mesh / service discovery
   - Ingress/egress rules
   - DNS resolution path
   - TLS termination points

9. **Produce Cloud Architecture Diagram** — Map the logical architecture to the specific cloud provider's services:
   - Compute (containers, serverless, VMs)
   - Storage (object, block, file)
   - Database (managed services, configuration)
   - Networking (VPC, subnets, security groups, CDN)
   - Observability (cloud-native monitoring, logging)
   - Security (IAM, secrets, encryption, WAF)
   - Cost annotations per service (estimated monthly)

10. **Cross-Reference All Diagrams** — Add navigation links between related documents:
    - Each workflow links to its data flow
    - Each data flow links to relevant ERD entities
    - Network diagram references security policies
    - Cloud architecture links to infrastructure cost estimates

11. **Verify Diagrams** — Run `npx mmdc -i <file> -o /tmp/check.svg` on every produced file. Enter failure recovery if any fail.

12. **Update Risk Register** — Document new risks discovered during detailed design:
    - Integration complexity risks (unexpected protocol mismatches)
    - Data model risks (normalization trade-offs, migration concerns)
    - Network/latency risks (cross-region calls, chatty services)
    - Cost risks (updated estimates from cloud architecture)
    - Add to project risk register with owners and mitigations.

13. **Await Approval** — Present complete documentation set for architecture review via the **Detailed Design Walkthrough** meeting.

---

## Required Meeting: Detailed Design Walkthrough

This meeting ensures the full engineering team understands and validates the detailed architecture before epic planning begins.

| Field | Value |
|-------|-------|
| **Objective** | Walk entire team through detailed architecture; validate ERDs, data flows, and cloud architecture; confirm engineers can build from these docs |
| **Duration** | 120 minutes (split into 2×60 if needed) |
| **Participants** | All engineers who will implement, Tech Lead, Architect, QA Lead |
| **Prerequisite** | All detailed design docs complete and diagram-validated |
| **Agenda** | 1. Finalized stack manifest review (10 min) 2. Use case walkthrough — each workflow diagram (30 min) 3. ERD review — entities, relationships, data types (20 min) 4. Data flow review — linked to workflows (20 min) 5. Network topology and security boundaries (15 min) 6. Cloud architecture and cost (15 min) 7. Questions, gaps, and concerns (10 min) |
| **Output** | Team understanding confirmed, gap list (if any), approval to proceed to epic planning |

### Design-Complete Gate

Before proceeding to `sdlc-epic-planning`, the following must be true:

- [ ] All use cases from scope have workflow diagrams
- [ ] ERDs cover all entities referenced in workflows
- [ ] Every data flow links to its parent workflow
- [ ] Network topology documents all service-to-service paths
- [ ] Cloud architecture has cost estimates
- [ ] Engineering team has reviewed and has no blocking questions
- [ ] Wireframes/mockups are available for all user-facing use cases (or explicitly marked as "in progress" with completion date)
- [ ] Risk register updated with design-phase discoveries
- [ ] Sign-off obtained (verbal or document signatures)

If wireframes are not complete, epic planning MAY begin for backend/infrastructure work only. UI stories MUST wait for wireframes.

### Failure Recovery (max 3 retries)

11a. Read mmdc error output — identify failing diagram
11b. Fix Mermaid syntax
11c. Re-validate
11d. After 3 failures → present error to user

### Rollback

If user cancels: delete all files created in `<cwd>/drafts/design/detailed/`, confirm clean state.

---

## Output Structure

```
<cwd>/drafts/design/detailed/
├── finalized-stack-manifest.md
├── use-cases/
│   ├── index.md                    (use case registry with links)
│   ├── uc-001-user-registration.md
│   ├── uc-002-authentication.md
│   ├── uc-003-[use-case].md
│   └── ...
├── erd/
│   ├── core-domain.md
│   ├── supporting-entities.md
│   └── full-schema.md
├── data-flows/
│   ├── df-001-user-registration.md (links to uc-001)
│   ├── df-002-authentication.md    (links to uc-002)
│   └── ...
├── network/
│   ├── topology.md
│   └── security-groups.md
└── cloud/
    ├── architecture.md
    └── cost-estimate.md
```

---

## Mermaid Diagram Rules

- Use double quotes for labels with special characters
- Use `<br/>` for line breaks in labels
- Subgraph names: spaces or underscores, no hyphens
- Node IDs: alphanumeric only
- Sequence diagram participants: declare before use
- ERDs: use `erDiagram` keyword, `||--o{` for relationships
- Do not reuse node IDs across subgraphs
- Validate every diagram before presenting

---

## Guardrails

- NEVER proceed without confirmed sign-off on stack selection
- NEVER produce workflow diagrams using generic names — detailed design uses ACTUAL technology names from finalized stack
- NEVER produce an ERD without data types and relationship cardinality
- NEVER produce a data flow without linking it to its parent workflow diagram
- NEVER omit cost annotations from cloud architecture
- NEVER produce a network diagram without security boundaries and trust zones
- NEVER skip use case enumeration — every scope item must have a workflow
- NEVER produce diagrams without validating they compile
- NEVER assume document locations — ASK the user
- NEVER exceed the charter's budget ceiling without triggering the Budget Escalation Gate (see below)
- NEVER make a major technical decision mid-design without documenting it as an ADR (see below)

---

## Budget Escalation Gate

If the detailed cloud architecture cost estimate exceeds the charter's budget constraint:

| Variance | Action |
|----------|--------|
| ≤ 10% over | Note in cost estimate, flag as risk, proceed |
| 11-25% over | STOP — present cost breakdown to PM and Engineering Manager. Options: reduce scope, optimize architecture, or request budget increase |
| > 25% over | STOP — escalate to Executive Sponsor. This requires a formal budget change request via Change Control Process |

Cost comparison must include:
- Monthly run cost at launch scale
- Monthly run cost at 12-month projected scale
- One-time setup/migration costs
- Licensing costs (annual)
- Total Cost of Ownership vs charter budget

---

## Architecture Decision Records (ADRs)

When the team makes a significant technical decision during detailed design that wasn't covered in the stack selection debate, it MUST be documented as an ADR.

### When to Write an ADR

- Choosing between two valid approaches for a component (e.g., sync vs async for a specific flow)
- Deviating from the selected stack for a specific use case
- Accepting a known trade-off (e.g., eventual consistency instead of strong consistency)
- Deciding on a data model approach that has alternatives (e.g., normalized vs denormalized)
- Any decision a new team member would ask "why did we do it this way?"

### ADR Template

```markdown
# ADR-[NNN]: [Decision Title]

**Date:** YYYY-MM-DD | **Status:** Proposed | Accepted | Deprecated | Superseded
**Deciders:** [Names]

## Context

<!-- What is the problem or question that requires a decision? -->

## Options Considered

### Option A: [Name]
- Pro: 
- Con: 

### Option B: [Name]
- Pro: 
- Con: 

## Decision

<!-- Which option was chosen and WHY -->

## Consequences

<!-- What are the implications of this decision? What becomes easier? What becomes harder? -->

## Revisit Trigger

<!-- Under what conditions should this decision be re-evaluated? -->
```

### ADR Storage

ADRs are stored in `<cwd>/drafts/design/detailed/adrs/` (or project-specific location). They are numbered sequentially and never deleted — only superseded.

## References

- `skills/sdlc-stack-selection.md` — Prerequisite: produces the finalized stack
- `skills/sdlc-planning.md` — Planning artifacts (scope, charter, risk register)
- `skills/sdlc-epic-planning.md` — Next step: work decomposition
- `templates/sdlc/` — Template stubs if needed
- `steering/orchestration/sdlc-pipeline.md` — Pipeline ordering and phase gates
- `steering/conventions/documentation.md` — Mermaid validation
- `steering/security/policies.md` — Security architecture patterns
- `steering/orchestration/local-dev.md` — Infrastructure topology reference
