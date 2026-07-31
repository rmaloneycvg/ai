# AI Workspace

Portable AI agent configurations, steering documents, skills, and MCP tooling. Designed for Kiro CLI but adaptable to any AI coding assistant.

## Structure

```
ai/
├── steering/                           # Behavioral guidance loaded into agent context
│   ├── orchestration/
│   │   ├── local-dev.md                # Tilt, nginx, Docker, k8s, Terraform patterns
│   │   ├── pipeline-contract.md        # Sub-agent pipeline I/O schema (input, output, retry, errors)
│   │   └── sdlc-pipeline.md           # SDLC phase ordering, gates, change control, rework paths
│   ├── conventions/
│   │   ├── code-style.md              # TypeScript naming, file org, imports
│   │   ├── documentation.md           # README structure, Mermaid templates, validation
│   │   ├── git-workflow.md            # Branching strategy, conventional commits, PR workflow
│   │   ├── release-gates.md           # Security, accessibility, data migration, parity gates
│   │   └── skill-schema.md            # Skill authoring patterns, quality checklist, refactoring ops
│   ├── security/
│   │   └── policies.md               # Auth, validation, CORS, secrets, headers
│   └── preferences/
│       ├── stack/
│       │   ├── react/
│       │   │   ├── dependency-graph.md    # React stack choices (shadcn, Zustand, TQ, etc.)
│       │   │   ├── custom-hooks.md        # Custom hook extraction patterns
│       │   │   ├── tanstack-query-hooks.md # TanStack Query hook patterns
│       │   │   ├── react-router-hooks.md  # React Router v6+ hook patterns
│       │   │   ├── use-callback.md        # useCallback steering
│       │   │   ├── use-context.md         # useContext vs Zustand decisions
│       │   │   ├── use-debug-value.md     # useDebugValue for custom hooks
│       │   │   ├── use-deferred-value.md  # useDeferredValue for expensive renders
│       │   │   ├── use-effect.md          # useEffect patterns and anti-patterns
│       │   │   ├── use-effect-event.md    # useEffectEvent (experimental)
│       │   │   ├── use-imperative-handle.md # useImperativeHandle for ref APIs
│       │   │   ├── use-layout-effect.md   # useLayoutEffect for DOM measurement
│       │   │   ├── use-memo.md            # useMemo steering
│       │   │   ├── use-optimistic.md      # useOptimistic for server actions
│       │   │   ├── use-reducer.md         # useReducer state machine patterns
│       │   │   ├── use-ref.md             # useRef patterns and pitfalls
│       │   │   ├── use-sync-external-store.md # useSyncExternalStore for browser APIs
│       │   │   └── use-transition.md      # useTransition for non-blocking updates
│       │   ├── nextjs/
│       │   │   ├── overview.md            # What Next.js replaces vs keeps from React stack
│       │   │   ├── app-router.md          # File-based routing, layouts, parallel routes
│       │   │   ├── server-components.md   # RSC vs client component decisions
│       │   │   ├── data-patterns.md       # ISR, server actions, route handlers
│       │   │   └── middleware.md          # Auth, redirects, A/B testing at the edge
│       │   ├── node/
│       │   │   └── api-caching.md         # Layered caching (HTTP, Redis, in-memory)
│       │   └── csharp/
│       │       └── api-caching.md         # Response/output cache, IDistributedCache
│       └── resume/
│           └── guardrails.md              # Resume/cover letter generation guardrails
├── skills/                             # On-demand capability files (YAML frontmatter)
│   ├── backend-cron-feature.md         # Cron job / scheduled task setup
│   ├── backend-rest-api-feature.md     # REST API endpoint scaffolding
│   ├── codility-prep.md               # Coding interview preparation
│   ├── general-debug.md               # Debugging workflow
│   ├── general-deploy.md              # Deployment workflow
│   ├── general-documentation.md       # README generation and maintenance
│   ├── general-refactor.md            # General code refactoring
│   ├── general-test.md                # Test writing workflow
│   ├── git-workflow.md                 # Git branching, conventional commits, PR prep, hotfix
│   ├── kiro-create-agent.md           # Standard agent config creation
│   ├── kiro-create-orchestration.md   # Orchestrator + sub-agent pipeline creation
│   ├── kiro-create-skill.md           # Skill authoring workflow
│   ├── kiro-refactor-agent.md         # Standard agent config editing
│   ├── kiro-refactor-orchestration.md # Orchestration pipeline editing
│   ├── kiro-refactor-skill.md         # Skill refactoring operations
│   ├── kiro-workflow-guidelines.md    # AI workspace architecture rules
│   ├── react-architecture.md          # Pipeline: UI architecture decisions
│   ├── react-components.md            # React component generation
│   ├── react-hooks-optimization.md    # Audit React hooks, extract custom hooks
│   ├── react-refactor.md              # Pipeline: code refactoring
│   ├── react-scaffold.md              # Pipeline: component scaffolding
│   ├── react-styling.md               # Pipeline: Tailwind/shadcn styling
│   ├── react-testing.md               # Pipeline: tests and stories
│   ├── resume-builder.md              # Resume/cover letter generation orchestrator
│   ├── resume-content-writer.md       # Sub-agent: high-reasoning content generation
│   ├── resume-experience-parser.md    # Extract experience from .docx files
│   ├── resume-job-scorer.md           # Score resume against job description
│   ├── sdlc-detailed-design.md       # SDLC design: workflows, ERDs, data flows, cloud architecture
│   ├── sdlc-epic-planning.md         # Epic/story/task decomposition with dependencies
│   ├── sdlc-manager-1on1.md         # Personal 1:1 prep, win tracking, goals, review narratives
│   ├── sdlc-meeting-debrief.md      # Post-meeting: store notes/transcripts, extract actions, route items
│   ├── sdlc-meeting-prep.md          # Meeting preparation, scheduling, and "what's next" guidance
│   ├── sdlc-people-management.md     # Coaching, improvement plans, escalation, promotion cases
│   ├── sdlc-performance-log.md     # Win logging, disagreement receipts, goals, review narrative
│   ├── sdlc-planning.md              # SDLC planning phase: debates, artifacts, meetings
│   ├── sdlc-release-planning.md      # Release criteria, rollback, monitoring, staged rollout
│   ├── sdlc-sprint-planning.md       # Sprint capacity, dependency tracking, timeline reports
│   ├── sdlc-stack-selection.md       # SDLC design: stack evaluation, gap analysis, architecture docs
│   ├── sdlc-team-metrics.md          # Sprint KPIs, thresholds, retro prep, estimate calibration
│   ├── sdlc-tool-jira.md             # Jira-specific field mapping and import guidance
│   └── sdlc-tool-linear.md           # Linear-specific field mapping and import guidance
├── agents/                             # Agent persona configs (JSON)
│   ├── general-dev.json                # Full-stack: all steering, broad tool access
│   ├── infra-dev.json                  # Infrastructure/DevOps focused
│   ├── react-architecture.json         # Sub-agent: UI architecture decisions (opus)
│   ├── react-frontend.json             # React/Next.js only, no shell/db access
│   ├── react-orchestrator.json         # Orchestrator: routes to sub-agents by task type
│   ├── react-refactor.json             # Sub-agent: code refactoring (opus)
│   ├── react-scaffold.json             # Sub-agent: component scaffolding (haiku)
│   ├── react-styling.json              # Sub-agent: Tailwind/shadcn styling (haiku)
│   ├── react-testing.json              # Sub-agent: tests and stories (sonnet)
│   ├── resume-builder.json             # Resume generation orchestrator
│   ├── resume-content-writer.json      # Sub-agent: high-reasoning content generation (opus)
│   ├── resume-experience-parser.json   # Extract experience from .docx resumes
│   ├── resume-job-scorer.json          # Score resume fit against a job description
│   └── sdlc-lead.json                  # SDLC planning, architecture, sprints, release, metrics
├── mcp/                                # MCP server definitions + tool scripts
│   └── mcp-scripts/
│       ├── servers/                    # MCP server entry points
│       │   ├── git.ts                 # git_status tool
│       │   ├── io.ts                  # read_json, write_json tools
│       │   ├── jira.ts               # Jira Cloud API (issues, sprints, metrics, links)
│       │   ├── linear.ts             # Linear GraphQL API (issues, cycles, projects, docs)
│       │   └── postgres.ts            # postgres_query, postgres_seed tools
│       ├── lib/
│       │   └── exec-python.ts         # Python execution helper
│       ├── git/status.ts              # Parsed git status implementation
│       ├── io/
│       │   ├── read-json.ts           # Read and validate JSON files
│       │   └── write-json.ts          # Write JSON with formatting
│       ├── jira/
│       │   ├── client.ts             # Jira REST API v3 client (auth, fetch wrapper)
│       │   ├── queries.ts            # Search, sprints, boards, sprint metrics
│       │   └── mutations.ts          # Create issues, sprints, links, transitions, comments
│       ├── linear/
│       │   ├── client.ts             # Linear GraphQL client (auth, query wrapper)
│       │   ├── queries.ts            # Teams, issues, projects, cycles, cycle metrics
│       │   └── mutations.ts          # Create issues, projects, cycles, documents, relations
│       └── postgres/
│           ├── query.py               # Parameterized read-only queries
│           └── seed.py                # Run SQL seed files
├── scripts/                            # Executable scripts used by agents
│   ├── git/
│   │   ├── setup.sh                  # Install hooks, validate env, configure workflow
│   │   ├── pyproject.toml            # Python dependencies (managed by uv)
│   │   ├── src/                      # CLI scripts + shared library
│   │   │   ├── branch.py            # Create branch with naming convention
│   │   │   ├── commit.py            # Auto-group changes, commit per type
│   │   │   ├── prepare_pr.py        # Squash + rewrite + rebase for PR
│   │   │   ├── merge_pr.py          # Final validation + merge
│   │   │   ├── hotfix.py            # Hotfix workflow from prod
│   │   │   ├── promote.py           # Manual environment promotion
│   │   │   └── lib/                  # Shared library (conventional, detect_changes, git_ops, ticket)
│   │   ├── hooks/                    # Git hook shell shims (commit-msg, pre-push)
│   │   └── tests/                    # pytest unit + integration tests
│   └── resume/
│       ├── generate_docx.py           # Generate ATS-optimized resume/cover letter docx (Lato, royal blue)
│       ├── parse_resumes.py           # Extract structured text from .docx files
│       ├── create_templates.py        # Generate docx templates with named styles
│       ├── requirements.txt           # Python dependencies (python-docx)
│       └── setup.sh                   # Initialize config (experience.json, venv, templates)
├── config/                             # Per-user configuration (personal data gitignored)
│   └── resume/
│       ├── experience.schema.json     # Schema for experience data (tracked)
│       ├── experience.json            # Personal experience data (gitignored, created by setup.sh)
│       └── templates/                 # Generated docx templates (gitignored)
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
| **Steering** | Prescriptive docs that shape agent behavior: technology choices, patterns, security rules, naming conventions | Loaded as always-in-context via `file://` URIs in agent configs |
| **Skills** | Condensed instruction sets with YAML frontmatter. Each skill is one focused capability | Loaded on-demand via `skill://` URIs — only metadata at startup, full content when triggered |
| **Agents** | JSON configs that compose a persona from steering + skills + tools | Selected with `kiro --agent <name>` — each restricts scope, tools, and file access |
| **MCP Scripts** | Small tool implementations (TypeScript/Python) invoked via Model Context Protocol | Declared in agent `mcpServers` — agents call them like functions |
| **Templates** | Stub markdown/JSON files copied into projects as starting points | Not loaded into context — used by SDLC skills to scaffold planning docs |

---

## Agents

Each agent is a focused persona with specific tool access, steering context, and file write restrictions.

### Primary Agents (user-facing)

| Agent | Command | Purpose | Tools |
|-------|---------|---------|-------|
| `general-dev` | `kiro --agent dev` | Full-stack development. Broad access, asks before destructive ops. Suggests specialized agents when relevant. | read, write, shell, glob, grep, code, git, io |
| `react-frontend` | `kiro --agent react-frontend` | React/Next.js development. No shell or database access. Writes restricted to `src/`. | read, write, glob, grep, code |
| `infra-dev` | `kiro --agent infra` | Terraform, Docker, Kubernetes, Tilt, nginx. Shell access for infra commands. Writes restricted to infra files. | read, write, shell, glob, grep, git, io, postgres |
| `react-orchestrator` | `kiro --agent react-orchestrator` | Multi-agent pipeline for frontend work. Classifies intent and delegates to sub-agents (architecture → scaffold → styling → testing). Never writes code directly. | read, glob, grep, code, subagent |
| `resume-builder` | `kiro --agent resume-builder` | Paste a JD → get tailored resume + cover letter (docx + pdf). Reads from experience.json. Delegates to content-writer sub-agent for high-reasoning work. | read, write, shell, glob, grep, subagent |
| `resume-experience-parser` | `kiro --agent experience-parser` | Extract structured experience data from .docx resume files into experience.json format. | read, write, shell, glob, grep |
| `resume-job-scorer` | `kiro --agent job-scorer` | Score a resume against a job description. Reports keyword match, gap analysis, and improvement suggestions. | read, glob, grep, io |
| `sdlc-lead` | `kiro --agent sdlc-lead` | Full SDLC lifecycle: planning → stack selection → design → epics → sprints → release. Also handles metrics, people management, and meeting prep. Writes to `drafts/` and `docs/`. | read, write, glob, grep, code, git, io |

### Sub-Agents (invoked by orchestrators, not directly)

| Agent | Model | Invoked By | Purpose |
|-------|-------|-----------|---------|
| `react-architecture` | opus | react-orchestrator | Component decomposition, server/client boundaries, data flow decisions |
| `react-scaffold` | haiku | react-orchestrator | Generate component files, stories, tests, barrel exports |
| `react-styling` | haiku | react-orchestrator | Tailwind CSS, shadcn/ui composition, responsive design, accessibility |
| `react-testing` | sonnet | react-orchestrator | Vitest unit tests, Playwright e2e, Storybook stories |
| `react-refactor` | opus | react-orchestrator | Extract components/hooks, migrate state, performance optimization |
| `resume-content-writer` | opus | resume-builder | High-reasoning content generation: headline crafting, bullet rewriting, cover letter writing, self-scoring |

---

## Skills

Skills are on-demand capabilities loaded into agent context when triggered by user intent.

### Development Skills

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `backend-rest-api-feature` | "Add an API endpoint" | Scaffolds Express route + Zod validation + handler + integration test |
| `backend-cron-feature` | "Add a cron job" | Creates scheduled task with Dockerfile, k8s CronJob, Tiltfile entry |
| `react-components` | "Create a component" | Generates component + types + story + test following stack conventions |
| `react-hooks-optimization` | "Audit hooks" / "extract a hook" | Reviews hook usage, extracts custom hooks, applies optimization patterns |
| `react-architecture` | "How should I structure this?" | Component decomposition, server/client split, state management decisions |
| `react-scaffold` | "Scaffold a new page/feature" | Pipeline stage: file generation from architecture decisions |
| `react-styling` | "Style this component" | Pipeline stage: Tailwind/shadcn application with responsive + a11y |
| `react-testing` | "Write tests for X" | Pipeline stage: Vitest + Playwright + Storybook story creation |
| `react-refactor` | "Refactor this" / "extract" | Pipeline stage: component/hook extraction, state migration |
| `codility-prep` | "Prepare for coding interview" | Structured practice: problem analysis, optimal solution, edge cases, complexity |

### General Workflows

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `general-debug` | "Debug this" / "why is this failing" | Systematic debugging: reproduce → isolate → diagnose → fix → verify |
| `general-deploy` | "Deploy this" | Deployment checklist: env validation → build → deploy → smoke test |
| `general-documentation` | "Update the README" | README generation following documentation conventions with Mermaid diagrams |
| `general-refactor` | "Refactor this code" | Code restructuring: identify smell → spec change → implement → verify |
| `general-test` | "Write tests" | Test creation: coverage analysis → write tests → verify passing |
| `git-workflow` | "Create a branch" / "prepare PR" | Git operations: branching, conventional commits, squash+rebase, hotfix |

### SDLC Skills

| Skill | Phase | What it does |
|-------|-------|--------------|
| `sdlc-planning` | 1 | Facilitates planning debates, generates charter, stakeholder analysis |
| `sdlc-stack-selection` | 2 | Technology evaluation: gap analysis, risk matrix, debate format, architecture doc |
| `sdlc-detailed-design` | 3 | Workflow diagrams, ERDs, data flows, cloud architecture, API contracts |
| `sdlc-epic-planning` | 4 | Decomposes features into epics → stories → tasks with dependencies |
| `sdlc-sprint-planning` | 5 | Capacity allocation, dependency tracking, timeline, risk identification |
| `sdlc-release-planning` | 7 | Release criteria, rollback plan, monitoring, staged rollout gates |
| `sdlc-team-metrics` | Any | Sprint KPIs, velocity tracking, retro prep, estimate calibration |
| `sdlc-people-management` | Any | Coaching, improvement plans, escalation paths, promotion case building |
| `sdlc-meeting-prep` | Any | Meeting preparation: agenda, context gathering, scheduling, "what's next" |
| `sdlc-meeting-debrief` | Any | Post-meeting: store notes, extract action items, route to owners |
| `sdlc-manager-1on1` | Any | Personal 1:1 prep: win tracking, goals, talking points, review narratives |
| `sdlc-performance-log` | Any | Win logging, disagreement receipts, goal tracking, review narrative generation |
| `sdlc-tool-linear` | After Phase 4 | Export epics/stories to Linear with field mapping |
| `sdlc-tool-jira` | After Phase 4 | Export epics/stories to Jira with field mapping |

### Resume Skills

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `resume-builder` | "Build a resume for this JD" | Orchestrates: JD parsing → content generation → docx creation → PDF conversion |
| `resume-content-writer` | (sub-agent) | High-reasoning: headline, bullet selection/rewriting, cover letter, scoring |
| `resume-experience-parser` | "Parse my resume" | Extracts structured data from .docx files into experience.json format |
| `resume-job-scorer` | "Score this resume" | Keyword analysis, gap detection, match percentage, improvement suggestions |

### Kiro Meta-Skills (workspace management)

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `kiro-create-skill` | "Create a new skill" | Authors a skill file following the skill-schema conventions |
| `kiro-refactor-skill` | "Refactor this skill" | Narrow triggers, split oversized skills, merge overlaps, add missing schema elements |
| `kiro-create-agent` | "Create a new agent" | Scaffolds agent JSON with steering, skills, tools, and restrictions |
| `kiro-refactor-agent` | "Edit this agent" | Updates agent config: add/remove skills, change tool access, update prompt |
| `kiro-create-orchestration` | "Create a pipeline" | Builds orchestrator + sub-agent pipeline with pipeline-contract compliance |
| `kiro-refactor-orchestration` | "Edit this pipeline" | Modifies orchestration: add/remove stages, change routing, update models |
| `kiro-workflow-guidelines` | "How does this workspace work?" | Explains architecture rules: steering vs skills, when to split, overlap detection |

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

### Environment Variables

| Server | Required Variables | Where to Get |
|--------|-------------------|--------------|
| **jira** | `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` | [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |
| **linear** | `LINEAR_API_KEY` | [Linear Settings → API](https://linear.app/settings/api) |
| **postgres** | `DATABASE_URL` or defaults to local | Local dev postgres |

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

### Orchestration

| File | What it defines |
|------|----------------|
| `local-dev.md` | Tilt topology, nginx gateway patterns, Docker multi-stage builds, k8s manifests, Terraform conventions, OAuth2 flow |
| `pipeline-contract.md` | Sub-agent I/O JSON schema: input format, output format, error schema, retry context, escalation rules |
| `sdlc-pipeline.md` | SDLC phase ordering, gate requirements, skip prevention rules, rework paths |

### Conventions

| File | What it defines |
|------|----------------|
| `code-style.md` | TypeScript naming (PascalCase components, camelCase functions, kebab-case files), import ordering, component patterns |
| `documentation.md` | README structure, Mermaid diagram templates (flowchart, sequence, state, ER, class), staleness detection |
| `git-workflow.md` | Branching model (prod ← staging ← dev ← feature), conventional commits, PR workflow, hotfix flow, CI auto-promotion |
| `release-gates.md` | Security, accessibility, data migration, environment parity, and operational readiness checklists |
| `skill-schema.md` | Skill file structure, quality checklist, idempotent scope principle, overlap detection, refactoring operations |

### Security

| File | What it defines |
|------|----------------|
| `policies.md` | OAuth2 + PKCE, RBAC middleware, input validation (Zod at boundary), CORS (per-origin, never wildcard), secrets management, security headers, rate limiting, container hardening |

### Stack Preferences

| Directory | Coverage |
|-----------|----------|
| `react/` | Dependency graph (shadcn, Zustand, TanStack Query, RHF+Zod, AG Grid, Recharts), every React hook with when/how/anti-patterns, custom hook extraction |
| `nextjs/` | App Router (file-based routing, layouts, parallel routes), Server Components vs Client, data patterns (ISR, Server Actions, Route Handlers), middleware (auth, geo, A/B) |
| `node/` | Layered API caching: HTTP headers → nginx proxy_cache → Redis → in-memory LRU → request dedup → stampede prevention |
| `csharp/` | Response caching, output caching (.NET 7+), IDistributedCache (Redis), IMemoryCache, stampede prevention with SemaphoreSlim |
| `resume/` | ATS formatting rules, section order, keyword optimization, cover letter structure, truthfulness constraints, voice/personality |

---

## Templates

Stub files in `templates/sdlc/` are copied into projects by SDLC skills. They're never loaded into agent context directly.

| Template | Used by | Purpose |
|----------|---------|---------|
| `preferred-stack.md` | sdlc-stack-selection | Baseline team technology preferences |
| `scope-profile.md` | sdlc-stack-selection | Project dimensions for stack evaluation |
| `high-level-architecture.md` | sdlc-detailed-design | Technology-agnostic system diagram |
| `workflow-diagrams.md` | sdlc-detailed-design | Data flow and interaction patterns |
| `gap-risk-assessment.md` | sdlc-stack-selection | Risk matrix across all dimensions |
| `stack-debate.md` | sdlc-stack-selection | Structured pros/cons for contested decisions |
| `design-architecture.md` | sdlc-detailed-design | Final design document with selected stack |
| `epics.json` | sdlc-epic-planning | Epic/story/task JSON schema with foundation epic |
| `epic-document.md` | sdlc-epic-planning | Human-readable epic document |
| `sprint-plan.md` | sdlc-sprint-planning | Sprint capacity and dependency tracking |

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
kiro --agent infra               # Terraform, Docker, k8s, Tilt
kiro --agent react-orchestrator  # Multi-agent frontend pipeline
kiro --agent resume-builder      # Tailored resume + cover letter from a JD
kiro --agent experience-parser   # Extract experience from .docx resumes
kiro --agent job-scorer          # Score resume against a job description
kiro --agent sdlc-lead           # Full SDLC lifecycle management
```

### Resume tooling setup

```bash
./scripts/resume/setup.sh
```

Creates `config/resume/experience.json` (gitignored), installs Python deps, generates docx templates.

### Git workflow setup

```bash
./scripts/git/setup.sh
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
  "prompt": "System prompt text",
  "mcpServers": { /* server connections */ },
  "tools": [ /* available tools */ ],
  "allowedTools": [ /* auto-approved subset */ ],
  "toolsSettings": { /* per-tool restrictions (allowed paths, commands) */ },
  "resources": [
    "skill://../skills/react-components.md",  // On-demand (metadata only at startup)
    "file://package.json"                     // Always in context
  ],
  "hooks": {
    "agentSpawn": [ /* commands run when agent starts */ ]
  }
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
| `mcp/` | `.claude/mcp.json` | Copilot Extensions | `Tool` implementations |

---

## Principles

1. **Organization enables portability.** Clear directory structure maps to any tool's config format.
2. **Skills are condensed; steering has depth.** Skills stay compact for context windows. They reference steering when detail is needed.
3. **MCP scripts are testable.** Each tool script does one thing, has tests alongside it, and runs independently of any agent framework.
4. **Everything is version-controllable.** Human-readable text, clean diffs, standard PR workflow.
5. **Agents are composable.** Adding a new persona means writing one JSON file over shared steering and skills.
