---
name: DevEnvSetupTiltConventions
description: Tilt + kind + nginx conventions for the dev-env-setup system — local k8s target, resource naming, reverse-proxy routing, non-root containers, and merge/diff-first rules for adopt mode. Read on demand by des-bootstrap, des-scaffold-service, and des-integration.
inclusion: manual
fileMatchPattern: [
  "**/Tiltfile",
  "**/nginx/nginx.conf",
  "**/k8s/**/*.yaml"
]
---

# dev-env-setup — Tilt / kind / nginx Conventions

## Local Kubernetes target: kind

The generated environment assumes **kind** as the local cluster. The Tiltfile does not
create or start a cluster; it assumes `kubectl` context points at a running kind cluster.
Preflight only reports whether `kind` is installed — it never creates clusters.

- `k8s_yaml(...)` for manifests under `k8s/` and per-service `k8s/*.yaml`.
- `docker_build('<image>', '<buildContext>', dockerfile='<dockerfile>')` for built services.
- `k8s_resource('<name>', port_forwards=[...], labels=[...], resource_deps=[...])`.
- Group resources with `labels` matching the descriptor `tiltResourceLabels`
  (e.g. `api`, `web`, `data`, `telemetry`, `gateway`, `worker`).

## Resource naming

- Tilt resource name == descriptor `name` == k8s Deployment/Service name (kebab-case).
- One Deployment + one Service per app microservice.
- Ports use the descriptor `ports[].name` for the k8s Service port name.

## nginx as reverse proxy + secure gateway

- Single nginx Deployment/Service named `gateway`, listening on `:80` in-cluster and
  port-forwarded to the host.
- The base `nginx/nginx.conf` (from `des-bootstrap`) contains security headers and an empty
  routes include; `des-integration` writes one `location` block per service that has an
  `nginxRoute`.
- Routing convention: `location <pathPrefix>/ { proxy_pass http://<name>:<upstreamPort>/; }`.
  When `stripPrefix` is true, the trailing-slash `proxy_pass` form strips the prefix.
- Security headers on all responses: `X-Content-Type-Options nosniff`, `X-Frame-Options DENY`,
  `Referrer-Policy strict-origin-when-cross-origin`. CORS is per-origin — never
  `*` with credentials (see SecurityPolicies steering).

### Route block template

```nginx
# --- BEGIN service:<name> ---
location <pathPrefix>/ {
    proxy_pass http://<name>:<upstreamPort>/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
# --- END service:<name> ---
```

The `BEGIN/END service:<name>` sentinels are how `des-integration` finds, replaces, or
preserves a block idempotently.

## Container hardening (all services)

- Run as non-root: set `securityContext.runAsNonRoot: true` and a non-zero `runAsUser` in
  the k8s manifest; use non-root/ distroless base images.
- No secrets in images or manifests-with-values committed to git. Use k8s `Secret` refs and
  env injection. `.dev-env/`, real secret files, and lockfile stay out of images.
- `readOnlyRootFilesystem: true` where the workload allows it.

## Greenfield generation

`des-integration` generates a fresh `Tiltfile` and `nginx.conf` from the full descriptor set.
Output is deterministic and byte-stable: descriptors are processed in sorted `name` order so
re-running yields identical files.

## Adopt mode — merge, never overwrite

When `.dev-env/mode.json` is `adopt`:

1. **Read before write.** Parse the existing `Tiltfile` and `nginx.conf`.
2. **Preserve hand-written content.** Any block NOT bounded by dev-env-setup sentinels is
   left byte-for-byte intact.
3. **Sentinel-scoped edits.** dev-env-setup-managed blocks are delimited:
   - Tiltfile: `# --- BEGIN des:<name> ---` / `# --- END des:<name> ---`
   - nginx: `# --- BEGIN service:<name> ---` / `# --- END service:<name> ---`
   Only these are added/updated/removed.
4. **Append new services**; update existing dev-env-managed blocks in place.
5. **Diff-first + confirm.** Before modifying a pre-existing shared file, produce a unified
   diff and require explicit confirmation. Never silently overwrite.
6. **Reuse existing infra.** If discovered descriptors already provide a `gateway` or
   `telemetry` resource, do not add duplicates — wire new services to the existing ones.

## Anti-patterns

- ❌ Creating or starting a kind cluster from an agent.
- ❌ Writing `latest` image tags into manifests (resolve + pin first).
- ❌ Overwriting a non-sentinel (hand-written) Tiltfile/nginx block.
- ❌ Root containers, or secrets baked into images/committed manifests.
- ❌ Non-deterministic generation (unsorted descriptor iteration).
