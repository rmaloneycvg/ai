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

**Non-negotiable requirements:**
- All services containerized with multi-stage Docker builds
- Tilt orchestrates the full local stack
- Nginx is the single entrypoint and router
- OAuth2 authentication on all web applications
- CORS properly configured on all web APIs
- Secrets never committed to source control

---

## 1. Tilt — Local Orchestration

Tilt is the **only** local orchestration tool. No docker-compose in production workflows.

### Principles

- Every service has a Kubernetes manifest and a Dockerfile
- Tilt watches source files and live-reloads containers
- Services are grouped by function (web, worker, infra, tooling)
- Manual triggers for destructive operations (db seed, migrations)
- Resource dependencies declared explicitly

### Tiltfile Structure

```python
# Tiltfile

# ============================================================
# Configuration
# ============================================================
load('ext://namespace', 'namespace_create', 'namespace_inject')
load('ext://secret', 'secret_from_dict')

# Environment
config.define_string('environment', args=True)
cfg = config.parse()
env = cfg.get('environment', 'development')

# ============================================================
# Secrets
# ============================================================
k8s_yaml(secret_from_dict('app-secrets', inputs={
    'DATABASE_URL': os.getenv('DATABASE_URL', 'postgres://app:app@postgres:5432/app'),
    'OAUTH_CLIENT_ID': os.getenv('OAUTH_CLIENT_ID', 'local-dev-client'),
    'OAUTH_CLIENT_SECRET': os.getenv('OAUTH_CLIENT_SECRET', 'local-dev-secret'),
    'SECRET_KEY': os.getenv('SECRET_KEY', 'local-dev-key-not-for-production'),
}))

# ============================================================
# Infrastructure Services
# ============================================================

# --- Postgres ---
docker_build('postgres-local', './docker/postgres',
    build_args={'POSTGRES_VERSION': '16'})
k8s_yaml('k8s/postgres.yaml')
k8s_resource('postgres',
    port_forwards='5432:5432',
    labels=['infra'])

# --- Redis ---
k8s_yaml('k8s/redis.yaml')
k8s_resource('redis',
    port_forwards='6379:6379',
    labels=['infra'])

# --- Nginx Gateway ---
docker_build('nginx-gateway', './docker/nginx',
    live_update=[
        sync('./docker/nginx/conf.d/', '/etc/nginx/conf.d/'),
        run('nginx -s reload', trigger=['./docker/nginx/conf.d/']),
    ])
k8s_yaml('k8s/nginx.yaml')
k8s_resource('nginx-gateway',
    port_forwards=['8080:80', '8443:443'],
    resource_deps=['web-app', 'api-service'],
    labels=['gateway'])

# ============================================================
# Application Services
# ============================================================

# --- Web Application ---
docker_build('web-app', '.',
    dockerfile='docker/web/Dockerfile',
    live_update=[
        fall_back_on(['package.json', 'requirements.txt']),
        sync('./src', '/app/src'),
        sync('./public', '/app/public'),
    ])
k8s_yaml('k8s/web-app.yaml')
k8s_resource('web-app',
    resource_deps=['postgres', 'redis'],
    labels=['app'])

# --- API Service ---
docker_build('api-service', '.',
    dockerfile='docker/api/Dockerfile',
    live_update=[
        fall_back_on(['requirements.txt', 'poetry.lock']),
        sync('./api', '/app/api'),
        run('pip install -r requirements.txt', trigger=['requirements.txt']),
    ])
k8s_yaml('k8s/api-service.yaml')
k8s_resource('api-service',
    resource_deps=['postgres', 'redis'],
    labels=['app'])

# ============================================================
# Worker Services
# ============================================================

# --- Celery Worker ---
docker_build('celery-worker', '.',
    dockerfile='docker/celery/Dockerfile',
    live_update=[
        sync('./tasks', '/app/tasks'),
        sync('./api', '/app/api'),
    ])
k8s_yaml('k8s/celery-worker.yaml')
k8s_resource('celery-worker',
    resource_deps=['postgres', 'redis'],
    labels=['workers'])

# --- Celery Beat (Scheduler) ---
k8s_yaml('k8s/celery-beat.yaml')
k8s_resource('celery-beat',
    resource_deps=['redis'],
    labels=['workers'])

# ============================================================
# Telemetry
# ============================================================
k8s_yaml('k8s/telemetry.yaml')
k8s_resource('otel-collector',
    port_forwards='4317:4317',
    labels=['telemetry'])
k8s_resource('jaeger',
    port_forwards='16686:16686',
    labels=['telemetry'])

# ============================================================
# Manual Triggers (Destructive Operations)
# ============================================================

# --- DB Seed ---
k8s_yaml('k8s/db-seed-job.yaml')
k8s_resource('db-seed',
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
    resource_deps=['postgres'],
    labels=['tooling'])

# --- DB Migrate ---
k8s_yaml('k8s/db-migrate-job.yaml')
k8s_resource('db-migrate',
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
    resource_deps=['postgres'],
    labels=['tooling'])
```

### Resource Labels Convention

| Label      | Services                                    |
|------------|---------------------------------------------|
| `gateway`  | nginx                                       |
| `infra`    | postgres, redis, rabbitmq                   |
| `app`      | web apps, API services                      |
| `workers`  | celery workers, celery beat                 |
| `telemetry`| otel-collector, jaeger, prometheus, grafana |
| `tooling`  | db-seed, db-migrate, scripts                |

---

## 2. Nginx — Application Gateway

Nginx is the **single entrypoint** for all local traffic. It routes by path prefix to upstream services.

### Core nginx.conf

```nginx
# docker/nginx/nginx.conf
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    client_max_body_size 50m;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=10r/s;

    # Gzip
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    include /etc/nginx/conf.d/*.conf;
}
```

### Route Configuration (conf.d/default.conf)

```nginx
# docker/nginx/conf.d/default.conf

# Upstreams — match Kubernetes service names
upstream web_app {
    server web-app:3000;
}

upstream api_service {
    server api-service:8000;
}

upstream telemetry_ui {
    server jaeger:16686;
}

# SSL Configuration (local self-signed)
server {
    listen 80;
    server_name localhost;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate /etc/nginx/ssl/localhost.crt;
    ssl_certificate_key /etc/nginx/ssl/localhost.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ---- CORS Headers (applied globally) ----
    # Per-location overrides possible
    set $cors_origin $http_origin;

    # ---- Web Application (default route) ----
    location / {
        proxy_pass http://web_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for HMR / live reload)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # ---- API Service ----
    location /api/ {
        limit_req zone=api burst=20 nodelay;

        proxy_pass http://api_service/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS
        add_header Access-Control-Allow-Origin $cors_origin always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, PATCH, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Request-ID" always;
        add_header Access-Control-Allow-Credentials "true" always;
        add_header Access-Control-Max-Age 86400 always;

        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }

    # ---- Auth endpoints (stricter rate limit) ----
    location /api/auth/ {
        limit_req zone=auth burst=5 nodelay;

        proxy_pass http://api_service/auth/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS (same as /api/)
        add_header Access-Control-Allow-Origin $cors_origin always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        add_header Access-Control-Allow-Credentials "true" always;

        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }

    # ---- Telemetry UI (dev only) ----
    location /telemetry/ {
        proxy_pass http://telemetry_ui/;
        proxy_set_header Host $host;
    }

    # ---- Health check ----
    location /health {
        access_log off;
        return 200 'ok';
        add_header Content-Type text/plain;
    }
}
```

### SSL for Local Development

Generate self-signed certs during Docker build:

```dockerfile
# docker/nginx/Dockerfile
FROM nginx:1.25-alpine

RUN apk add --no-cache openssl && \
    mkdir -p /etc/nginx/ssl && \
    openssl req -x509 -nodes -days 365 \
      -subj "/CN=localhost" \
      -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1" \
      -newkey rsa:2048 \
      -keyout /etc/nginx/ssl/localhost.key \
      -out /etc/nginx/ssl/localhost.crt

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/
```

### Rate Limiting Patterns

| Zone   | Rate     | Burst | Use Case                    |
|--------|----------|-------|-----------------------------|
| `api`  | 100r/s   | 20    | General API endpoints       |
| `auth` | 10r/s    | 5     | Login, token refresh        |
| `upload`| 5r/s    | 2     | File uploads                |
| `ws`   | 50r/s    | 10    | WebSocket connections       |

---

## 3. Docker — Multi-Stage Builds

Every service uses multi-stage builds. The pattern:

### Python Service (API / Celery)

```dockerfile
# docker/api/Dockerfile

# Stage 1: Dependencies
FROM python:3.12-slim AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim AS production
WORKDIR /app
COPY --from=deps /install /usr/local
COPY ./api /app/api
COPY ./tasks /app/tasks

# Non-root user
RUN adduser --disabled-password --no-create-home appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 3: Development (extends production with dev tools)
FROM production AS development
USER root
RUN pip install --no-cache-dir debugpy watchfiles
USER appuser
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Node.js Service (Web App)

```dockerfile
# docker/web/Dockerfile

# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Stage 2: Build
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 3: Production
FROM node:20-alpine AS production
WORKDIR /app
RUN adduser -D appuser
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json .
USER appuser
EXPOSE 3000
CMD ["node", "dist/server.js"]

# Stage 4: Development
FROM node:20-alpine AS development
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
USER node
EXPOSE 3000
CMD ["npm", "run", "dev"]
```

### Build Target Selection in Tilt

```python
# In Tiltfile — use development target locally
docker_build('api-service', '.',
    dockerfile='docker/api/Dockerfile',
    target='development',
    live_update=[...])
```

---

## 4. Kubernetes — Local and Production

### Local (Tilt-managed)

Tilt uses a local k8s cluster (k3d or kind). Manifests live in `k8s/` directory.

#### Example Service Manifest

```yaml
# k8s/api-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  labels:
    app: api-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
    spec:
      containers:
        - name: api-service
          image: api-service
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: app-secrets
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
```

#### DB Seed Job (Manual Trigger)

```yaml
# k8s/db-seed-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-seed
spec:
  template:
    spec:
      containers:
        - name: db-seed
          image: api-service
          command: ["python", "-m", "scripts.seed_database"]
          envFrom:
            - secretRef:
                name: app-secrets
      restartPolicy: Never
  backoffLimit: 1
```

### Production (Terraform-managed)

Production Kubernetes is provisioned and managed by Terraform. Tilt manifests are **not** used in production — they are development-only. Production uses Helm charts or Kustomize overlays generated from the same base manifests.

---

## 5. Terraform — Infrastructure as Code

### Directory Structure

```
terraform/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   └── ...
│   └── production/
│       └── ...
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── kubernetes/
│   │   └── ...
│   ├── database/
│   │   └── ...
│   ├── cdn/
│   │   └── ...
│   └── monitoring/
│       └── ...
└── shared/
    ├── backend.tf
    └── providers.tf
```

### Expectations

- **State**: Remote state in S3/GCS with locking (DynamoDB/GCS)
- **Modules**: Reusable modules for each infrastructure component
- **Environments**: Separate state per environment, same modules with different vars
- **Secrets**: Use cloud secret managers (AWS Secrets Manager, GCP Secret Manager) — never in tfvars
- **Naming**: `{project}-{environment}-{resource}` convention
- **Tags**: All resources tagged with `project`, `environment`, `managed-by=terraform`

### Key Resources Managed by Terraform

- Kubernetes cluster (EKS/GKE)
- Managed databases (RDS/CloudSQL)
- Load balancers and CDN
- DNS records
- SSL certificates (ACM/managed certs)
- IAM roles and policies
- VPC and networking
- Monitoring and alerting

---

## 6. OAuth2 — Authentication

**All web applications MUST use OAuth2 for authentication.** No custom auth schemes.

### Implementation Pattern

```
┌──────────┐     ┌───────────┐     ┌──────────────┐
│  Browser  │────▶│  Nginx    │────▶│  API Service │
│           │◀────│  Gateway  │◀────│  (validates) │
└──────────┘     └───────────┘     └──────────────┘
      │                                      │
      │         ┌──────────────┐             │
      └────────▶│  OAuth2      │◀────────────┘
                │  Provider    │
                └──────────────┘
```

### Required OAuth2 Configuration

```python
# Environment variables (in secrets)
OAUTH_PROVIDER=google  # or github, okta, auth0, cognito
OAUTH_CLIENT_ID=...
OAUTH_CLIENT_SECRET=...
OAUTH_REDIRECT_URI=https://localhost:8443/api/auth/callback
OAUTH_SCOPES=openid,email,profile
```

### Local Development OAuth2

For local development, use one of:
1. **Real OAuth provider** with localhost redirect URI configured
2. **Mock OAuth server** as a Tilt-managed service (for offline dev)

```python
# Tiltfile addition for mock OAuth (optional)
docker_build('mock-oauth', './docker/mock-oauth')
k8s_yaml('k8s/mock-oauth.yaml')
k8s_resource('mock-oauth',
    port_forwards='9090:9090',
    labels=['infra'])
```

### Token Flow

1. Frontend redirects to `/api/auth/login`
2. API redirects to OAuth provider
3. Provider redirects back to `/api/auth/callback`
4. API exchanges code for tokens, creates session
5. Session token set as HttpOnly, Secure, SameSite=Strict cookie
6. Subsequent requests authenticated via session cookie
7. API endpoints return 401 if session invalid

---

## 7. CORS — Cross-Origin Resource Sharing

### Rules

- CORS headers are set at the **nginx level** (not duplicated in application code)
- Allowed origins are explicit — no wildcards in production
- Credentials mode requires explicit origin (not `*`)
- Preflight responses cached for 24 hours

### Local Development CORS Config

```nginx
# Allowed origins for local dev
map $http_origin $cors_allowed_origin {
    default "";
    "https://localhost:8443" "https://localhost:8443";
    "http://localhost:3000" "http://localhost:3000";
    "http://localhost:5173" "http://localhost:5173";
}
```

### Application-Level CORS (Backup/Fine-Grained)

Applications should **not** add CORS headers if nginx is handling them. If an application must handle CORS directly (e.g., WebSocket upgrade), use the framework's middleware:

```python
# FastAPI example
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # From env
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    max_age=86400,
)
```

---

## 8. Security — First-Class Concern

### Secrets Management

| Context     | Method                                          |
|-------------|-------------------------------------------------|
| Local dev   | `.env` files (gitignored) loaded into k8s secrets via Tilt |
| CI/CD       | Pipeline secrets (GitHub Secrets, GitLab CI vars) |
| Production  | Cloud secret manager (AWS SM, GCP SM, Vault)    |

### .env File Pattern

```bash
# .env.local (NEVER committed)
DATABASE_URL=postgres://app:app@localhost:5432/app
OAUTH_CLIENT_ID=local-client-id
OAUTH_CLIENT_SECRET=local-client-secret
SECRET_KEY=local-dev-only-key
REDIS_URL=redis://localhost:6379/0
```

### Security Checklist for Every Service

- [ ] Non-root user in Docker containers
- [ ] Read-only filesystem where possible
- [ ] Resource limits set (CPU, memory)
- [ ] Health checks configured
- [ ] No secrets in Docker images or manifests
- [ ] Dependencies pinned to exact versions
- [ ] Security headers set (via nginx)
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] Rate limiting on auth and public endpoints

### Security Headers (nginx)

```nginx
# Add to server block
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

---

## 9. Multi-Service Architecture

### Standard Service Topology

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx Gateway (:8443)                  │
├─────────────────────────────────────────────────────────┤
│  /          → Web App (:3000)                            │
│  /api/      → API Service (:8000)                        │
│  /ws/       → WebSocket Service (:8001)                  │
│  /telemetry → Jaeger UI (:16686)                         │
└─────────────────────────────────────────────────────────┘
         │              │              │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │ Postgres │   │  Redis  │   │  OTEL   │
    │  (:5432) │   │ (:6379) │   │ (:4317) │
    └─────────┘   └─────────┘   └─────────┘
                        │
                   ┌────▼────┐
                   │ Celery  │
                   │ Workers │
                   └─────────┘
```

### Service Categories and Tilt Configuration

**Always auto-start:**
- nginx-gateway
- postgres
- redis
- web-app
- api-service
- celery-worker
- celery-beat
- otel-collector

**Manual trigger only:**
- db-seed
- db-migrate
- load-test

**Optional (disabled by default):**
- jaeger (enable with `tilt up -- --telemetry`)
- grafana
- prometheus
- mailhog (email testing)

```python
# Tiltfile — optional services
config.define_bool('telemetry')
cfg = config.parse()

if cfg.get('telemetry', False):
    k8s_yaml('k8s/jaeger.yaml')
    k8s_resource('jaeger', port_forwards='16686:16686', labels=['telemetry'])
    k8s_yaml('k8s/grafana.yaml')
    k8s_resource('grafana', port_forwards='3001:3000', labels=['telemetry'])
```

---

## 10. Docker-Compose to Tilt Migration

### Migration Checklist

When migrating from docker-compose to Tilt:

1. **Create k8s/ directory** with a manifest for each service
2. **Create Dockerfiles** with multi-stage builds (replace `image:` references)
3. **Convert `depends_on`** to `resource_deps` in Tiltfile
4. **Convert `volumes`** to `live_update` sync rules
5. **Convert `environment`** to Kubernetes Secrets or ConfigMaps
6. **Convert `ports`** to `port_forwards` in Tiltfile
7. **Convert `command`** to container `command` in k8s manifest
8. **Remove docker-compose.yml** once migration verified

### Mapping Table

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

---

## Quick Reference Commands

```bash
# Start all services
tilt up

# Start with telemetry
tilt up -- --telemetry

# Trigger db seed (from Tilt UI or CLI)
tilt trigger db-seed

# Trigger migration
tilt trigger db-migrate

# View logs for a service
tilt logs -f api-service

# Tear down
tilt down

# Tear down and delete volumes
tilt down --delete-namespaces
```

---

## File Structure Expectation

```
project-root/
├── Tiltfile
├── .env.local              # gitignored
├── docker/
│   ├── nginx/
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── conf.d/
│   │       └── default.conf
│   ├── api/
│   │   └── Dockerfile
│   ├── web/
│   │   └── Dockerfile
│   ├── celery/
│   │   └── Dockerfile
│   └── postgres/
│       ├── Dockerfile
│       └── init.sql
├── k8s/
│   ├── nginx.yaml
│   ├── postgres.yaml
│   ├── redis.yaml
│   ├── web-app.yaml
│   ├── api-service.yaml
│   ├── celery-worker.yaml
│   ├── celery-beat.yaml
│   ├── otel-collector.yaml
│   ├── jaeger.yaml
│   ├── db-seed-job.yaml
│   └── db-migrate-job.yaml
├── terraform/
│   ├── environments/
│   ├── modules/
│   └── shared/
├── src/                    # Web app source
├── api/                    # API service source
└── tasks/                  # Celery tasks
```
