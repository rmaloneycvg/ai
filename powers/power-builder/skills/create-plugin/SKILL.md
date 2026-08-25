---
name: "create-plugin"
description: "Create a new Kiro Power using the Agent Plugins v1.0.0 specification. Use when building a new power from scratch with plugin.json, skills, and optional MCP server configuration."
license: "MIT"
metadata:
  author: "Kiro Team"
  version: "1.0.0"
---

# Create a New Agent Plugin

Interactive workflow for creating a Kiro Power that conforms to the Agent Plugins specification v1.0.0.

## Overview

This skill guides you through creating a portable plugin with:
- A `plugin.json` manifest
- One or more skills (each with `SKILL.md`)
- Optional `mcp.json` for MCP server integration
- Optional helper scripts, references, and assets

## Workflow Overview

```
1. Understand the user's use case
2. Determine plugin components (skills, MCP, or both)
3. Create plugin directory and plugin.json
4. Create skills (SKILL.md + supporting files)
5. Create mcp.json (if MCP server involved)
6. Test and install locally
```

## Step-by-Step Guide

### 1. Understand the Use Case

Have a natural conversation to understand:
- What problem does this plugin solve?
- Does it involve an MCP server? (needs mcp.json)
- What distinct tasks/workflows does it enable? (each becomes a skill)
- Is it pure documentation/guidance? (skills only, no mcp.json)
- Who is the audience?

Through this conversation, determine:
- The **plugin name** (lowercase, hyphens, 1-64 chars, no `--`)
- Whether it needs **mcp.json** (MCP server integration)
- How many **skills** it needs (one per distinct workflow/concern)
- Basic metadata (description, keywords, author)

### 2. Create Plugin Directory

```bash
mkdir -p {workspace}/powers/{plugin-name}
mkdir -p {workspace}/powers/{plugin-name}/skills
```

Tell the user the location: `{workspace}/powers/{plugin-name}/`

### 3. Generate plugin.json

Create the manifest. Always required.

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "{plugin-name}",
  "version": "1.0.0",
  "description": "{description}",
  "author": {
    "name": "{author-name}"
  },
  "keywords": ["{keyword1}", "{keyword2}", "{keyword3}"],
  "license": "MIT"
}
```

**Validation checklist:**
- [ ] `$schema` is exactly `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`
- [ ] `name` matches directory name
- [ ] `name` is 1-64 chars, lowercase `a-z0-9.-`, no `--` or `..`, starts/ends alphanumeric
- [ ] No fields beyond: `$schema`, `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `extensions`

### 4. Create Skills

For each distinct workflow or concern, create a skill directory with SKILL.md.

#### 4.1: Determine Skill Boundaries

Each skill should be a self-contained unit covering one task area. Split when:
- Workflows are independent (a user would use one without the other)
- Content exceeds 800 lines (break into focused skills)
- Different prerequisites or contexts

Keep together when:
- Steps form a single workflow
- Content is under 800 lines
- Users always need all the information together

#### 4.2: Create Skill Directory

For each skill:

```bash
mkdir -p {workspace}/powers/{plugin-name}/skills/{skill-name}
```

#### 4.3: Write SKILL.md

Each skill needs a SKILL.md with frontmatter and markdown body:

```markdown
---
name: "{skill-name}"
description: "{What it does}. Use when {trigger conditions}."
license: "MIT"
metadata:
  author: "{author}"
  version: "1.0.0"
---

# {Skill Title}

## Overview
{2-3 sentences: what this skill does, why it's useful, key capabilities.}

## Prerequisites Checklist
- [ ] {Requirement 1}
- [ ] {Requirement 2}

## Step-by-Step Guide

### 1. {First Step}
{Clear instructions with code examples}

### 2. {Second Step}
{Instructions...}

## Common Workflows

### Workflow: {Name}
**Goal:** {What this accomplishes}

## Troubleshooting

### Error: "{common error message}"
**Cause:** {why it happens}
**Solution:**
1. {fix step}
2. {verify step}

## Best Practices
- {Practice 1}
- {Practice 2}
- {Practice 3}
```

**SKILL.md validation:**
- [ ] Frontmatter `name` matches directory name exactly
- [ ] `description` starts with a verb, max 1024 chars
- [ ] `description` includes "Use when..." trigger phrase
- [ ] Body is 400-800 lines (move excess to references/)
- [ ] Code examples are complete and copy-paste ready
- [ ] All relative paths reference files within the skill directory

#### 4.4: Add Supporting Files (Optional)

**scripts/** - Helper scripts the agent or user can execute:
```bash
mkdir -p {workspace}/powers/{plugin-name}/skills/{skill-name}/scripts
```
Focus on core logic, < 500 lines. The agent may regenerate with appropriate parameters.

**references/** - Additional documentation too large for SKILL.md:
```bash
mkdir -p {workspace}/powers/{plugin-name}/skills/{skill-name}/references
```
Use for: API references, detailed examples, checklists, extended troubleshooting.

**assets/** - Templates, config files, static resources:
```bash
mkdir -p {workspace}/powers/{plugin-name}/skills/{skill-name}/assets
```
Use for: boilerplate templates, example configs, starter files.

### 5. Create mcp.json (If Needed)

Only create mcp.json if the plugin integrates with an MCP server.

#### 5.1: Gather MCP Server Information

Check if the user already has the MCP server configured in Kiro:
- Workspace: `.kiro/settings/mcp.json`
- User: `~/.kiro/settings/mcp.json`

If configured, read the existing config and adapt it. If not, ask the user for:
- How the server is started (command, npm package, binary)
- Required environment variables
- Whether it's local (stdio) or remote (HTTP)

#### 5.2: Generate mcp.json

**For local (stdio) servers:**
```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "{server-name}": {
      "type": "stdio",
      "command": "{command}",
      "args": ["{arg1}", "{arg2}"],
      "env": {
        "{ENV_VAR}": "{value-or-placeholder}"
      }
    }
  }
}
```

**For remote servers:**
```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "{server-name}": {
      "type": "streamable-http",
      "url": "https://example.com/mcp",
      "headers": {
        "X-Tenant": "public-value"
      }
    }
  }
}
```

**mcp.json validation:**
- [ ] `$schema` is exactly `https://agent-plugins.org/schemas/1.0.0/mcp.schema.json`
- [ ] Each server has a `type` field (`stdio`, `streamable-http`, or `sse`)
- [ ] stdio: `command` is a single token (not a shell string)
- [ ] stdio: `command` is either a bare name or starts with `./`
- [ ] `env` does not contain `PLUGIN_ROOT` or `PLUGIN_DATA` keys
- [ ] If `cwd` present: starts with `./`, `${PLUGIN_ROOT}`, or `${PLUGIN_DATA}`
- [ ] Remote URLs are HTTPS (HTTP only for localhost)
- [ ] No secrets in `env` or `headers`
- [ ] No fields beyond those defined per transport type

#### 5.3: Sanitize for Sharing

If the mcp.json contains user-specific values, replace with placeholders and document them in the relevant skill's SKILL.md under a "Configuration" section.

### 6. Final Structure Validation

Verify the complete plugin:

```
{plugin-name}/
├── plugin.json                    # Required
├── skills/                        # At least one skill recommended
│   ├── {skill-1}/
│   │   ├── SKILL.md              # Required per skill
│   │   ├── scripts/              # Optional
│   │   ├── references/           # Optional
│   │   └── assets/               # Optional
│   └── {skill-2}/
│       └── SKILL.md
└── mcp.json                       # Only if MCP server involved
```

**Final checklist:**
- [ ] `plugin.json` exists at root with valid `$schema` and `name`
- [ ] All skills have `SKILL.md` with valid frontmatter
- [ ] Skill `name` in frontmatter matches directory name
- [ ] `mcp.json` (if present) has valid `$schema` and `mcpServers`
- [ ] No files reference paths outside the plugin root
- [ ] No secrets in any configuration files

### 7. Test and Install

#### Install Locally

1. Open Kiro Powers UI (call action="configure")
2. Click "Add Custom Power" at the top
3. Select "Local Directory"
4. Provide the absolute path: `{workspace}/powers/{plugin-name}`
5. Click "Add"

#### Test

1. Use the "Try Power" button on the power's detail page
2. Also test in a fresh agent chat session
3. Make natural language requests that should trigger the power's skills
4. Verify MCP tools work if applicable

#### Iterate

If issues found:
1. Edit files in `{workspace}/powers/{plugin-name}/`
2. In Powers UI, navigate to the installed power
3. Click "Check for Updates" then "Update Power"
4. Re-test

## Sharing

### GitHub Repository
Push to a public GitHub repository. Users add the repo URL in Kiro Powers UI.

Before sharing:
- Sanitize mcp.json (replace secrets with placeholders)
- Document all placeholders in relevant SKILL.md files
- Include a LICENSE file

### Kiro Recommended Powers
Submit at: https://kiro.dev/powers/submit/

Requirements:
- Public GitHub repository
- Complete documentation and testing
- Sanitized configuration
- Clear use cases and examples

## Agent Guidelines

### Do
- Ask questions one at a time, don't overwhelm
- Generate complete files, never leave `{TODO}` placeholders
- Use exact MCP tool names from documentation
- Include copy-paste-ready examples
- Validate all files against the spec before finishing

### Don't
- Don't add fields not in the spec schemas
- Don't use shell command strings in `command` (single token only)
- Don't embed secrets in config files
- Don't create overly broad keywords that cause false activations
- Don't skip the `$schema` field on plugin.json or mcp.json
- Don't put `PLUGIN_ROOT` or `PLUGIN_DATA` as keys in `env`
