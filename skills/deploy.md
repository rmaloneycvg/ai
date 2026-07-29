---
name: deploy
description: Deploy infrastructure or services — terraform plan/apply workflows, environment promotion, database migrations, rollbacks, and health checks. NOT for local development setup (use steering/orchestration/local.md) or adding new services (use backend-rest-api-feature or backend-cron-feature).
---

# Deploy

## Environment Scope

**write+execute** — Writes terraform configs and migration files. Executes `terraform plan` (read-only preview). Does NOT execute `terraform apply` without explicit user approval and plan review. Lists all commands with expected duration in spec.

## Workflow

1. **Check Existing State** — Run `terraform plan` in the target environment to see current drift. If there's unexpected drift, STOP and report to user before proceeding.
2. **Gather Context** — Read the relevant terraform module, migration files, and deployment config. Identify which environment is targeted (dev/staging/prod).
3. **Generate Spec** — List: resources to create/modify/destroy, migration steps, expected downtime (if any), rollback procedure, commands to execute with expected durations.
4. **Await Approval** — Present the spec with the terraform plan output. Do NOT apply until user explicitly confirms.
5. **Implement** — Apply terraform changes, run migrations, and deploy application code in the approved order.
6. **Verify** — Check health endpoints, run smoke tests, confirm monitoring shows healthy state. Expected: <5min for health to stabilize. If unhealthy, enter failure loop.
7. **Document** — Record deployment in team channel/log. Note the image tag or commit SHA deployed.

### Failure Recovery (max 3 retries)

6a. Check health endpoint and service logs → identify failure cause
6b. If config issue: fix and re-apply. If code issue: escalate to user.
6c. Re-check health
6d. After 3 failures → initiate rollback procedure, report to user

### Rollback

If deployment fails or user requests rollback:
1. **Application**: revert to previous container image tag (`terraform apply -var="image_tag=<previous>"`)
2. **Terraform**: `terraform apply` targeting the previous known-good state or revert the IaC commit and re-plan
3. **Database**: apply reverse migration (prefer forward-fix for data changes)
4. Verify health after rollback
5. Report what was reverted and current state

## Terraform Plan/Apply Workflow

1. Make changes in the appropriate module under `infra/`
2. Run plan to preview:

```bash
cd infra/<module>
terraform plan -out=tfplan
```

3. Review plan output carefully — check for destroys/replacements
4. Apply after review:

```bash
terraform apply tfplan
```

5. Commit the updated state if using local backend (prefer remote state)

## Environment Promotion

- Flow: `dev` → `staging` → `production`
- Each environment has its own tfvars and state file
- Promote by merging to the appropriate branch or triggering CI pipeline
- Verify in each environment before promoting to the next
- Use feature flags for risky features that need gradual rollout

## Database Migrations

- Run migrations before deploying application code (expand-then-contract)
- Steps:
  1. Write migration (additive only: new columns, tables, indexes)
  2. Deploy migration
  3. Deploy application code that uses new schema
  4. Clean up old columns/code in a follow-up migration
- Never drop columns or tables in the same deploy as the code change
- Test migrations against a copy of production data when possible

## Health Checks

- Every service must expose a health endpoint (`/health` or `/healthz`)
- Health check should verify: service running, critical dependencies reachable (DB, cache, downstream APIs)
- Configure readiness and liveness probes in k8s manifests:

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 30
readinessProbe:
  httpGet:
    path: /healthz
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 10
```

## Guardrails

- NEVER run `terraform apply` without reviewing plan output first
- NEVER apply to production without successful staging deployment
- NEVER drop database columns/tables in the same deploy as application code changes
- NEVER deploy without a documented rollback procedure
- NEVER skip health check verification after deployment
- NEVER ignore terraform plan showing unexpected resource destroys — stop and investigate
- NEVER deploy database migrations without testing against production-like data first

## Deploy Checklist

- [ ] Terraform plan reviewed (no unexpected destroys)
- [ ] Migrations tested and applied
- [ ] Health checks passing in target environment
- [ ] Monitoring/alerts confirmed
- [ ] Rollback plan documented
- [ ] Team notified of deployment

## References

- `steering/orchestration/local.md` — Terraform module layout, backend configuration, and local development environment setup
- `steering/security/policies.md` — Secrets management, container security, dependency security for deployment
