# AI Workspace

Portable AI agent configurations, steering documents, skills, and MCP tooling. Designed for Kiro CLI but adaptable to any AI coding assistant.

## Structure

```
ai/
├── steering/                           # Behavioral guidance loaded into agent context
│   ├── DOTNET-EntityFrameworkQueries.md # EF Core query guardrails, CQRS, bulk ops, encryption
│   ├── react/
│   │   ├── dependency-graph.md        # React stack choices (shadcn, Zustand, TQ, etc.)
│   │   ├── custom-hooks.md            # Custom hook extraction patterns
│   │   ├── tanstack-query-hooks.md    # TanStack Query hook patterns
│   │   ├── react-router-hooks.md      # React Router v6+ hook patterns
│   │   ├── use-callback.md            # useCallback steering
│   │   ├── use-context.md             # useContext vs Zustand decisions
│   │   ├── use-debug-value.md         # useDebugValue for custom hooks
│   │   ├── use-deferred-value.md      # useDeferredValue for expensive renders
│   │   ├── use-effect.md              # useEffect patterns and anti-patterns
│   │   ├── use-effect-event.md        # useEffectEvent (experimental)
│   │   ├── use-imperative-handle.md   # useImperativeHandle for ref APIs
│   │   ├── use-layout-effect.md       # useLayoutEffect for DOM measurement
│   │   ├── use-memo.md                # useMemo steering
│   │   ├── use-optimistic.md          # useOptimistic for server actions
│   │   ├── use-reducer.md             # useReducer state machine patterns
│   │   ├── use-ref.md                 # useRef patterns and pitfalls
│   │   ├── use-sync-external-store.md # useSyncExternalStore for browser APIs
│   │   └── use-transition.md          # useTransition for non-blocking updates
│   ├── nextjs/
│   │   ├── overview.md                # What Next.js replaces vs keeps from React stack
│   │   ├── app-router.md              # File-based routing, layouts, parallel routes
│   │   ├── server-components.md       # RSC vs client component decisions
│   │   ├── data-patterns.md           # ISR, server actions, route handlers
│   │   └── middleware.md              # Auth, redirects, A/B testing at the edge
│   └── security/
│       └── policies.md                # Auth, validation, CORS, secrets, headers
├── skills/                             # On-demand capability directories (SKILL.md + supporting files)
│   ├── design/                        # Plan new features interactively (clarify → research → plan.md)
│   │   └── SKILL.md
│   ├── diagnose/                      # Test-first debugging for .kiro/issues/ reports
│   │   └── SKILL.md
│   ├── diagram-spec/                  # Mermaid diagram authoring (architecture, flowchart, ER, etc.)
│   │   ├── SKILL.md
│   │   ├── assets/
│   │   │   └── puppeteer-config.json
│   │   ├── references/                # Per-diagram-type reference docs
│   │   └── scripts/
│   │       └── validate-mermaid.sh
│   ├── documentation/                 # README generation, API docs, runbooks, ADRs
│   │   └── SKILL.md
│   ├── execute/                       # Run active plan task groups via subagent delegation
│   │   └── SKILL.md
│   ├── flywheel/                      # Analyze sessions for correction patterns → improve config
│   │   └── SKILL.md
│   ├── git-workflow/                  # Branching, conventional commits, PR prep, hotfix
│   │   ├── SKILL.md
│   │   ├── hooks/                     # Git hook shell shims (commit-msg, pre-push)
│   │   ├── references/                # Commitlint config, PR template, revert workflow, submodules
│   │   └── scripts/                   # Python CLI (branch, commit, prepare_pr, hotfix, merge, promote)
│   │       ├── setup.sh
│   │       ├── pyproject.toml
│   │       └── src/
│   │           ├── branch.py
│   │           ├── commit.py
│   │           ├── prepare_pr.py
│   │           ├── merge_pr.py
│   │           ├── hotfix.py
│   │           ├── promote.py
│   │           └── lib/               # Shared: conventional, detect_changes, git_ops, ticket
│   ├── harvest-debt/                  # Collect SHORTCUT: markers into docs/debt.md ledger
│   │   └── SKILL.md
│   └── resume-content-writer/         # Tailored resume bullets, cover letters, scoring from JD
│       ├── SKILL.md
│       ├── references/                # Experience data, guardrails, formatting rules, voice
│       └── scripts/                   # Python: generate_docx, parse_resumes, create_templates
│           ├── setup.sh
│           ├── generate_docx.py
│           ├── parse_resumes.py
│           ├── create_templates.py
│           └── requirements.txt
├── agents/                             # Agent persona configs (JSON)
│   ├── general-dev.json               # Full-stack: broad tool access, suggests specialists
│   ├── react-architecture.json        # Sub-agent: UI architecture decisions (opus)
│   ├── react-frontend.json            # React/Next.js only, no shell/db access
│   ├── react-orchestrator.json        # Orchestrator: routes to sub-agents by task type
│   ├── react-scaffold.json            # Sub-agent: component scaffolding (haiku)
│   ├── react-styling.json             # Sub-agent: Tailwind/shadcn styling (haiku)
│   ├── react-testing.json             # Sub-agent: tests and stories (sonnet)
│   ├── resume-builder.json            # Resume generation orchestrator
│   └── work-summary.json              # Daily work summary tracker (git, AI sessions, browser)
├── hooks/                              # Kiro CLI hooks (pre/post tool-use guards)
│   ├── 01-check-secrets.json          # Block writes containing credential-shaped strings
│   ├── 02-guard-secret-reads.json     # Guard reads of .env, credentials, private keys
│   ├── 03-guard-config-writes.json    # Guard writes to sensitive config files
│   ├── 10-validate-environment.json   # Validate environment before operations
│   ├── 20-git-context.json            # Inject git context into prompts
│   ├── 50-rtk-compress.json           # Compress RTK context
│   └── scripts/                       # Shell scripts invoked by hook actions
│       ├── check-secrets.sh
│       ├── git-context.sh
│       ├── guard-config-writes.sh
│       ├── guard-destructive-commands.sh
│       ├── guard-secret-reads.sh
│       ├── rtk-compress.sh
│       └── validate-environment.sh
├── knowledge/                          # Reference documents for semantic search / RAG
│   ├── csharp/
│   │   ├── dapper-antipatterns.md
│   │   ├── dotnet-architecture-cheatsheet.md
│   │   ├── efcore-antipatterns.md
│   │   └── efcore-query-patterns.md
│   ├── mssql/
│   │   ├── mssql-cheatsheet.md
│   │   └── query-performance.md
│   └── nextjs/
│       ├── data-patterns.md
│       └── middleware.md
├── mcp/                                # MCP server definitions + tool scripts
│   └── mcp-scripts/
│       ├── servers/                    # MCP server entry points
│       │   ├── git.ts                 # git_status tool
│       │   ├── grafana.ts             # Grafana dashboards, reports, annotations, self-healing
│       │   ├── io.ts                  # read_json, write_json tools
│       │   ├── jaeger.ts             # Distributed tracing: search, bottlenecks, Kiro traces
│       │   ├── jira.ts               # Jira Cloud API (issues, sprints, metrics, links)
│       │   ├── linear.ts             # Linear GraphQL API (issues, cycles, projects, docs)
│       │   ├── postgres.ts            # postgres_query, postgres_seed tools
│       │   ├── prometheus.ts          # PromQL queries, metric discovery, alerting, Kiro telemetry
│       │   ├── rag.ts                 # rag_search, rag_status (semantic search over steering)
│       │   └── work-summary.ts        # Daily work summary generation + config
│       ├── lib/
│       │   └── exec-python.ts         # Python execution helper
│       ├── git/
│       │   └── status.ts              # Parsed git status implementation
│       ├── grafana/
│       │   ├── client.ts             # Grafana HTTP client
│       │   ├── mutations.ts          # Annotations, ticket creation, self-healing triggers
│       │   └── queries.ts            # Dashboard search, query, versions, reports
│       ├── io/
│       │   ├── read-json.ts           # Read and validate JSON files
│       │   └── write-json.ts          # Write JSON with formatting
│       ├── jaeger/
│       │   ├── client.ts             # Jaeger HTTP client
│       │   └── queries.ts            # Trace search, bottleneck analysis, Kiro session traces
│       ├── jira/
│       │   ├── client.ts             # Jira REST API v3 client (auth, fetch wrapper)
│       │   ├── queries.ts            # Search, sprints, boards, sprint metrics
│       │   └── mutations.ts          # Create issues, sprints, links, transitions, comments
│       ├── linear/
│       │   ├── client.ts             # Linear GraphQL client (auth, query wrapper)
│       │   ├── queries.ts            # Teams, issues, projects, cycles, cycle metrics
│       │   └── mutations.ts          # Create issues, projects, cycles, documents, relations
│       ├── postgres/
│       │   ├── query.py               # Parameterized read-only queries
│       │   └── seed.py                # Run SQL seed files
│       ├── prometheus/
│       │   ├── client.ts             # Prometheus HTTP client
│       │   └── queries.ts            # PromQL execution, metric discovery, Kiro telemetry
│       └── work-summary/
│           ├── aggregator.ts          # Combine collector outputs into unified timeline
│           ├── ai-flagger.ts          # Flag AI-assisted work (Kiro session overlap)
│           ├── categorizer.ts         # Categorize work items (Features, Refactors, Tests, Docs)
│           ├── config.ts              # Configuration management (workspace paths, collectors)
│           ├── renderer.ts            # Render summaries as JSON + Markdown
│           ├── types.ts               # Shared type definitions
│           └── collectors/
│               ├── chrome-collector.ts    # Browser activity
│               ├── git-collector.ts       # Git commit history
│               ├── kiro-collector.ts      # Kiro AI session activity
│               ├── google-meet-collector.ts
│               ├── outlook-collector.ts
│               ├── slack-collector.ts
│               ├── teams-collector.ts
│               ├── zoom-collector.ts
│               └── time-estimator.ts      # Edit time estimation from git + file mtimes
├── config/                             # Per-user configuration
│   ├── permissions.yaml               # Kiro CLI user-global permissions
│   ├── .kiroignore                    # Files excluded from Kiro context
│   └── resume/
│       └── experience.schema.json     # Schema for experience data (tracked)
├── templates/                          # Default stub templates (copied to projects, not loaded into context)
│   └── sdlc/
│       ├── preferred-stack.md         # Team technology preferences baseline
│       ├── scope-profile.md           # Project scope dimensions for stack evaluation
│       ├── high-level-architecture.md # Technology-agnostic system diagram
│       ├── workflow-diagrams.md       # Data flow and interaction pattern diagrams
│       ├── gap-risk-assessment.md     # Stack risk matrix with all dimensions
│       ├── stack-debate.md            # Structured pros/cons for contested decisions
│       ├── design-architecture.md     # Final design document with selected stack
│       ├── epics.json                 # Epic/story/task JSON schema with foundation epic
│       ├── epic-document.md           # Human-readable epic document template
│       └── sprint-plan.md            # Sprint plan with capacity and dependency tracking
├── link.sh                             # Create .kiro/ in another project with symlinks back
└── .gitignore
```

## Concepts

| Concept | What it is | How it's used |
|---------|-----------|---------------|
| **Steering** | Prescriptive docs that shape agent behavior: technology choices, patterns, security rules | Loaded as always-in-context references in agent configs or via Kiro rules |
| **Skills** | Directory-based capability units (SKILL.md + references + scripts). Each skill is one focused capability | Loaded on-demand — only metadata at startup, full content when triggered by intent |
| **Agents** | JSON configs that compose a persona from steering + skills + tools | Selected with `kiro --agent <name>` — each restricts scope, tools, and file access |
| **Hooks** | JSON-defined guards that intercept tool calls (pre/post) to enforce security policies | Evaluated automatically by Kiro CLI before/after tool execution |
| **Knowledge** | Reference documents organized by domain for semantic search | Indexed for RAG search via the `rag` MCP server |
| **MCP Scripts** | Small tool implementations (TypeScript/Python) invoked via Model Context Protocol | Declared in agent `mcpServers` — agents call them like functions |
| **Templates** | Stub markdown/JSON files copied into projects as starting points | Not loaded into context — used by SDLC skills to scaffold planning docs |

---

## Agents

Each agent is a focused persona with specific tool access, steering context, and file write restrictions.

### Primary Agents (user-facing)

| Agent | Command | Purpose |
|-------|---------|---------|
| `general-dev` | `kiro --agent dev` | Full-stack development. Broad access, asks before destructive ops. Suggests specialized agents when relevant. |
| `react-frontend` | `kiro --agent react-frontend` | React/Next.js development. No shell or database access. Writes restricted to `src/`. |
| `react-orchestrator` | `kiro --agent react-orchestrator` | Multi-agent pipeline for frontend work. Classifies intent and delegates to sub-agents. Never writes code directly. |
| `resume-builder` | `kiro --agent resume-builder` | Paste a JD → get tailored resume + cover letter (docx). Delegates to content-writer sub-agent. |
| `work-summary` | `kiro --agent work-summary` | Daily work summary tracker. Scans git repos, AI sessions, browser activity, and communication tools. |

### Sub-Agents (invoked by orchestrators, not directly)

| Agent | Invoked By | Purpose |
|-------|-----------|---------|
| `react-architecture` | react-orchestrator | Component decomposition, server/client boundaries, data flow decisions |
| `react-scaffold` | react-orchestrator | Generate component files, stories, tests, barrel exports |
| `react-styling` | react-orchestrator | Tailwind CSS, shadcn/ui composition, responsive design, accessibility |
| `react-testing` | react-orchestrator | Vitest unit tests, Playwright e2e, Storybook stories |

---

## Skills

Skills are directory-based capabilities loaded into agent context when triggered by user intent. Each skill directory contains a `SKILL.md` with YAML frontmatter and optionally `references/`, `scripts/`, `hooks/`, and `assets/` subdirectories.

### Development & Workflow Skills

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `design` | "Design this" / "Plan a feature" | Interactive planning: clarify problem → research → produce plan.md + tasks.md |
| `diagnose` | "Debug this" / "Triage the issue" | Test-first debugging for `.kiro/issues/` reports |
| `execute` | "Execute the plan" / "Build this" | Runs active plan task groups via subagent delegation (coder, ops, reviewer, docs) |
| `documentation` | "Write docs" / "Update README" | Technical documentation: READMEs, API docs, runbooks, ADRs |
| `diagram-spec` | "Create a diagram" | Mermaid diagram authoring (architecture-beta, flowchart, erDiagram, stateDiagram-v2, sequenceDiagram, journey, eventmodeling, ishikawa-beta) |
| `git-workflow` | "Create a branch" / "Prepare PR" | Git operations: branching, conventional commits, squash+rebase, hotfix, submodules |
| `harvest-debt` | "Harvest debt" / "Audit shortcuts" | Collects `SHORTCUT:` markers across codebase into docs/debt.md ledger |
| `flywheel` | "Run the flywheel" / "Improve config" | Analyzes session transcripts for user-correction patterns → proposes config improvements |

### Resume Skills

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `resume-content-writer` | "Build a resume for this JD" | Tailored resume bullets, cover letters, and scoring from a job description. Reads experience data, produces docx output. |

---

## Hooks

Hooks are JSON-defined guards that run before or after tool calls to enforce security and operational policies.

| Hook | Trigger | What it does |
|------|---------|--------------|
| `01-check-secrets` | PreToolUse (writes) | Blocks writes containing credential-shaped strings (AWS keys, tokens, private keys) |
| `02-guard-secret-reads` | PreToolUse (reads) | Guards reads of `.env`, credentials, and private key files |
| `03-guard-config-writes` | PreToolUse (writes) | Guards writes to sensitive configuration files |
| `10-validate-environment` | PreToolUse | Validates environment prerequisites before operations |
| `20-git-context` | PreToolUse | Injects git context (branch, status) into prompts |
| `50-rtk-compress` | PreToolUse | Compresses RTK context for efficiency |

---

## MCP Servers

MCP (Model Context Protocol) tools give agents structured access to external systems.

| Server | Tools Provided | Purpose |
|--------|---------------|---------|
| **git** (`servers/git.ts`) | `git_status` | Parsed git status: staged, unstaged, and untracked files as structured data |
| **io** (`servers/io.ts`) | `read_json`, `write_json` | Read/validate JSON files, write JSON with configurable formatting |
| **jira** (`servers/jira.ts`) | `jira_list_projects`, `jira_search_issues`, `jira_get_issue`, `jira_create_issue`, `jira_create_issues_bulk`, `jira_list_sprints`, `jira_get_sprint_metrics`, `jira_create_sprint`, `jira_create_link`, `jira_transition_issue`, `jira_add_comment` | Jira Cloud REST API: issue CRUD, sprint management, metrics extraction, dependency linking |
| **linear** (`servers/linear.ts`) | `linear_list_teams`, `linear_list_issues`, `linear_get_issue`, `linear_create_issue`, `linear_create_issues_bulk`, `linear_list_projects`, `linear_create_project`, `linear_list_cycles`, `linear_get_cycle_metrics`, `linear_create_cycle`, `linear_create_document`, `linear_create_relation` | Linear GraphQL API: issue CRUD, project/cycle management, metrics, documents, relations |
| **postgres** (`servers/postgres.ts`) | `postgres_query`, `postgres_seed` | Parameterized read-only queries; run SQL seed files against local dev DB |
| **rag** (`servers/rag.ts`) | `rag_search`, `rag_status` | Triple-vector semantic search over steering/knowledge documents (folder 30% + heading hierarchy 30% + content 40%). Session-aware deduplication. |
| **prometheus** (`servers/prometheus.ts`) | `prometheus_query`, `prometheus_range_query`, `prometheus_metrics`, `prometheus_label_values`, `prometheus_alerts`, `prometheus_rules`, `prometheus_kiro_usage`, `prometheus_kiro_performance`, `prometheus_kiro_models`, `prometheus_kiro_context`, `prometheus_kiro_security`, `prometheus_error_rates`, `prometheus_release_compare` | Prometheus PromQL queries, metric discovery, alerting status, Kiro feature/model/context/security telemetry |
| **jaeger** (`servers/jaeger.ts`) | `jaeger_services`, `jaeger_operations`, `jaeger_search_traces`, `jaeger_get_trace`, `jaeger_dependencies`, `jaeger_analyze_bottlenecks`, `jaeger_kiro_slow_sessions`, `jaeger_kiro_by_command`, `jaeger_kiro_by_model`, `jaeger_kiro_security_traces`, `jaeger_kiro_session_trace` | Jaeger distributed tracing: trace search, bottleneck analysis, Kiro session/model/security trace queries |
| **grafana** (`servers/grafana.ts`) | `grafana_search_dashboards`, `grafana_get_dashboard`, `grafana_dashboard_versions`, `grafana_query`, `grafana_datasources`, `grafana_annotations`, `grafana_create_annotation`, `grafana_release_report`, `grafana_kiro_report`, `grafana_top10_report`, `grafana_create_ticket_from_telemetry`, `grafana_trigger_self_healing`, `grafana_kiro_failure_report` | Grafana dashboards, release comparison reports, Kiro telemetry reports, automatic ticket generation from alerts, self-healing triggers with audit trail |
| **work-summary** (`servers/work-summary.ts`) | `work_summary_generate`, `work_summary_config`, `work_summary_status` | Daily work summary generation (git + AI sessions + browser + comms), configuration management, collector status |

### Environment Variables

#### MCP Servers

| Server | Required Variables | Where to Get |
|--------|-------------------|--------------|
| **jira** | `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` | [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |
| **linear** | `LINEAR_API_KEY` | [Linear Settings → API](https://linear.app/settings/api) |
| **postgres** | `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` | Standard [libpq env vars](https://www.postgresql.org/docs/current/libpq-envars.html). Defaults to local socket if unset. |
| **prometheus** | `PROMETHEUS_URL`, `PROMETHEUS_AUTH_TOKEN` (optional) | Your Prometheus instance URL (e.g., `http://localhost:9090`). Auth token only needed for secured instances. |
| **jaeger** | `JAEGER_URL`, `JAEGER_AUTH_TOKEN` (optional) | Your Jaeger Query UI URL (e.g., `http://localhost:16686`). Auth token only needed for secured instances. |
| **grafana** | `GRAFANA_URL`, `GRAFANA_API_KEY`, `GRAFANA_ORG_ID` (optional) | [Grafana Service Account tokens](https://grafana.com/docs/grafana/latest/administration/service-accounts/). Org ID only for multi-org setups. |

#### Git Workflow Scripts

| Variable | Required | Purpose |
|----------|----------|---------|
| `TICKET_SYSTEM_URL` | Optional | Enables ticket ID enforcement in branches/commits/PRs. Set to your project management URL (e.g., `https://mycompany.atlassian.net`). Without it, branches don't require ticket prefixes. |

#### Example `.zshrc` / `.bashrc` Configuration

```bash
# MCP: Jira (required for sdlc-tool-jira)
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_EMAIL="you@company.com"
export JIRA_API_TOKEN="your-api-token"

# MCP: Linear (required for sdlc-tool-linear)
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxx"

# MCP: Postgres (required for postgres_query/postgres_seed tools)
export PGHOST="localhost"
export PGPORT="5432"
export PGUSER="postgres"
export PGPASSWORD="postgres"
export PGDATABASE="postgres"

# Git workflow scripts (optional — enables ticket enforcement)
export TICKET_SYSTEM_URL="https://yourcompany.atlassian.net"

# MCP: Prometheus (required for prometheus_query/prometheus_kiro_* tools)
export PROMETHEUS_URL="http://localhost:9090"
export PROMETHEUS_AUTH_TOKEN=""  # optional — only for secured instances

# MCP: Jaeger (required for jaeger_search_traces/jaeger_kiro_* tools)
export JAEGER_URL="http://localhost:16686"
export JAEGER_AUTH_TOKEN=""  # optional — only for secured instances

# MCP: Grafana (required for grafana_query/grafana_kiro_report/grafana_top10_report tools)
export GRAFANA_URL="http://localhost:3000"
export GRAFANA_API_KEY="glsa_xxxxxxxxxxxx"
export GRAFANA_ORG_ID=""  # optional — only for multi-org setups
```

For secrets management in teams, use [Infisical](https://infisical.com), Vault, or dotenv files (gitignored). Never commit these values.

### Running MCP servers

Servers are TypeScript files executed via `npx tsx`. They're declared in agent configs:

```jsonc
"mcpServers": {
  "git": {
    "command": "npx",
    "args": ["tsx", "~/workspace/ai/mcp/mcp-scripts/servers/git.ts"],
    "timeout": 30000
  }
}
```

Agents reference tools as `@git/git_status`, `@io/read_json`, `@postgres/postgres_query`.

### Testing MCP scripts

```bash
cd mcp/mcp-scripts
npm test               # Vitest for TypeScript tools
uv run pytest          # pytest for Python tools (postgres)
```

---

## Steering (Context Documents)

Steering docs are loaded into agent context at startup. They define how the agent should behave prescriptively.

### Top-Level Rules

| File | What it defines |
|------|----------------|
| `DOTNET-EntityFrameworkQueries.md` | EF Core query guardrails, CQRS patterns, bulk mutation thresholds, encryption handling, anti-pattern detection |

### React Hooks & Patterns

| File | What it defines |
|------|----------------|
| `react/dependency-graph.md` | Stack choices: shadcn, Zustand, TanStack Query, RHF+Zod, AG Grid, Recharts |
| `react/custom-hooks.md` | Custom hook extraction patterns |
| `react/tanstack-query-hooks.md` | TanStack Query hook patterns |
| `react/react-router-hooks.md` | React Router v6+ hook patterns |
| `react/use-*.md` (14 files) | Every React hook with when/how/anti-patterns |

### Next.js

| File | What it defines |
|------|----------------|
| `nextjs/overview.md` | What Next.js replaces vs keeps from React stack |
| `nextjs/app-router.md` | File-based routing, layouts, parallel routes |
| `nextjs/server-components.md` | RSC vs client component decisions |
| `nextjs/data-patterns.md` | ISR, server actions, route handlers |
| `nextjs/middleware.md` | Auth, redirects, A/B testing at the edge |

### Security

| File | What it defines |
|------|----------------|
| `security/policies.md` | OAuth2 + PKCE, RBAC middleware, input validation (Zod at boundary), CORS (per-origin, never wildcard), secrets management, security headers, rate limiting, container hardening |

---

## Knowledge (Reference Documents)

Deep-reference documents indexed for semantic search via the RAG MCP server. Not loaded into agent context directly — queried on demand.

| Directory | Coverage |
|-----------|----------|
| `csharp/` | .NET architecture cheatsheet (CQRS, DDD, resilience, clean arch), EF Core query patterns & anti-patterns, Dapper anti-patterns |
| `mssql/` | SQL Server comprehensive patterns (indexing, APPLY vs JOIN, window functions, CTEs, execution plans), query performance decision hierarchies & DMV diagnostics |
| `nextjs/` | Next.js data patterns and middleware reference |

---

## Templates

Stub files in `templates/sdlc/` are copied into projects by SDLC skills. They're never loaded into agent context directly.

| Template | Purpose |
|----------|---------|
| `preferred-stack.md` | Baseline team technology preferences |
| `scope-profile.md` | Project dimensions for stack evaluation |
| `high-level-architecture.md` | Technology-agnostic system diagram |
| `workflow-diagrams.md` | Data flow and interaction patterns |
| `gap-risk-assessment.md` | Risk matrix across all dimensions |
| `stack-debate.md` | Structured pros/cons for contested decisions |
| `design-architecture.md` | Final design document with selected stack |
| `epics.json` | Epic/story/task JSON schema with foundation epic |
| `epic-document.md` | Human-readable epic document |
| `sprint-plan.md` | Sprint capacity and dependency tracking |

---

## Usage

### Linking to a project

Kiro CLI looks for `.kiro/` at the project root. Use `link.sh` to create symlinks:

```bash
~/workspace/ai/link.sh /path/to/project    # creates /path/to/project/.kiro/
~/workspace/ai/link.sh                      # defaults to ~/.kiro/
```

Changes to any file here are reflected immediately in all linked projects.

### Selecting an agent

```bash
kiro --agent dev                 # Full-stack, broad access
kiro --agent react-frontend      # React/Next.js scoped (no shell)
kiro --agent react-orchestrator  # Multi-agent frontend pipeline
kiro --agent resume-builder      # Tailored resume + cover letter from a JD
kiro --agent work-summary        # Daily work summary tracker
```

### Resume tooling setup

```bash
cd skills/resume-content-writer/scripts
./setup.sh
```

Creates experience.json, installs Python deps, generates docx templates.

### Git workflow setup

```bash
cd skills/git-workflow/scripts
./setup.sh
```

Installs commit-msg/pre-push hooks, enables `git rerere`, makes workflow scripts available:

```bash
uv run git-branch       # Create branch with naming convention
uv run git-commit       # Auto-group changes, commit per type
uv run git-prepare-pr   # Squash + rewrite + rebase for PR
uv run git-hotfix       # Hotfix workflow from prod
uv run git-merge-pr     # Validate and merge PR
uv run git-promote      # Manual environment promotion
```

Optional: `export TICKET_SYSTEM_URL="https://yourcompany.atlassian.net"` for ticket refs in branches/PRs.

---

## Agent Config Format

```jsonc
{
  "name": "agent-name",
  "description": "What this agent does",
  "model": "auto",
  "prompt": "System prompt text",
  "mcpServers": { /* server connections */ },
  "tools": ["@builtin"],
  "allowedTools": ["@builtin"],
  "permissions": {
    "rules": [
      { "capability": "shell", "match": ["git *"], "effect": "allow" }
    ]
  },
  "resources": [
    "skill://../skills/git-workflow/SKILL.md",  // On-demand (metadata only at startup)
    "file://package.json"                       // Always in context
  ]
}
```

### Resource URI types

- `skill://path` — on-demand skill (only description loaded at startup, full content on trigger)
- `file://path` — always loaded into context (keep small: package.json, tsconfig)

---

## Adapting to Other Tools

| This repo | Claude Code | GitHub Copilot | LangChain/LangGraph |
|-----------|-------------|----------------|---------------------|
| `steering/` | `.claude/instructions/` or `CLAUDE.md` | `.github/copilot-instructions.md` | System prompt context |
| `skills/` | Referenced files in `CLAUDE.md` | Inline in instructions | RAG documents or tool descriptions |
| `agents/` | Per-directory `CLAUDE.md` variants | Not supported | `Agent` class definitions |
| `hooks/` | `.claude/hooks/` | Not supported | Middleware / guardrails |
| `mcp/` | `.claude/mcp.json` | Copilot Extensions | `Tool` implementations |

---

## Principles

1. **Organization enables portability.** Clear directory structure maps to any tool's config format.
2. **Skills are self-contained directories.** Each skill bundles its SKILL.md, references, and scripts together.
3. **Hooks enforce invariants.** Security policies are enforced automatically, not by agent self-discipline.
4. **MCP scripts are testable.** Each tool script does one thing, has tests alongside it, and runs independently of any agent framework.
5. **Everything is version-controllable.** Human-readable text, clean diffs, standard PR workflow.
6. **Agents are composable.** Adding a new persona means writing one JSON file over shared steering and skills.
