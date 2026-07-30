# AI Workspace

Portable AI agent configurations, steering documents, skills, and MCP tooling. Designed for Kiro CLI but adaptable to any AI coding assistant.

## Structure

```
ai/
├── steering/                           # Behavioral guidance loaded into agent context
│   ├── orchestration/
│   │   └── local.md                    # Tilt, nginx, Docker, k8s, Terraform patterns
│   ├── conventions/
│   │   ├── code-style.md              # TypeScript naming, file org, imports
│   │   ├── documentation.md           # README structure, Mermaid templates, validation
│   │   ├── react-pipeline-contract.md  # React/Next.js sub-agent pipeline I/O schema
│   │   ├── git-workflow.md            # Branching strategy, conventional commits, PR workflow
│   │   └── skill-schema.md            # Skill authoring patterns, quality checklist, refactoring ops
│   ├── security/
│   │   └── policies.md               # Auth, validation, CORS, secrets, headers
│   └── preferences/stack/
│       ├── react/
│       │   └── dependency-graph.md    # React stack choices (shadcn, Zustand, TQ, etc.)
│       ├── nextjs/
│       │   ├── overview.md            # What Next.js replaces vs keeps from React stack
│       │   ├── app-router.md          # File-based routing, layouts, parallel routes
│       │   ├── server-components.md   # RSC vs client component decisions
│       │   ├── data-patterns.md       # ISR, server actions, route handlers
│       │   └── middleware.md          # Auth, redirects, A/B testing at the edge
│       ├── node/
│       │   └── api-caching.md         # Layered caching (HTTP, Redis, in-memory)
│       ├── csharp/
│       │   └── api-caching.md         # Response/output cache, IDistributedCache
│       └── resume/
│           └── guardrails.md          # Resume/cover letter generation guardrails
├── skills/                             # On-demand capability files (YAML frontmatter)
│   ├── react-components.md
│   ├── backend-rest-api-feature.md
│   ├── backend-cron-feature.md
│   ├── project-readme-documentation.md
│   ├── create-kiro-skill.md
│   ├── refactor-kiro-skill.md
│   ├── refactor.md
│   ├── debug.md
│   ├── test.md
│   ├── deploy.md
│   ├── git-workflow.md                 # Git branching, conventional commits, PR prep, hotfix
│   ├── react-scaffold.md                # Pipeline: component scaffolding
│   ├── react-architecture.md            # Pipeline: UI architecture decisions
│   ├── react-styling.md                 # Pipeline: Tailwind/shadcn styling
│   ├── react-testing.md                 # Pipeline: tests and stories
│   ├── react-refactor.md                # Pipeline: code refactoring
│   ├── react-hooks-optimization.md      # Audit React hooks, extract custom hooks
│   ├── resume-builder.md               # Resume/cover letter generation workflow
│   ├── resume-content-writer.md        # Sub-agent: high-reasoning content generation
│   ├── experience-parser.md            # Extract experience from .docx files
│   └── job-scorer.md                   # Score resume against job description
├── agents/                             # Agent persona configs (JSON)
│   ├── dev.json                        # Full-stack: all steering, broad tool access
│   ├── react-frontend.json              # React/Next.js only, no shell/db access
│   ├── react-frontend-orchestrator.json # Orchestrator: routes to sub-agents by task type
│   ├── react-scaffold.json              # Sub-agent: component scaffolding (haiku)
│   ├── react-architecture.json          # Sub-agent: UI architecture decisions (opus)
│   ├── react-styling.json               # Sub-agent: Tailwind/shadcn styling (haiku)
│   ├── react-testing.json               # Sub-agent: tests and stories (sonnet)
│   ├── react-refactor.json              # Sub-agent: code refactoring (opus)
│   ├── infra.json                      # Infrastructure/DevOps focused
│   ├── resume-builder.json             # Resume generation orchestrator
│   ├── resume-content-writer.json      # Sub-agent: high-reasoning content generation (opus)
│   ├── experience-parser.json          # Extract experience from .docx resumes
│   └── job-scorer.json                 # Score resume fit against a job description
├── mcp/                                # MCP server definitions + tool scripts
│   └── mcp-scripts/
│       ├── servers/                    # MCP server entry points (git, io, postgres)
│       │   ├── git.ts                 # git_status tool
│       │   ├── io.ts                  # read_json, write_json tools
│       │   └── postgres.ts            # postgres_query, postgres_seed tools
│       ├── git/status.ts               # Parsed git status
│       ├── io/read-json.ts             # Read and validate JSON files
│       ├── io/write-json.ts            # Write JSON with formatting
│       ├── postgres/query.py           # Parameterized read-only queries
│       └── postgres/seed.py            # Run SQL seed files
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
│       ├── generate_docx.py           # Generate ATS-optimized resume/cover letter docx
│       ├── parse_resumes.py           # Extract structured text from .docx files
│       ├── create_templates.py        # Generate docx templates with named styles
│       ├── pyproject.toml             # Python dependencies for resume scripts (managed by uv)
│       └── setup.sh                   # Initialize config (experience.json, venv, templates)
├── config/                             # Per-user configuration (personal data gitignored)
│   └── resume/
│       ├── experience.schema.json     # Schema for experience data (tracked)
│       ├── experience.json            # Personal experience data (gitignored, created by setup.sh)
│       └── templates/                 # Generated docx templates (gitignored)
├── setup.sh                            # Generate local .kiro/ with symlinks
├── link.sh                             # Create .kiro/ in another project with symlinks back
└── .gitignore
```

## Concepts

**Steering** — detailed, prescriptive documents that shape how an agent writes code. They define technology choices, architectural patterns, security requirements, and naming conventions. Loaded as context via `file://` URIs.

**Skills** — condensed instruction sets with YAML frontmatter. Each skill is a focused capability (scaffold a component, add an API endpoint, run a deploy). Skills reference steering docs for depth but stay compact for context efficiency.

**Agents** — JSON configs that compose a persona from steering + skills + tools. Each agent is a focused lens: the frontend agent loads React/Next.js steering and restricts file writes to `src/`; the infra agent loads orchestration/Terraform docs and gets shell access.

**MCP Scripts** — small, testable tool implementations (TypeScript and Python) that agents invoke via the Model Context Protocol. Each does one thing: query postgres, read a file, get git status.

## Usage

### In a project

Kiro CLI looks for `.kiro/` at the project root. Use the `link.sh` script to create one with symlinks back to this workspace:

```bash
~/workspace/ai/link.sh /path/to/project
```

This creates `/path/to/project/.kiro/` containing symlinks to `agents/`, `steering/`, and `skills/`. Changes to any file are reflected immediately in all linked projects — no syncing needed.

### Local setup (this repo as a project)

To use Kiro CLI directly in this workspace:

```bash
./setup.sh
```

Creates `.kiro/` with symlinks to the sibling directories. Gitignored.

### Resume tooling setup

If you plan to use the resume-builder, experience-parser, or job-scorer agents:

```bash
./scripts/resume/setup.sh
```

This creates `config/resume/experience.json` (from an existing file or a blank scaffold), installs Python dependencies, and generates docx templates. The experience.json file is gitignored — each user populates their own.

### Git workflow setup

To enforce conventional commits, branch naming, and the squash+rebase PR workflow:

```bash
./scripts/git/setup.sh
```

This installs commit-msg and pre-push git hooks, enables `git rerere` globally, and makes the workflow scripts available. The hooks validate commit message format and branch naming conventions. Available commands (from `scripts/git/`):

```bash
uv run git-branch       # Create branch with naming convention
uv run git-commit       # Auto-group changes, commit per type
uv run git-prepare-pr   # Squash + rewrite + rebase for PR
uv run git-hotfix       # Hotfix workflow from prod
uv run git-merge-pr     # Validate and merge PR
uv run git-promote      # Manual environment promotion
```

Optional: set `TICKET_SYSTEM_URL` in your shell profile to enable ticket references in branch names and PR titles:

```bash
export TICKET_SYSTEM_URL="https://yourcompany.atlassian.net"
```

### Selecting an agent

```bash
kiro --agent dev        # Full-stack, broad access
kiro --agent react-frontend   # React/Next.js scoped
kiro --agent infra      # Infrastructure/DevOps
kiro --agent react-frontend-orchestrator  # Multi-agent pipeline (delegates to sub-agents)
kiro --agent resume-builder         # Generate tailored resume + cover letter from a JD
kiro --agent experience-parser      # Extract experience data from .docx resumes
kiro --agent job-scorer             # Score resume fit against a job description
```

## Agent config format

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
    "skill://../skills/react-components.md",  // On-demand skill (metadata only at startup)
    "file://package.json"                     // Small project file (always in context)
  ],
  "hooks": {
    "agentSpawn": [ /* commands run when agent starts */ ]
  }
}
```

## Adapting to other tools

The directory structure maps directly to other AI assistants:

| This repo | Claude Code | GitHub Copilot | LangChain/LangGraph |
|-----------|-------------|----------------|---------------------|
| `steering/` | `.claude/instructions/` or `CLAUDE.md` | `.github/copilot-instructions.md` | System prompt context |
| `skills/` | Referenced files in `CLAUDE.md` | Inline in instructions | RAG documents or tool descriptions |
| `agents/` | Per-directory `CLAUDE.md` variants | Not supported | `Agent` class definitions |
| `mcp/` | `.claude/mcp.json` | Copilot Extensions | `Tool` implementations |

## Principles

1. **Organization enables portability.** Clear directory structure maps to any tool's config format.
2. **Skills are condensed; steering has depth.** Skills stay compact for context windows. They reference steering when detail is needed.
3. **MCP scripts are testable.** Each tool script does one thing, has tests alongside it, and runs independently of any agent framework.
4. **Everything is version-controllable.** Human-readable text, clean diffs, standard PR workflow.
5. **Agents are composable.** Adding a new persona means writing one JSON file over shared steering and skills.
