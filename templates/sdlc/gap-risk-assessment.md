# Stack Gap & Risk Assessment: [Project Name]

**Date:** YYYY-MM-DD | **Author:** [Architect]
**Scope Profile Version:** [version/date]
**Preferred Stack Version:** [version/date]

---

## Assessment Matrix

| # | Component | Library / Framework / Service | Supports Scope? | GitHub Stars | Last Updated | PR Health | Native or Custom? | Code Debt Risk | Time Risk | Cost Risk | Security Risk | Knowledge Gap Risk | Dependency Risk | Regulation Risk | Overall |
|---|-----------|-------------------------------|----------------|--------------|--------------|-----------|-------------------|---------------|-----------|-----------|---------------|-------------------|-----------------|-----------------|---------|
| 1 | Frontend Framework | <!-- name --> | <!-- Full/Partial/No --> | <!-- count --> | <!-- date --> | <!-- Healthy/Concerning/Stale --> | <!-- Native/Custom --> | <!-- VH/H/N/L/VL/None --> | <!-- VH/H/N/L/VL/None --> | <!-- VH/H/N/L/VL/None --> | <!-- VH/H/N/L/VL/None --> | <!-- VH/H/N/L/VL/None --> | <!-- VH/H/N/L/VL/None --> | <!-- VH/H/N/L/VL/None --> | <!-- VH/H/N/L/VL/None --> |
| 2 | Meta-framework | <!-- name --> | | | | | | | | | | | | | |
| 3 | State Management | <!-- name --> | | | | | | | | | | | | | |
| 4 | Backend Framework | <!-- name --> | | | | | | | | | | | | | |
| 5 | Backend Language | <!-- name --> | | | | | | | | | | | | | |
| 6 | API Style | <!-- name --> | | | | | | | | | | | | | |
| 7 | Database (Primary) | <!-- name --> | | | | | | | | | | | | | |
| 8 | Database (Document) | <!-- name --> | | | | | | | | | | | | | |
| 9 | Cache | <!-- name --> | | | | | | | | | | | | | |
| 10 | Message Queue | <!-- name --> | | | | | | | | | | | | | |
| 11 | Search Engine | <!-- name --> | | | | | | | | | | | | | |
| 12 | Auth Provider | <!-- name --> | | | | | | | | | | | | | |
| 13 | Cloud Platform | <!-- name --> | | | | | | | | | | | | | |
| 14 | Container Orchestration | <!-- name --> | | | | | | | | | | | | | |
| 15 | IaC Tool | <!-- name --> | | | | | | | | | | | | | |
| 16 | CI/CD | <!-- name --> | | | | | | | | | | | | | |
| 17 | CDN | <!-- name --> | | | | | | | | | | | | | |
| 18 | API Gateway | <!-- name --> | | | | | | | | | | | | | |
| 19 | Observability (Logs) | <!-- name --> | | | | | | | | | | | | | |
| 20 | Observability (Metrics) | <!-- name --> | | | | | | | | | | | | | |
| 21 | Observability (Tracing) | <!-- name --> | | | | | | | | | | | | | |
| 22 | Error Tracking | <!-- name --> | | | | | | | | | | | | | |
| 23 | LLM Provider | <!-- name --> | | | | | | | | | | | | | |
| 24 | Vector Store | <!-- name --> | | | | | | | | | | | | | |
| 25 | Email Service | <!-- name --> | | | | | | | | | | | | | |
| 26 | Payment Gateway | <!-- name --> | | | | | | | | | | | | | |
| 27 | File Storage | <!-- name --> | | | | | | | | | | | | | |
| 28 | Feature Flags | <!-- name --> | | | | | | | | | | | | | |
| 29 | Analytics | <!-- name --> | | | | | | | | | | | | | |

---

## Risk Scale Legend

| Rating | Meaning |
|--------|---------|
| **Very High (VH)** | Likely to cause project failure or major rework. Requires immediate mitigation or alternative. |
| **High (H)** | Significant concern. Must be actively managed. Could delay timeline or increase cost substantially. |
| **Normal (N)** | Expected level of risk for this type of component. Standard mitigation sufficient. |
| **Low (L)** | Minor concern. Unlikely to impact project success. Monitor only. |
| **Very Low (VL)** | Negligible risk. Well-understood, well-supported, low probability of issues. |
| **None** | No identified risk for this dimension. |

## Column Definitions

| Column | What to Evaluate |
|--------|-----------------|
| **Supports Scope?** | Does this tool natively handle the scale, features, and constraints in our scope profile? Full = no custom work. Partial = some gaps. No = fundamental mismatch. |
| **GitHub Stars** | Community adoption signal. Not quality — but abandonment risk indicator. <1k = niche, 1k-10k = established, 10k-50k = popular, 50k+ = ubiquitous. |
| **Last Updated** | When was the last meaningful release? >6 months with open security issues = Stale. >12 months = major concern. |
| **PR Health** | Open bug count, avg time to merge, maintainer responsiveness, unresolved CVEs. Healthy = <50 open bugs, responsive maintainers. Concerning = growing backlog. Stale = abandoned. |
| **Native or Custom?** | Does the tool provide what we need out-of-box (Native), or must we build significant custom code on top (Custom)? Custom = higher code debt risk. |
| **Code Debt Risk** | Will this choice accumulate technical debt? Immature APIs with frequent breaking changes, no migration tooling, complex upgrade paths. |
| **Time Risk** | Learning curve + integration time + debugging time. Will this slow delivery beyond what timeline allows? |
| **Cost Risk** | Per-user licensing, service fees at projected scale, cost cliffs at tier boundaries, vendor lock-in premium. |
| **Security Risk** | Known CVEs (unpatched), auth model maturity, data handling practices, supply chain exposure, audit history. |
| **Knowledge Gap Risk** | Can the current team operate this in production without significant training? How hard is it to hire for? |
| **Dependency Risk** | Nested 3rd-party deps count, single-maintainer packages in tree, history of supply chain incidents, lockfile depth. |
| **Regulation Risk** | Does this choice complicate compliance? Data residency limitations, audit log gaps, encryption gaps, BAA availability. |

---

## Summary of Findings

### Components Requiring Debate (Risk ≥ High in any dimension)

| # | Component | Highest Risk Dimension | Rating | Action |
|---|-----------|----------------------|--------|--------|
| <!-- # --> | <!-- component --> | <!-- dimension --> | <!-- VH/H --> | <!-- Debate alternatives / Spike / Accept with mitigation --> |

### Components Clear to Proceed (All dimensions ≤ Normal)

| # | Component | Selection | Confidence |
|---|-----------|-----------|------------|
| <!-- # --> | <!-- component --> | <!-- tool --> | <!-- High/Medium --> |

---

## Notes

<!-- Additional context, links to spike results, vendor conversations, POC outcomes -->
