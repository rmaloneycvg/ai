# AI Workspace

A portable, structured collection of AI agent configurations, steering documents, skills, and MCP tooling. Designed for Kiro CLI but adaptable to any AI coding assistant or agent framework.

## 1. Overview

This repository organizes everything an AI assistant needs—behavioral guidance, domain knowledge, tool access, and agent personas—into a modular structure that can be version-controlled, shared, and ported across tools.

| Directory | Purpose |
|-----------|---------|
| `steering/` | Detailed steering documents organized by concern (React, Terraform, orchestration, etc.). These are the comprehensive instructions that shape agent behavior. |
| `skills/` | Condensed skill files with YAML frontmatter, loaded on demand. Each skill is a focused capability (add code, refactor, test, deploy) with pointers back to detailed steering. |
| `agents/` | Custom agent configurations in Kiro CLI JSON format. Each agent defines its tools, resources, MCP servers, and persona. |
| `mcp/` | MCP (Model Context Protocol) server configs and executable scripts that extend agent capabilities with external tools. |

## 2. Directory Structure

```
ai/
├── README.md                        # This file
├── steering/                        # Detailed behavioral guidance
│   ├── orchestration/               # Agent coordination and workflow rules
│   │   └── local.md                 # Local development orchestration
│   ├── conventions/                 # Code style and naming standards
│   │   └── code-style.md           # TypeScript naming, file org, imports, patterns
│   ├── security/                    # Security policies and standards
│   │   └── policies.md             # Auth, validation, CORS, secrets, headers
│   └── preferences/
│       └── stack/
│           ├── react/
│           │   └── dependency-graph.md   # React stack choices
│           ├── nextjs/
│           │   ├── overview.md           # Next.js stack overview
│           │   ├── app-router.md         # App router patterns
│           │   ├── server-components.md  # RSC guidance
│           │   ├── data-patterns.md      # ISR, server actions
│           │   └── middleware.md         # Auth, redirects, A/B
│           ├── node/
│           │   └── api-caching.md        # Node.js API caching patterns
│           └── csharp/
│               └── api-caching.md        # C# API caching patterns
├── skills/                          # On-demand skill files
│   ├── react-components.md          # React component scaffolding
│   ├── backend-rest-api-feature.md  # REST API endpoint development
│   ├── backend-cron-feature.md      # Cron/scheduled job features
│   ├── project-readme-documentation.md # Project README generation/maintenance
│   ├── create-kiro-skill.md         # Creating new Kiro skill files
│   ├── refactor.md                  # Refactoring existing code
│   ├── debug.md                     # Debugging and profiling
│   ├── test.md                      # Writing and running tests
│   └── deploy.md                    # Deployment workflows
├── agents/                          # Agent persona configurations
│   ├── dev.json                     # Full-stack development agent
│   ├── frontend.json                # React/Next.js focused agent
│   └── infra.json                   # Infrastructure/DevOps agent
└── mcp/                             # MCP server tooling
    └── mcp-scripts/                 # Executable tool scripts
        ├── git/                     # Git operations (status, diff, log)
        ├── io/                      # File I/O operations
        └── postgres/                # Database query tools
```

## 3. Usage with Kiro CLI

### Linking into a Project

Kiro CLI looks for a `.kiro/` directory at the project root. Symlink or copy this workspace into your project:

```bash
# Option 1: Symlink the entire workspace
ln -s ~/workspace/ai /path/to/project/.kiro

# Option 2: Symlink individual pieces
mkdir -p /path/to/project/.kiro
ln -s ~/workspace/ai/agents /path/to/project/.kiro/agents
ln -s ~/workspace/ai/steering /path/to/project/.kiro/steering
ln -s ~/workspace/ai/skills /path/to/project/.kiro/skills
ln -s ~/workspace/ai/mcp /path/to/project/.kiro/mcp
```

### Agent Loading

Agents are JSON files in `agents/`. Kiro loads them by name or keyboard shortcut:

```bash
# Start Kiro with a specific agent
kiro --agent infra

# Or use keyboard shortcuts defined in agent configs:
#   Ctrl+D → dev agent
#   Ctrl+F → frontend agent
#   Ctrl+I → infra agent
```

Each agent config defines:
- `prompt` — the base system prompt (typically a steering doc)
- `resources` — steering docs and skills loaded into context
- `tools` / `allowedTools` — tool access restrictions
- `mcpServers` — which MCP servers to connect
- `hooks` — commands run on agent lifecycle events

### Skill Loading

Skills use the `skill://` resource URI scheme. They're loaded on demand based on the agent config:

```json
{
  "resources": [
    "skill://../skills/react-components.md",
    "skill://../skills/backend-rest-api-feature.md",
    "skill://../skills/project-readme-documentation.md"
  ]
}
```

Skills are condensed and contain YAML frontmatter with metadata:

```markdown
---
name: react-components
description: Scaffold new React components with TypeScript, Storybook stories, tests, and proper exports.
---

# React Component Scaffolding

Instructions for scaffolding components...
```

### Steering Loading

Steering documents are loaded via `file://` URIs with glob support:

```json
{
  "resources": [
    "file://../steering/**/*.md",
    "file://../steering/react/**/*.md"
  ]
}
```

Agents can load all steering (broad context) or a focused subset (domain-specific agent).

## 4. Migration Guides

### Claude Code

Claude Code uses `CLAUDE.md` files and a `.claude/` directory for configuration.

**Mapping:**

| This repo | Claude Code equivalent |
|-----------|----------------------|
| `steering/` | `.claude/instructions/` directory or inline in `CLAUDE.md` |
| `skills/` | Referenced docs in `CLAUDE.md` via file paths |
| `agents/` | Not directly supported; use `CLAUDE.md` prompt variations per branch/directory |
| `mcp/` | `.claude/mcp.json` |

**Example: Load steering into CLAUDE.md**

```bash
#!/bin/bash
# scripts/generate-claude-md.sh
# Concatenate steering docs into CLAUDE.md for Claude Code

OUTPUT="CLAUDE.md"
echo "# Project Instructions" > "$OUTPUT"
echo "" >> "$OUTPUT"

for doc in steering/**/*.md; do
  echo "<!-- Source: $doc -->" >> "$OUTPUT"
  cat "$doc" >> "$OUTPUT"
  echo -e "\n---\n" >> "$OUTPUT"
done

echo "Generated $OUTPUT from steering/ documents"
```

**Example: Convert MCP scripts to .claude/mcp.json**

```json
{
  "mcpServers": {
    "git": {
      "command": "node",
      "args": ["./mcp/mcp-scripts/git/index.js"],
      "env": {}
    },
    "postgres": {
      "command": "node",
      "args": ["./mcp/mcp-scripts/postgres/index.js"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

**Example: Use steering as .claude/instructions/ files**

```bash
#!/bin/bash
# scripts/sync-to-claude.sh
# Mirror steering/ into .claude/instructions/

mkdir -p .claude/instructions

for doc in steering/**/*.md; do
  # Flatten path: steering/react/components.md → .claude/instructions/react-components.md
  target=$(echo "$doc" | sed 's|steering/||; s|/|-|g')
  cp "$doc" ".claude/instructions/$target"
done
```

---

### GitHub Copilot CLI

GitHub Copilot uses `.github/copilot-instructions.md` for project-level instructions.

**Mapping:**

| This repo | Copilot equivalent |
|-----------|-------------------|
| `steering/` | `.github/copilot-instructions.md` (single file, concatenated) |
| `skills/` | Referenced inline in instructions |
| `agents/` | Not directly supported |
| `mcp/` | Custom extensions via Copilot Extensions |

**Example: Generate copilot-instructions.md from steering**

```bash
#!/bin/bash
# scripts/generate-copilot-instructions.sh

OUTPUT=".github/copilot-instructions.md"
mkdir -p .github
echo "# Copilot Instructions" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "These instructions are auto-generated from ai/steering/." >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Include steering docs
for doc in steering/**/*.md; do
  section=$(basename "$doc" .md)
  echo "## ${section}" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
  cat "$doc" >> "$OUTPUT"
  echo -e "\n" >> "$OUTPUT"
done

# Append condensed skills as reference
echo "## Available Skills" >> "$OUTPUT"
echo "" >> "$OUTPUT"
for skill in skills/*.md; do
  name=$(basename "$skill" .md)
  # Extract description from YAML frontmatter
  desc=$(sed -n '/^description:/s/description: *//p' "$skill")
  echo "- **${name}**: ${desc}" >> "$OUTPUT"
done

echo "Generated $OUTPUT"
```

**Example: .github/copilot-instructions.md structure**

```markdown
# Copilot Instructions

## React Components
Follow these patterns when generating React code:
- Use functional components with hooks
- ...

## Terraform
When writing Terraform:
- Use modules for reusable infrastructure
- ...

## Available Skills
- **react-components**: Scaffold new React components with TypeScript, Storybook, tests
- **backend-rest-api-feature**: Add or modify REST API endpoints for Node.js or C#
- **backend-cron-feature**: Add or modify scheduled/cron jobs and background workers
- **project-readme-documentation**: Generate and maintain project README documentation
- **create-kiro-skill**: Create new Kiro skill files with proper schema and overlap auditing
- **refactor**: Restructure code without changing behavior
- **debug**: Debugging and performance profiling
- **test**: Generate and run tests
- **deploy**: Execute deployment workflows
```

---

### LangChain / LangGraph

For programmatic agent frameworks, steering becomes system prompt context, skills become tool descriptions or RAG context, and MCP scripts become tool implementations.

**Mapping:**

| This repo | LangChain/LangGraph equivalent |
|-----------|-------------------------------|
| `steering/` | System prompts loaded as context strings |
| `skills/` | Tool descriptions or retrieval-augmented context |
| `agents/` | `Agent` class definitions with tool bindings |
| `mcp/` | `Tool` implementations wrapping the same scripts |

**Example: Load steering as system context (Python)**

```python
"""Load steering documents as agent system context."""
from pathlib import Path
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI


def load_steering(patterns: list[str]) -> str:
    """Load and concatenate steering documents matching glob patterns."""
    ai_root = Path("~/workspace/ai").expanduser()
    sections = []

    for pattern in patterns:
        for path in sorted(ai_root.glob(pattern)):
            sections.append(f"<!-- {path.name} -->\n{path.read_text()}")

    return "\n\n---\n\n".join(sections)


# Load domain-specific steering
react_context = load_steering(["steering/react/**/*.md"])
infra_context = load_steering(["steering/terraform/**/*.md", "steering/docker/**/*.md"])

# Use as system message
llm = ChatOpenAI(model="gpt-4o")
messages = [
    SystemMessage(content=f"You are a React expert.\n\n{react_context}"),
]
response = llm.invoke(messages)
```

**Example: Skills as retrieval-augmented context**

```python
"""Index skills for retrieval-augmented generation."""
import yaml
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


def load_skills(skills_dir: str = "~/workspace/ai/skills") -> list[Document]:
    """Parse skill files into LangChain documents with metadata."""
    skills_path = Path(skills_dir).expanduser()
    documents = []

    for skill_file in skills_path.glob("*.md"):
        content = skill_file.read_text()

        # Parse YAML frontmatter
        if content.startswith("---"):
            _, frontmatter, body = content.split("---", 2)
            metadata = yaml.safe_load(frontmatter)
        else:
            metadata = {}
            body = content

        documents.append(Document(
            page_content=body.strip(),
            metadata={
                "name": metadata.get("name", skill_file.stem),
                "description": metadata.get("description", ""),
                "triggers": metadata.get("triggers", []),
                "steering_refs": metadata.get("steering", []),
                "source": str(skill_file),
            },
        ))

    return documents


# Build a vector store for skill retrieval
skills = load_skills()
vectorstore = FAISS.from_documents(skills, OpenAIEmbeddings())
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# Query relevant skills based on user intent
relevant_skills = retriever.invoke("add a new React component")
for skill in relevant_skills:
    print(f"Skill: {skill.metadata['name']}")
    print(f"  {skill.page_content[:100]}...")
```

**Example: MCP scripts as LangChain tools**

```python
"""Wrap MCP scripts as LangChain tools."""
import subprocess
import json
from langchain_core.tools import tool


@tool
def git_status() -> str:
    """Get the current git status of the repository."""
    result = subprocess.run(
        ["./mcp/mcp-scripts/git/status.sh"],
        capture_output=True, text=True, timeout=10,
    )
    return result.stdout


@tool
def query_postgres(sql: str) -> str:
    """Execute a read-only SQL query against the database."""
    result = subprocess.run(
        ["./mcp/mcp-scripts/postgres/query.sh", sql],
        capture_output=True, text=True, timeout=30,
    )
    return result.stdout


@tool
def read_file(path: str) -> str:
    """Read the contents of a file."""
    result = subprocess.run(
        ["./mcp/mcp-scripts/io/read.sh", path],
        capture_output=True, text=True, timeout=10,
    )
    return result.stdout
```

**Example: Agent definition mirroring agents/infra.json**

```python
"""Define agents matching the Kiro agent configs."""
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from .steering import load_steering
from .tools import git_status, query_postgres, read_file


def create_infra_agent():
    """Create an infrastructure agent matching agents/infra.json."""
    steering = load_steering([
        "steering/orchestration/**/*.md",
        "steering/terraform/**/*.md",
        "steering/docker/**/*.md",
        "steering/k8s/**/*.md",
    ])

    llm = ChatOpenAI(model="gpt-4o")
    tools = [git_status, query_postgres, read_file]

    agent = create_react_agent(
        llm,
        tools=tools,
        state_modifier=f"You are an infrastructure agent.\n\n{steering}",
    )
    return agent


def create_frontend_agent():
    """Create a frontend agent matching agents/frontend.json."""
    steering = load_steering([
        "steering/react/**/*.md",
        "steering/nextjs/**/*.md",
    ])

    llm = ChatOpenAI(model="gpt-4o")
    tools = [read_file]

    agent = create_react_agent(
        llm,
        tools=tools,
        state_modifier=f"You are a frontend development agent.\n\n{steering}",
    )
    return agent
```

## 5. Principles

1. **Strict organization enables portability.** A clear directory structure makes it trivial to map this workspace onto any tool's configuration format. The migration guides above prove the point: steering, skills, agents, and tools map cleanly to every major AI coding assistant.

2. **Skills are condensed with pointers to detailed steering.** Skills are the "what to do" in compact form. They reference steering docs for the "how to do it in detail." This keeps context windows efficient while maintaining depth when needed.

3. **MCP scripts are testable and language-minimal.** Tool scripts are simple executables (shell scripts, small Node/Python scripts) that do one thing. They can be tested independently, run outside any agent framework, and wrapped by any tool abstraction.

4. **Everything is version-controllable.** No binary blobs, no IDE-specific state, no generated caches. Every file is human-readable text that diffs cleanly and merges without conflict. Agents, steering, and skills evolve with your codebase through the same PR workflow.

5. **Agents are composable, not monolithic.** Each agent configuration is a focused lens over the same shared steering and skills. Adding a new agent persona means writing one JSON file, not duplicating documentation.
