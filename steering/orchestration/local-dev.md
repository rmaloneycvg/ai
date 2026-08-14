---
inclusion: manual
---

# Local Development Orchestration

## Steering Summary

Every project runs locally via **Tilt** with all services dockerized. Nginx serves as the application gateway (reverse proxy), routing requests to microservices by path prefix. All infrastructure is defined as code — Terraform for cloud, Kubernetes manifests for local (managed by Tilt).

## Why These Choices

| Decision | Why |
|----------|-----|
| **Tilt over docker-compose** | Live-update (hot reload into running containers) eliminates rebuild cycles. Native k8s support means local dev uses the same manifests as production. Resource grouping and manual triggers give control over what runs. |
| **nginx as gateway** | Single entry point for all services. Path-based routing matches production topology. SSL termination in one place. CORS/auth headers applied consistently at the edge, not per-service. |
| **Everything dockerized** | "Works on my machine" eliminated. New developers run `tilt up` on day one. No local runtime version conflicts (Node 18 vs 20, Python 3.11 vs 3.12). |
| **Kubernetes manifests (not just Docker)** | Same manifests deploy to local (Tilt), staging, and production. No translation layer between environments. Reduces "works locally but fails in prod" drift. |
| **Terraform for cloud** | Declarative, auditable, reviewable infrastructure. `terraform plan` shows exactly what will change before it happens. State tracking prevents drift. |
| **OAuth2 everywhere** | Consistent auth model across all services. No per-service auth implementations to maintain. Token-based = stateless scaling. |

## Non-Negotiable Requirements

- All services containerized with multi-stage Docker builds
- Tilt orchestrates the full local stack
- Nginx is the single entrypoint and router
- OAuth2 authentication on all web applications
- CORS properly configured on all web APIs
- Secrets never committed to source control

---

## Tilt — Local Orchestration

### Principles

- Every service has a Kubernetes manifest and a Dockerfile
- Tilt watches source files and live-reloads containers
- Services are grouped by function (web, worker, infra, tooling)
- Manual triggers for destructive operations (db seed, migrations)
- Resource dependencies declared explicitly

### Resource Labels

| Label      | Services                                    |
|------------|---------------------------------------------|
| `gateway`  | nginx                                       |
| `infra`    | postgres, redis, rabbitmq                   |
| `app`      | web apps, API services                      |
| `workers`  | celery workers, celery beat                 |
| `telemetry`| otel-collector, jaeger, prometheus, grafana |
| `tooling`  | db-seed, db-migrate, scripts                |

### Tiltfile Conventions

- Use `load('ext://namespace', ...)` and `load('ext://secret', ...)` extensions
- Secrets via `secret_from_dict()` pulling from environment variables
- `docker_build()` with `live_update` for hot reload (sync source, trigger rebuilds on lockfile changes)
- `k8s_resource()` with `resource_deps` for startup ordering, `port_forwards` for local access
- Manual triggers: `auto_init=False, trigger_mode=TRIGGER_MODE_MANUAL` for destructive ops
- Optional services gated by config flags: `config.define_bool('telemetry')`

### Service Topology

```
nginx-gateway (:8443)
├── /          → web-app (:3000)
├── /api/      → api-service (:8000)
├── /ws/       → websocket-service (:8001)
└── /telemetry → jaeger (:16686)

infra: postgres (:5432), redis (:6379), otel-collector (:4317)
workers: celery-worker, celery-beat (depend on postgres + redis)
```

### Quick Reference Commands

```bash
tilt up                        # Start all services
tilt up -- --telemetry         # Start with optional telemetry
tilt trigger db-seed           # Run database seed (manual)
tilt trigger db-migrate        # Run migration (manual)
tilt logs -f api-service       # Follow service logs
tilt down                      # Tear down
tilt down --delete-namespaces  # Tear down + delete volumes
```

---

## Nginx — Application Gateway

### Routing Pattern

- Upstreams match Kubernetes service names
- HTTP → HTTPS redirect on port 80
- Self-signed SSL cert generated during Docker build (`subjectAltName=DNS:localhost,IP:127.0.0.1`)
- WebSocket support on web-app location (Upgrade headers for HMR)
- `/api/` proxied with trailing-slash strip (`proxy_pass http://api_service/`)

### CORS (nginx-managed, not per-app)

- Headers set at nginx level: `Access-Control-Allow-Origin`, `Allow-Methods`, `Allow-Headers`, `Allow-Credentials`
- Explicit origin map — never wildcard with credentials
- Preflight `OPTIONS` returns 204 directly
- Applications should NOT duplicate CORS headers (exception: WebSocket upgrade)

### Rate Limiting

| Zone   | Rate     | Burst | Use Case              |
|--------|----------|-------|-----------------------|
| `api`  | 100r/s   | 20    | General API endpoints |
| `auth` | 10r/s    | 5     | Login, token refresh  |
| `upload`| 5r/s    | 2     | File uploads          |
| `ws`   | 50r/s    | 10    | WebSocket connections |

### Security Headers (all responses)

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## Docker — Multi-Stage Builds

### Pattern (all services)

1. **deps stage** — install dependencies only (cache-friendly)
2. **production stage** — copy deps + source, non-root user, expose port
3. **development stage** — extends production with dev tools (debugpy, watchfiles, --reload flags)

### Rules

- Non-root user (`adduser --disabled-password appuser`, then `USER appuser`)
- `fall_back_on` in live_update for lockfile changes (triggers full rebuild)
- `sync()` for source directories (hot reload without rebuild)
- Use `target='development'` in Tiltfile `docker_build()` for local

---

## Kubernetes Manifests

### Local (Tilt-managed, in `k8s/` directory)

- Deployments with `replicas: 1`
- `envFrom: secretRef` pointing to Tilt-managed secrets
- Readiness probes on `/health` endpoint
- Resource requests/limits set (128Mi–512Mi memory, 100m–500m CPU)
- Jobs for manual operations (db-seed, db-migrate) with `backoffLimit: 1`

### Production (Terraform-managed)

- Helm charts or Kustomize overlays from same base manifests
- Tilt manifests are NOT used in production
- Production k8s provisioned by Terraform (EKS/GKE)

---

## Terraform

### Directory Structure

```
terraform/
├── environments/{dev,staging,production}/  # Per-env state + tfvars
├── modules/{networking,kubernetes,database,cdn,monitoring}/
└── shared/backend.tf, providers.tf
```

### Conventions

- Remote state in S3/GCS with locking (DynamoDB/GCS)
- Naming: `{project}-{environment}-{resource}`
- Tags: `project`, `environment`, `managed-by=terraform` on all resources
- Secrets via cloud secret managers — never in tfvars
- Reusable modules, separate state per environment

---

## OAuth2 — Authentication

### Token Flow

1. Frontend redirects to `/api/auth/login`
2. API redirects to OAuth provider
3. Provider redirects back to `/api/auth/callback`
4. API exchanges code for tokens, creates session
5. Session token set as HttpOnly, Secure, SameSite=Strict cookie
6. Subsequent requests authenticated via session cookie
7. API endpoints return 401 if session invalid

### Local Development

- Real OAuth provider with localhost redirect URI, OR
- Mock OAuth server as a Tilt-managed service (for offline dev)

---

## Security Checklist (every service)

- [ ] Non-root user in containers
- [ ] Read-only filesystem where possible
- [ ] Resource limits set (CPU, memory)
- [ ] Health checks configured
- [ ] No secrets in Docker images or manifests
- [ ] Dependencies pinned to exact versions
- [ ] Security headers via nginx
- [ ] Input validation on all endpoints
- [ ] Parameterized queries (no SQL string concatenation)
- [ ] Rate limiting on auth and public endpoints

---

## Secrets Management

| Context     | Method                                          |
|-------------|-------------------------------------------------|
| Local dev   | `.env` files (gitignored) → k8s secrets via Tilt |
| CI/CD       | Pipeline secrets (GitHub Secrets, GitLab CI vars) |
| Production  | Cloud secret manager (AWS SM, GCP SM, Vault)    |

---

## File Structure Expectation

```
project-root/
├── Tiltfile
├── .env.local              # gitignored
├── docker/{nginx,api,web,celery,postgres}/Dockerfile
├── k8s/{nginx,postgres,redis,web-app,api-service,celery-worker,celery-beat,otel-collector,jaeger,db-seed-job,db-migrate-job}.yaml
├── terraform/{environments,modules,shared}/
├── src/                    # Web app source
├── api/                    # API service source
└── tasks/                  # Celery tasks
```

---

## Docker-Compose → Tilt Migration

| docker-compose          | Tilt/k8s equivalent                          |
|-------------------------|----------------------------------------------|
| `services.X.image`     | `docker_build()` in Tiltfile                 |
| `services.X.build`     | `docker_build()` with dockerfile path        |
| `services.X.ports`     | `port_forwards` in `k8s_resource()`          |
| `services.X.volumes`   | `live_update` with `sync()`                  |
| `services.X.environment`| `envFrom` / `env` in k8s manifest           |
| `services.X.depends_on`| `resource_deps` in `k8s_resource()`          |
| `services.X.command`   | `command` in container spec                  |
| `services.X.healthcheck`| `readinessProbe`/`livenessProbe` in k8s     |
| `networks`             | k8s Services (automatic DNS)                 |
| `volumes` (named)      | PersistentVolumeClaims                       |
