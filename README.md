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
│   │   └── frontend-pipeline-contract.md  # Sub-agent pipeline I/O schema
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
│   ├── fe-scaffold.md                  # Pipeline: component scaffolding
│   ├── fe-architecture.md              # Pipeline: UI architecture decisions
│   ├── fe-styling.md                   # Pipeline: Tailwind/shadcn styling
│   ├── fe-testing.md                   # Pipeline: tests and stories
│   ├── fe-refactor.md                  # Pipeline: code refactoring
│   ├── resume-builder.md               # Resume/cover letter generation workflow
│   ├── experience-parser.md            # Extract experience from .docx files
│   └── job-scorer.md                   # Score resume against job description
├── agents/                             # Agent persona configs (JSON)
│   ├── dev.json                        # Full-stack: all steering, broad tool access
│   ├── frontend.json                   # React/Next.js only, no shell/db access
│   ├── frontend-orchestrator.json      # Orchestrator: routes to sub-agents by task type
│   ├── fe-scaffold.json                # Sub-agent: component scaffolding (haiku)
│   ├── fe-architecture.json            # Sub-agent: UI architecture decisions (opus)
│   ├── fe-styling.json                 # Sub-agent: Tailwind/shadcn styling (haiku)
│   ├── fe-testing.json                 # Sub-agent: tests and stories (sonnet)
│   ├── fe-refactor.json                # Sub-agent: code refactoring (opus)
│   ├── infra.json                      # Infrastructure/DevOps focused
│   ├── resume-builder.json             # Resume generation orchestrator
│   ├── experience-parser.json          # Extract experience from .docx resumes
│   └── job-scorer.json                 # Score resume fit against a job description
├── mcp/                                # MCP server definitions + tool scripts
│   ├── servers.json                    # Server config (git, io, postgres)
│   └── mcp-scripts/
│       ├── git/status.ts               # Parsed git status
│       ├── io/read-json.ts             # Read and validate JSON files
│       ├── io/write-json.ts            # Write JSON with formatting
│       ├── postgres/query.py           # Parameterized read-only queries
│       └── postgres/seed.py            # Run SQL seed files
├── .kiro/                              # Mirror of agents/steering/skills for Kiro CLI
├── root-to-kiro.sh                     # Sync root dirs → .kiro/
├── kiro-to-root.sh                     # Sync .kiro/ → root dirs
└── .gitignore
```

## Concepts

**Steering** — detailed, prescriptive documents that shape how an agent writes code. They define technology choices, architectural patterns, security requirements, and naming conventions. Loaded as context via `file://` URIs.

**Skills** — condensed instruction sets with YAML frontmatter. Each skill is a focused capability (scaffold a component, add an API endpoint, run a deploy). Skills reference steering docs for depth but stay compact for context efficiency.

**Agents** — JSON configs that compose a persona from steering + skills + tools. Each agent is a focused lens: the frontend agent loads React/Next.js steering and restricts file writes to `src/`; the infra agent loads orchestration/Terraform docs and gets shell access.

**MCP Scripts** — small, testable tool implementations (TypeScript and Python) that agents invoke via the Model Context Protocol. Each does one thing: query postgres, read a file, get git status.

## Usage

### In a project

Kiro CLI looks for `.kiro/` at the project root. Symlink this workspace:

```bash
ln -s ~/workspace/ai /path/to/project/.kiro
```

Or symlink individual directories:

```bash
mkdir -p /path/to/project/.kiro
ln -s ~/workspace/ai/agents /path/to/project/.kiro/agents
ln -s ~/workspace/ai/steering /path/to/project/.kiro/steering
ln -s ~/workspace/ai/skills /path/to/project/.kiro/skills
```

### Selecting an agent

```bash
kiro --agent dev        # Full-stack, broad access
kiro --agent frontend   # React/Next.js scoped
kiro --agent infra      # Infrastructure/DevOps
kiro --agent frontend-orchestrator  # Multi-agent pipeline (delegates to sub-agents)
kiro --agent resume-builder         # Generate tailored resume + cover letter from a JD
kiro --agent experience-parser      # Extract experience data from .docx resumes
kiro --agent job-scorer             # Score resume fit against a job description
```

### Syncing the .kiro mirror

The repo maintains a `.kiro/` copy of `agents/`, `steering/`, and `skills/` for when the repo itself is used as a `.kiro` directory:

```bash
./root-to-kiro.sh              # Copy root → .kiro/
./root-to-kiro.sh /other/proj  # Copy root → /other/proj/.kiro/

./kiro-to-root.sh              # Copy .kiro/ → root (after editing via Kiro)
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
    "file://../steering/**/*.md",      // Glob-matched steering docs
    "file://../skills/react-components.md"  // Specific skills
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
