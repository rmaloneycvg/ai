# Release Gates

## Why This Exists

Release gates (security, accessibility, data migration, environment parity, operational readiness) are reusable quality checks applied to every production release. They live here as a single reference rather than being duplicated inline in the release planning skill.

---

## Environment Parity Gate

Verify staging mirrors production before trusting staging test results:

| Dimension | What to Check | Failure Criteria |
|-----------|---------------|-----------------|
| Data volume | Row/record counts | < 10% of prod → performance tests UNRELIABLE |
| Infrastructure specs | CPU/memory/instances | Must document ratio if scaled down |
| Network topology | Service layout | Must match production |
| Environment variables | All vars listed | No staging value pointing to prod services |
| Feature flags | Flag states | Must match or differences documented |
| Third-party integrations | Sandbox vs production accounts | Document behavioral differences |
| Database schema | Migration version | Must match after migration |
| Dependency versions | Lock file | Must be identical |

**Rules:**
- If staging data < 10% of production → run production-scale load test or accept risk in writing
- If staging infra scaled down → document ratio and which test results may not reflect prod
- If third-party sandbox behaves differently → document what's NOT being tested
- Audit environment variables for cross-pointing errors

---

## Operational Readiness Gate

| Check | Description |
|-------|-------------|
| On-call rotation assigned | Someone owns production health during release window |
| On-call briefed | 15-minute minimum briefing on new features and what could break |
| Runbooks exist | Every new service/endpoint has a "2am alert fires, what do I do?" runbook |
| Alert routing configured | Who gets paged for what |
| Escalation path documented | On-call → Tech Lead → Eng Manager |
| Dashboard access verified | On-call can see the metrics |
| Rollback tested by non-author | Proves procedure is documented, not just "in someone's head" |
| Communication channel identified | Slack channel or war room for release coordination |
| Smoke test checklist written | Post-deploy verification steps |
| Maintenance window communicated | If downtime expected |

**Rules:**
- On-call for release week MUST know what's shipping
- Rollback must be tested by someone who didn't write the deploy script
- If no on-call rotation exists → BLOCKER for release

---

## Security Review Gate

Any release containing auth changes, PII handling, external API integrations, new input surfaces, or permission changes MUST have security review.

### Triggers

| Change Type | Reviewer |
|------------|----------|
| New authentication flow | Security engineer or Tech Lead |
| PII handling changes | Security engineer |
| New external API integration | Security engineer or Tech Lead |
| New user-facing input surface | Any senior engineer |
| Permission/authorization changes | Security engineer |
| Dependency updates with security advisories | Any engineer |

### Security Review Checklist

- [ ] OWASP Top 10 reviewed for relevant categories
- [ ] No secrets in code, config, or Docker layers
- [ ] Input validation on all new endpoints (Zod/schema validated)
- [ ] SQL injection: parameterized queries only
- [ ] XSS: output encoding / CSP headers appropriate
- [ ] CSRF: token validation where applicable
- [ ] Rate limiting configured for new public endpoints
- [ ] PII fields encrypted at rest
- [ ] Audit log events emitted for security-relevant actions
- [ ] Dependency scan clean (no high/critical unresolved CVEs)

If no dedicated security engineer, Tech Lead owns this gate.

---

## Data Migration Gate

Applies when the release includes schema changes, data transforms, or backfills.

### Pre-Release Migration Checklist

- [ ] Migration tested against production-scale data volume
- [ ] Down-migration (rollback) script exists and is tested
- [ ] Migration timing estimated at production volume
- [ ] Data integrity verified (no loss, no corruption)
- [ ] Zero-downtime tested (or maintenance window communicated)
- [ ] Backup taken before migration (automated or manual with verification)
- [ ] Application works with BOTH schemas during transition (if zero-downtime)
- [ ] Monitoring in place for migration failures mid-run

### Migration Risk Levels

| Data Volume | Strategy | Risk Level |
|-------------|----------|-----------|
| < 100K rows | Run inline during deploy | Low |
| 100K–1M rows | Background job with progress tracking | Medium |
| > 1M rows | Staged migration with dual-write period | High — requires own mini release plan |

---

## Accessibility Gate

Applies to any release with user-facing UI changes. Minimum: WCAG 2.1 AA.

### Checklist

- [ ] Keyboard navigation: all interactive elements reachable and operable
- [ ] Screen reader: semantic HTML, ARIA labels, logical reading order
- [ ] Color contrast: 4.5:1 normal text, 3:1 large text
- [ ] Focus management: visible indicator, logical tab order, trapped in modals
- [ ] Form accessibility: visible labels, errors announced to screen readers
- [ ] Responsive: usable at 200% zoom, no horizontal scroll at 320px
- [ ] Motion: respects `prefers-reduced-motion`
- [ ] Touch targets: minimum 44×44px on mobile
- [ ] Images: meaningful alt text or `alt=""` for decorative
- [ ] Storybook `addon-a11y`: all stories passing

### Automated (must pass in CI)

- `axe-core` integration tests (zero critical/serious violations)
- Lighthouse accessibility score ≥ 90
- Storybook `addon-a11y` — no violations

### Manual (reviewer performs)

- Tab through all new/modified pages — can you complete the primary workflow?
- Enable VoiceOver/NVDA — does the page make sense?
- Test with 200% browser zoom — does layout break?
