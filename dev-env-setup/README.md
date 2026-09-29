# dev-env-setup

A self-contained Kiro agent module that bootstraps a **Tilt-orchestrated Kubernetes
(kind) multi-microservice development environment**. A top-level orchestrator delegates to a
tree of sub-agents (which themselves orchestrate sub-agents) to plan a stack interactively,
scaffold each microservice concurrently, wire everything through an nginx reverse-proxy /
secure gateway with a full OpenTelemetry stack, and finalize with linting and dry-run
validation.

Works for **greenfield** workspaces and for **existing solutions** that already have a
`Tiltfile` and projects (**adopt mode** — additive, merge/diff-first, never overwrites
hand-written config).

## Install

File-level symlinks into a Kiro config dir (defaults to `~/.kiro`):

```bash
./install.sh                 # links into ~/.kiro
./install.sh /path/to/proj   # links into /path/to/proj/.kiro
./uninstall.sh               # removes only this module's symlinks (safe)
```

`install.sh` symlinks `agents/*.json` → `<target>/agents/`,
`steering/dev-env-setup/**` → `<target>/steering/dev-env-setup/`, and
`config/preferred-stack.json` → `<target>/config/`. `uninstall.sh` removes only symlinks that
resolve back into this module (real files and foreign symlinks are never touched).

## Usage

Run the `dev-env-setup` agent, giving it a target workspace path (or use the current dir).
It sequences:

1. **des-preflight** — probes `tilt`/`kubectl`/`kind`/`docker`/`helm` (read-only, no install)
   and detects greenfield vs adopt mode.
2. **des-discover** (adopt only) — reverse-engineers descriptors for existing services.
3. **des-stack-planner** — the interactive Q&A (API lang, RabbitMQ, Redis, web framework,
   socket API, database + vector, Celery, cron). Gap-fills in adopt mode.
4. **des-bootstrap** (greenfield) — base `Tiltfile`, nginx gateway, and the full telemetry
   stack (OTel Collector + Jaeger + Prometheus + Grafana).
5. **des-scaffold-orchestrator** — spawns **des-scaffold-service** in parallel (one per new
   service), then **des-integration** once to generate/merge `Tiltfile` + `nginx.conf`.
6. **des-finalize** — runs the `lint-safe-fix` skill on new React/Node projects (per-rule-type
   commit gate) and validates via Tiltfile parse + `kubectl apply --dry-run=client`.

The cluster is **never started** by the agents — you run `tilt up` yourself against a running
kind cluster.

## Design principles

- **Registration-manifest pattern.** Each scaffold agent writes `.tilt/services/<name>.json`;
  a single integration agent generates shared config from all descriptors — no write
  contention across parallel agents.
- **Pin, don't float.** `preferred-stack.json` uses `"latest"` as an instruction; agents
  resolve it to a concrete secure/stable version, write the pin into project manifests, and
  record it in `.dev-env/resolved-stack.lock.json`. No `^`/`~` ranges (SecurityPolicies).
- **Thin prompts, on-demand steering.** Authoritative detail lives in
  `steering/dev-env-setup/`; agents load only what they need. Workers return **JSON only**.
- **Idempotent / resumable.** Re-running skips already-produced artifacts; a single failed
  service does not re-scaffold the others.
- **Non-root containers, secrets via env**, per-origin CORS, `npm audit` high/critical gate.

## Layout

```
dev-env-setup/
├── install.sh / uninstall.sh
├── config/preferred-stack.json
├── steering/dev-env-setup/{orchestration-contract,tilt-conventions,telemetry-conventions}.md
└── agents/
    ├── dev-env-setup.json            (top orchestrator)
    ├── des-preflight.json
    ├── des-discover.json
    ├── des-bootstrap.json
    ├── des-stack-planner.json
    ├── des-scaffold-orchestrator.json
    ├── des-scaffold-service.json
    ├── des-integration.json
    └── des-finalize.json
```

## Generated workspace layout

```
<workspace>/
├── .dev-env/{mode.json, stack-plan.json, resolved-stack.lock.json}
├── .tilt/services/<name>.json
├── Tiltfile
├── nginx/nginx.conf
├── k8s/{telemetry,gateway,...}
└── <service-name>/
```
