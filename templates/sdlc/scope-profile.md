# Project Scope Profile: [Project Name]

**Generated from:** Planning artifacts dated [date]
**Purpose:** Input to stack selection and architecture decisions

---

## Scale & Complexity

| Dimension | Value | Justification |
|-----------|-------|---------------|
| Users at launch | <!-- number --> | <!-- source --> |
| Users at 12 months | <!-- number --> | <!-- growth assumption --> |
| Concurrent users (peak) | <!-- number --> | <!-- % of total × peak factor --> |
| API requests/second (estimated) | <!-- number --> | <!-- users × avg requests/session --> |
| Data storage (year 1) | <!-- GB/TB --> | <!-- per-user data × users --> |
| Implementation complexity | <!-- Low / Medium / High / Very High --> | <!-- feature count, integrations, novelty --> |

## Regulatory & Compliance

| Requirement | Applies? | Impact on Stack |
|-------------|----------|-----------------|
| HIPAA | <!-- Y/N --> | <!-- encryption at rest, audit logs, BAA required --> |
| GDPR | <!-- Y/N --> | <!-- data residency, right to deletion, consent --> |
| SOC 2 | <!-- Y/N --> | <!-- access controls, audit trail, incident response --> |
| PCI DSS | <!-- Y/N --> | <!-- tokenization, network segmentation, logging --> |
| FedRAMP | <!-- Y/N --> | <!-- authorized cloud regions, specific controls --> |
| CCPA | <!-- Y/N --> | <!-- consumer data rights, opt-out mechanisms --> |
| FERPA | <!-- Y/N --> | <!-- education records, parental consent --> |
| Other | <!-- specify --> | <!-- impact --> |

## Team Capabilities

| Skill Area | Team Proficiency (1-5) | # Engineers | Years Experience | Projects Shipped |
|-----------|----------------------|-------------|-----------------|-----------------|
| <!-- Language 1 --> | <!-- 1-5 --> | <!-- count --> | <!-- years --> | <!-- count --> |
| <!-- Language 2 --> | <!-- 1-5 --> | <!-- count --> | <!-- years --> | <!-- count --> |
| <!-- Framework 1 --> | <!-- 1-5 --> | <!-- count --> | <!-- years --> | <!-- count --> |
| <!-- Cloud Platform --> | <!-- 1-5 --> | <!-- count --> | <!-- years --> | <!-- count --> |
| <!-- DevOps/IaC --> | <!-- 1-5 --> | <!-- count --> | <!-- years --> | <!-- count --> |
| <!-- Database --> | <!-- 1-5 --> | <!-- count --> | <!-- years --> | <!-- count --> |
| <!-- AI/ML --> | <!-- 1-5 --> | <!-- count --> | <!-- years --> | <!-- count --> |

## Constraints & Preferences

| Constraint Type | Details |
|----------------|---------|
| Budget ceiling (monthly infra) | <!-- $/month --> |
| Budget ceiling (licensing) | <!-- $/year --> |
| Hard deadline | <!-- date or "flexible" --> |
| Existing infrastructure | <!-- what's already running --> |
| Vendor restrictions | <!-- approved vendor list, if any --> |
| Team preference (stated) | <!-- what team wants to use --> |
| Language/framework mandate | <!-- organizational standards --> |
| Data residency requirement | <!-- regions where data must stay --> |
| Uptime SLA requirement | <!-- 99.9%, 99.99%, etc. --> |

## Integration Points

| External System | Direction | Protocol | Volume | Criticality |
|----------------|-----------|----------|--------|-------------|
| <!-- system 1 --> | <!-- inbound/outbound/bidirectional --> | <!-- REST/gRPC/webhook/file --> | <!-- requests/day --> | <!-- critical/important/nice-to-have --> |
| <!-- system 2 --> | | | | |
| <!-- system 3 --> | | | | |

## Non-Functional Requirements

| Requirement | Target | Priority |
|-------------|--------|----------|
| Response time (p95) | <!-- ms --> | <!-- must/should/could --> |
| Throughput | <!-- requests/sec --> | <!-- must/should/could --> |
| Availability | <!-- % uptime --> | <!-- must/should/could --> |
| Recovery Time Objective (RTO) | <!-- minutes/hours --> | <!-- must/should/could --> |
| Recovery Point Objective (RPO) | <!-- minutes/hours --> | <!-- must/should/could --> |
| Data retention | <!-- duration --> | <!-- must/should/could --> |
| Concurrent connections | <!-- number --> | <!-- must/should/could --> |
| Max payload size | <!-- MB --> | <!-- must/should/could --> |

---

## Summary

<!-- 2-3 sentences describing the overall complexity profile and primary constraints that will drive stack decisions -->
