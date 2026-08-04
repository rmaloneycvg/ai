# User Guide — LangGraph Workspace Runtime

## What This Does

This system takes the same artifact files that Kiro uses (agents, skills, steering, tools) and runs them locally using LangGraph + local LLMs (Ollama). You author artifacts once — they work in Kiro's cloud environment AND locally through this runtime.

**Two modes of operation:**

| Mode | Command | What it does |
|------|---------|-------------|
| **Create** | `make run TASK="..."` | Generates new Kiro artifacts (skills, agents, steering, tools) |
| **Execute** | `make execute-agent ...` | Runs existing Kiro artifacts as LangGraph workflows using local models |

Run `make help` to see all available commands with descriptions.

---

## Prerequisites

### Required

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- [Ollama](https://ollama.com/) running locally with at least one model pulled

### Setup

```bash
cd ~/workspace/ai/custom/langgraph
make setup
```

This syncs dependencies, creates `.env` from the template, and verifies Ollama connectivity.

### Pull a Model

```bash
ollama pull llama3.1:8b    # 4.7GB, good baseline
# OR for better quality:
ollama pull qwen2.5:14b    # 8.9GB, better reasoning
```

### Verify Ollama is Running

```bash
make provider-test
# Or with a specific model:
make provider-test MODEL=qwen2.5:14b
```

---

## Workflows

### Workflow 1: Execute an Agent

Load a Kiro agent JSON config and interact with it using a local model.

```bash
# General-purpose dev agent
make execute-agent AGENT=general-dev TASK="Show me the project structure and suggest improvements"

# Frontend-focused agent (restricted to React/Next.js files)
make execute-agent AGENT=react-frontend TASK="Add a UserProfile component with avatar and name"

# Infrastructure agent
make execute-agent AGENT=infra-dev TASK="Review the Tiltfile and suggest optimization"

# Override model for better quality
make execute-agent AGENT=general-dev MODEL=qwen2.5:14b TASK="Explain the authentication flow"
```

**What happens internally:**
1. Loads `~/workspace/ai/agents/<name>.json`
2. Runs `agentSpawn` hooks (git status, branch, etc.) for context
3. Resolves `resources` (skills, files) via progressive disclosure
4. Maps allowed tools from the config to LangGraph `@tool` functions
5. Builds system prompt from: agent prompt + hook context + skill context + guardrails
6. Creates a LangGraph ReAct agent with the local model
7. Executes the task with tool calling

### Workflow 2: Execute a Skill

Run a structured, phased workflow defined in a skill markdown file.

```bash
# Debugging workflow (8 steps with approval gate)
make execute-skill SKILL=general-debug TASK="The /api/users endpoint returns 500 errors intermittently"

# Documentation generation
make execute-skill SKILL=general-documentation TASK="Document the payment service API"

# Code refactoring
make execute-skill SKILL=general-refactor TASK="Extract the validation logic into a shared module"

# Skip approval gates (non-interactive)
make execute-ni SKILL=general-debug TASK="Fix the failing test in auth.test.ts"
```

**What happens internally:**
1. Loads `~/workspace/ai/skills/<name>.md`
2. Parses workflow steps into LangGraph nodes
3. Detects approval gates → pauses for user input (or auto-approves with `execute-ni`)
4. Detects verify/validate steps → wires retry loops
5. Each step gets the skill's Role & Tone, guardrails, and previous step results as context
6. Executes step-by-step, passing results downstream
7. On failure: retries up to max_retries, then reports to user

### Workflow 3: Execute an Orchestrator (Multi-Agent Pipeline)

Run a multi-agent pipeline that classifies intent and delegates to specialized sub-agents.

```bash
# The orchestrator classifies and routes automatically
make execute-orch AGENT=react-orchestrator TASK="Build a complete settings page with form validation"

# Force routing to a specific sub-agent with a prefix
make execute-orch AGENT=react-orchestrator TASK="scaffold: a new DataTable component"
make execute-orch AGENT=react-orchestrator TASK="test: write vitest tests for the UserProfile"
make execute-orch AGENT=react-orchestrator TASK="refactor: extract useAuth hook from LoginForm"
make execute-orch AGENT=react-orchestrator TASK="arch: how should I structure the dashboard layout"
make execute-orch AGENT=react-orchestrator TASK="style: make the sidebar responsive"
```

**Forced routing prefixes** (skip LLM classification, go directly to sub-agent):

| Prefix | Routes to | Use when |
|--------|-----------|----------|
| `scaffold:` | react-scaffold | Creating new component files |
| `test:` | react-testing | Writing or running tests |
| `refactor:` | react-refactor | Extracting/restructuring code |
| `arch:` | react-architecture | Design/structure questions |
| `style:` | react-styling | CSS/Tailwind/layout work |

**What happens internally:**
1. Loads orchestrator agent config, detects `crew.availableAgents`
2. Checks for forced routing prefix (e.g., `scaffold:`)
3. If no prefix: uses LLM classification with the orchestrator's prompt rules
4. Determines pipeline (single agent or multi-stage sequence)
5. Executes each stage with the appropriate model tier
6. Passes upstream decisions as constraints to downstream stages
7. Halts pipeline if any stage fails

### Workflow 4: Create New Artifacts

Generate new Kiro-format workspace artifacts.

```bash
# Create a new skill
make run TASK="Create a skill for database migration management"

# Create a new agent
make run TASK="Create an agent for data pipeline management"

# Write a steering doc
make run TASK="Write a steering doc for GraphQL resolver patterns"

# Build a tool
make run TASK="Build a tool for querying Elasticsearch"
```

**Output locations:**
- Skills → `output/skills/<name>.md`
- Agents → `output/agents/<name>.json`
- Steering → `output/steering/<category>/<name>.md`
- Tools → `output/tools/<func_name>.py`

### Workflow 5: Discover Available Artifacts

```bash
# List all agents (shows orchestrators with [orchestrator] tag)
make list-agents

# List all skills
make list-skills

# Show token budget for your model
make budget
make budget MODEL=qwen2.5:14b

# Show what context gets loaded for a query
make disclose MODEL=llama3.1:8b QUERY="skill schema conventions"
```

### Workflow 6: Model Management

```bash
# Test provider connection
make provider-test
make provider-test MODEL=qwen2.5:14b

# List configured providers and models
make providers

# Profile a model (generates optimized prompt strategies)
make profile MODEL=llama3.1:8b
make profile MODEL=qwen2.5:14b

# Show available tools for a task phase
make tools
make tools PHASE=skill_create
```

---

## Configuration

### Model Mapping (`config/model-mapping.yaml`)

Kiro agent configs reference cloud models (`claude-opus-4.8`, `gpt-4o`). This file tells the runtime which local model to substitute.

```yaml
default: llama3.1:8b

tiers:
  strong: qwen2.5:14b    # For architecture/reasoning tasks
  medium: llama3.1:8b    # For general tasks
  fast: llama3.1:8b      # For scaffolding/boilerplate

# Optional: direct overrides
overrides:
  claude-opus-4.8: qwen2.5:14b
  claude-haiku-4.5: llama3.1:8b
```

**When to edit:** When you have multiple models pulled and want orchestrator sub-agents to use different ones based on task complexity.

### Provider Config (`config/providers.yaml`)

Defines connection info and model capabilities. You rarely need to edit this unless adding new models.

### Environment Variables (`.env`)

```bash
LLM_PROVIDER=ollama          # Default provider
LLM_MODEL=llama3.1:8b        # Default model
OLLAMA_BASE_URL=http://localhost:11434   # Ollama server URL
```

---

## Common Errors and Troubleshooting

### Connection Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ConnectionRefusedError: [Errno 111]` | Ollama is not running | Start Ollama: `ollama serve` or launch the app |
| `httpx.ConnectError` | Wrong Ollama URL | Check `OLLAMA_BASE_URL` in `.env` matches where Ollama is running |
| `404 model not found` | Model not pulled | Run `ollama pull llama3.1:8b` |
| `timeout` on first call | Model loading into GPU memory | Wait 10-30s on first call, subsequent calls are fast |

**Quick diagnostic:**
```bash
# Is Ollama running?
curl http://localhost:11434/api/tags

# Is your model pulled?
ollama list

# Can the system reach it?
make provider-test
```

### Artifact Not Found

| Error | Cause | Fix |
|-------|-------|-----|
| `FileNotFoundError: Agent 'xyz' not found` | Agent name doesn't exist | Run `make list-agents` to see available names |
| `FileNotFoundError: Skill 'xyz' not found` | Skill name doesn't exist | Run `make list-skills` to see available names |

**Note:** Names are the filename without extension. Use kebab-case:
- ✅ `AGENT=react-frontend` (matches `agents/react-frontend.json`)
- ❌ `AGENT="React Frontend"` (wrong format)
- ❌ `AGENT=react-frontend.json` (don't include extension)

### Model Quality Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Agent ignores tools, produces only text | Model doesn't support tool calling | Use a model with `supports_tools: true` (llama3.1:8b, qwen2.5:14b) |
| Agent produces garbled JSON tool calls | Model too weak for tool calling | Switch to a stronger model: `MODEL=qwen2.5:14b` |
| Orchestrator routes to wrong agent | Classification too complex for model | Use forced routing prefixes (`scaffold:`, `test:`, `refactor:`) |
| Skill steps produce generic responses | Context window too small | Use a model with larger context (qwen2.5:14b = 32K) |
| Responses cut off mid-sentence | Max tokens too low or context overflow | Try a model with larger context window |

**Recommendation:** Start with `llama3.1:8b` for simple tasks. Use `qwen2.5:14b` for anything involving tool calling, multi-step reasoning, or orchestration.

### Tool Execution Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `BLOCKED: Cannot write to 'path'` | Agent's `allowedPaths` restricts this path | Check the agent JSON's `toolsSettings.write.allowedPaths` |
| `Permission denied` on shell commands | Agent's `allowedCommands` doesn't include this | Check `toolsSettings.shell.allowedCommands` in the agent config |
| Tool returns empty results | Path doesn't exist or CWD is wrong | Run from the correct project directory |

### Recursion/Timeout Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `RecursionLimit reached` | Agent looping on tool calls | Model is confused — try a stronger model or simplify the task |
| Skill hangs at approval gate | Interactive mode waiting for input | Use `make execute-ni` to auto-approve |
| Pipeline never completes | Sub-agent stuck in retry loop | Kill and re-run with `make execute-ni` or use forced routing |

### Makefile Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Error: AGENT is required` | Missing required variable | Add `AGENT=name` before TASK |
| `Error: TASK is required` | Missing task description | Add `TASK="your task here"` |
| Quotes breaking in TASK | Shell quote handling | Use double quotes: `TASK="your task"` |

### Import/Module Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'src'` | Running from wrong directory | `cd ~/workspace/ai/custom/langgraph` first |
| `ModuleNotFoundError: No module named 'langgraph'` | Dependencies not installed | Run `make setup` |

---

## Tips for Best Results

### Use the Right Model for the Task

| Task Type | Recommended Model | Why |
|-----------|------------------|-----|
| Simple Q&A, file reading | `llama3.1:8b` | Fast, sufficient quality |
| Tool calling, code generation | `qwen2.5:14b` | Better instruction following |
| Multi-step orchestration | `qwen2.5:14b` | Needs strong reasoning for routing |
| Scaffolding/boilerplate | `llama3.1:8b` | Speed matters more than quality |
| Architecture decisions | `qwen2.5:14b` or larger | Requires deep reasoning |

### Run from the Right Directory

The `file://` resources in agent configs resolve relative to CWD. If an agent references `file://package.json`, you need to run from the project that has that file:

```bash
# Run the react-frontend agent from your React project
cd ~/workspace/my-react-app
make -C ~/workspace/ai/custom/langgraph execute-agent AGENT=react-frontend TASK="Add a new page"
```

### Use Forced Routing for Orchestrators

LLM classification can misroute, especially with small models. Use prefixes to skip classification entirely:

```bash
# Instead of letting the orchestrator guess:
make execute-orch AGENT=react-orchestrator TASK="create a new Button"

# Be explicit:
make execute-orch AGENT=react-orchestrator TASK="scaffold: a new Button component"
```

### Profile Your Model First

Profiling tells the system your model's strengths so it can adapt prompts:

```bash
make profile MODEL=llama3.1:8b
# Now the system knows: CoT needed? Examples needed? JSON mode?
```

### Non-Interactive Mode for Automation

Skills with approval gates will pause and wait for input. For CI/scripting:

```bash
make execute-ni SKILL=general-debug TASK="Fix the failing test"
make execute-ni AGENT=general-dev TASK="Generate README"
```

---

## Command Reference

Run `make help` for the full list. Key commands:

### Execution

| Command | Purpose |
|---------|---------|
| `make execute-agent AGENT=x TASK="..."` | Run a Kiro agent with a local model |
| `make execute-skill SKILL=x TASK="..."` | Run a Kiro skill workflow |
| `make execute-orch AGENT=x TASK="..."` | Run a multi-agent pipeline |
| `make execute-ni AGENT=x TASK="..."` | Run non-interactive (auto-approves) |
| `make run TASK="..."` | Create a new artifact |

### Discovery

| Command | Purpose |
|---------|---------|
| `make list-agents` | Show available agents |
| `make list-skills` | Show available skills |
| `make tools` | Show available tools |
| `make tools PHASE=skill_create` | Show tools for a specific phase |
| `make disclose QUERY="..."` | Preview what context gets loaded |

### Model & Provider

| Command | Purpose |
|---------|---------|
| `make provider-test` | Test model connectivity |
| `make provider-test MODEL=qwen2.5:14b` | Test a specific model |
| `make profile MODEL=x` | Calibrate model capabilities |
| `make budget MODEL=x` | Show token budget allocation |
| `make providers` | List configured providers |

### Development

| Command | Purpose |
|---------|---------|
| `make test` | Run all tests |
| `make test-unit` | Unit tests only (fast, no services) |
| `make test-runtime` | Runtime module tests only |
| `make lint` | Check code style |
| `make format` | Auto-fix formatting |
| `make setup` | Initial project setup |
| `make clean` | Remove caches |
| `make clean-output` | Remove generated artifacts |

### Infrastructure

| Command | Purpose |
|---------|---------|
| `make infra-up` | Start Postgres/Redis (docker-compose) |
| `make infra-down` | Stop infrastructure |
| `make infra-logs` | Tail service logs |
| `make serve` | Start REST + WebSocket server |

---

## Workspace Layout

The system reads from two locations:

```
~/workspace/ai/                     ← Primary workspace (shared with Kiro)
├── agents/*.json                   ← Agent configs (15 available)
├── skills/*.md                     ← Skill workflows (50 available)
├── steering/                       ← Conventions, patterns, security rules
│   ├── conventions/
│   ├── orchestration/
│   ├── preferences/
│   └── security/
└── templates/

~/workspace/ai/custom/langgraph/    ← This project
├── Makefile                        ← All commands (run `make help`)
├── config/
│   ├── providers.yaml              ← LLM provider config
│   ├── model-mapping.yaml          ← Cloud → local model mapping
│   └── model-profiles/             ← Calibration results
├── output/                         ← Generated artifacts (from `make run`)
├── docs/
│   └── USER_GUIDE.md              ← This file
├── steering-local/                 ← Local steering overrides + design docs
└── src/
    ├── runtime/                    ← Artifact execution engine
    ├── graphs/                     ← Creation sub-agents
    ├── context/                    ← Token budget, progressive disclosure
    ├── providers/                  ← Ollama, OpenAI, Anthropic, vLLM, llama.cpp
    ├── profiler/                   ← Model calibration
    └── tools/                      ← @tool implementations
```

---

## How It Differs from Kiro

| Aspect | Kiro | This Runtime |
|--------|------|-------------|
| Models | Claude (cloud) | Local via Ollama/vLLM/llama.cpp |
| Tools | MCP servers (TypeScript) | Python `@tool` functions (same behavior) |
| Context management | Automatic | Explicit budget + progressive disclosure |
| Multi-agent | `subagent` tool | LangGraph sub-graphs with model mapping |
| Artifacts | Source of truth | Consumed unchanged |
| Execution | Cloud-hosted | Local, offline-capable |
| Approval gates | Interactive UI | CLI prompt or `make execute-ni` |
| Commands | Editor-integrated | `make` targets |

The same `agents/*.json` and `skills/*.md` files work in both environments without modification.
