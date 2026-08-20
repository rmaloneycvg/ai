---
name: "agent-plugins-reference"
description: "Reference documentation for the Agent Plugins v1.0.0 specification. Use when you need to understand plugin structure, plugin.json schema, SKILL.md format, mcp.json configuration, or environment variable expansion."
license: "MIT"
metadata:
  author: "Kiro Team"
  version: "1.0.0"
---

# Agent Plugins Specification Reference

## Overview

Agent Plugins is an open, vendor-neutral specification (v1.0.0) maintained by a Technical Steering Committee including Amazon, Cursor, Microsoft, OpenAI, and Vercel. It defines a portable package format for Agent Skills and MCP servers that compatible clients can discover and load consistently.

A power built to the agent-plugins standard is portable across any conformant client.

## Plugin Structure

```
my-plugin/
├── plugin.json          # Required manifest
├── skills/              # Agent Skills (optional)
│   └── my-skill/
│       ├── SKILL.md     # Required per skill
│       ├── scripts/     # Helper scripts (optional)
│       ├── references/  # Reference docs (optional)
│       └── assets/      # Templates, configs (optional)
├── mcp.json             # MCP server config (optional)
└── com.example.client/  # Client extensions (optional)
```

## plugin.json (Manifest)

Required. Identifies the plugin and the spec version it targets.

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "author": {
    "name": "Your Name",
    "url": "https://example.com"
  },
  "keywords": ["keyword1", "keyword2"],
  "license": "MIT",
  "repository": "https://github.com/example/my-plugin"
}
```

**Required fields:**
- `$schema` - Must be `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`
- `name` - Lowercase, 1-64 chars, only `a-z`, `0-9`, `-`, `.`. No consecutive `--` or `..`. Must start/end alphanumeric.

**Optional metadata fields:**
- `version` - Semantic Versioning recommended
- `description` - Short description
- `author` - Object with `name`, `email`, `url` (all optional strings)
- `homepage` - Documentation URL
- `repository` - Source repo URL
- `license` - SPDX identifier recommended
- `keywords` - Array of search/discovery tags
- `extensions` - Client-specific data keyed by reverse-domain namespace

The schema defines a fixed set of top-level fields; unknown fields are reported and ignored but do not invalidate the manifest.

## skills/ (Agent Skills)

Each immediate subdirectory of `skills/` containing a `SKILL.md` file is one skill. Skills follow the [Agent Skills specification](https://agentskills.io/specification). Clients do not recursively search deeper descendants.

### SKILL.md Format

```markdown
---
name: "my-skill"
description: "What this skill does. Use when the user needs X."
license: "MIT"
compatibility: "Works with Kiro, Claude Code, Cursor"
metadata:
  author: "your-name"
  version: "1.0.0"
---

# My Skill

## Overview
What this skill does and when to use it.

## Prerequisites Checklist
- [ ] Requirement 1
- [ ] Requirement 2

## Step-by-Step Guide

### 1. First Step
Instructions with code examples...

## Troubleshooting

### Error: "common error"
**Solution:** How to fix it.
```

**Required frontmatter fields:**
- `name` - Lowercase with hyphens, 1-64 chars, must match directory name exactly
- `description` - Max 1024 chars, start with verb, include when to use

**Optional frontmatter fields:**
- `license` - SPDX identifier
- `compatibility` - Environment requirements (max 500 chars)
- `metadata` - Arbitrary key-value pairs (author, version, created, etc.)
- `allowed-tools` - Experimental glob patterns for tool restrictions

### Skill Subdirectories

All optional:

| Directory | Purpose | Guidelines |
|-----------|---------|-----------|
| `scripts/` | Executable helper scripts | Any language, < 500 lines each |
| `references/` | Additional documentation | API refs, extended examples, checklists |
| `assets/` | Templates, config files | Static resources referenced from SKILL.md |

Reference files from SKILL.md using relative paths: `See [API reference](references/api.md)`

### Size Guidelines

| Component | Recommendation | Rationale |
|-----------|---------------|-----------|
| SKILL.md | 400-800 lines | Lightweight discovery and loading |
| Individual scripts | < 500 lines | Easy to understand and modify |
| Total skill directory | < 2 MB | Quick download and indexing |

Move large reference materials to external repositories if needed.

## mcp.json (MCP Servers)

Optional. Configures MCP servers the plugin provides.

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@example/mcp-server"],
      "env": {
        "CONFIG": "${PLUGIN_ROOT}/config.json"
      }
    }
  }
}
```

**Required fields:**
- `$schema` - Must be `https://agent-plugins.org/schemas/1.0.0/mcp.schema.json`
- `mcpServers` - Object with named server entries

**Server transport types:**

### stdio

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `"stdio"` | Yes | Selects stdio transport |
| `command` | string | Yes | Single executable token (bare name or `./` relative) |
| `args` | string[] | No | Arguments passed to executable |
| `env` | object of strings | No | Environment variables (cannot contain `PLUGIN_ROOT` or `PLUGIN_DATA` keys) |
| `cwd` | string | No | Working directory (must start with `./`, `${PLUGIN_ROOT}`, or `${PLUGIN_DATA}`) |

- `command` must be a single token, not a shell command string
- Bare names resolve via platform executable search
- Plugin-relative paths (`./bin/server`) resolve against plugin root
- When `cwd` is omitted, the plugin root is used

### streamable-http

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `"streamable-http"` | Yes | Selects Streamable HTTP transport |
| `url` | string | Yes | Absolute HTTP/HTTPS URL (HTTPS required for non-loopback) |
| `headers` | object of strings | No | Fixed HTTP headers (no secrets, no expansion) |

### sse (Legacy)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `"sse"` | Yes | Selects deprecated HTTP+SSE transport |
| `url` | string | Yes | Absolute HTTP/HTTPS URL |
| `headers` | object of strings | No | Fixed HTTP headers |

### Loading Rules

- Invalid `mcp.json` (bad JSON, unsupported schema version, schema mismatch with plugin.json) disables MCP for that plugin but does not prevent other components from loading
- Invalid individual server entries are skipped; other servers continue loading
- Unsupported transport types are skipped
- Connection failures are non-fatal to other components

## Environment Variables and Placeholder Expansion

Clients provide two variables to stdio subprocesses:

| Variable | Purpose | Contents |
|----------|---------|----------|
| `${PLUGIN_ROOT}` | Bundled read-only files | Absolute path to plugin directory |
| `${PLUGIN_DATA}` | Persistent writable state | Absolute path to client-managed data directory |

**Expansion applies to:** `args` elements, `env` values, `cwd` string

**Expansion does NOT apply to:** `command`, `url`, header names/values, `env` keys

Expansion is single-pass, non-recursive. Unrecognized placeholder-like text remains literal. No other placeholder or environment-variable expansion is performed.

**Use `PLUGIN_ROOT` for:** referencing bundled scripts, binaries, config files that ship with the plugin.

**Use `PLUGIN_DATA` for:** installed dependencies, generated code, caches, persistent state that survives plugin updates.

## Client Extensions

Client-specific behavior goes in reverse-domain namespaces. Agent Plugins assigns no portable semantics to extension data.

**In plugin.json:**
```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "my-plugin",
  "extensions": {
    "dev.kiro": {
      "powerCategory": "development"
    }
  }
}
```

**As a directory:**
```
my-plugin/
├── plugin.json
├── skills/...
└── dev.kiro/
    └── hooks/
```

Clients ignore extension namespaces they don't implement without validating their contents.

## Mapping: Kiro Powers to Agent Plugins

| Kiro Power (old) | Agent Plugin (new) | Notes |
|------------------|-------------------|-------|
| POWER.md frontmatter | `plugin.json` | name, description, keywords, author move here |
| POWER.md body | `skills/*/SKILL.md` | Split into discrete skills |
| `steering/*.md` | `skills/*/references/*.md` or separate skills | Depends on independence |
| `mcp.json` | `mcp.json` with `$schema` + `type` per server | Add schema ref and transport type |
| N/A | `skills/*/scripts/` | Executable helper scripts |
| N/A | `skills/*/assets/` | Templates and configs |
| N/A | `extensions` in plugin.json | Client-specific metadata |
| N/A | `com.client.name/` directory | Client-specific files |

## Best Practices

### Naming
- Plugin names: lowercase, hyphens/periods, 1-64 chars (`my-plugin`, `acme.tools`)
- Skill names: match directory name exactly, lowercase with hyphens
- Keep names descriptive but concise

### Description Writing
- Start with a verb: "Generate...", "Monitor...", "Deploy..."
- Include when to use it: "Use when uploading datasets or creating cards."
- Max 1024 chars for skill descriptions

### Skill Organization
- One skill per concern. Don't lump unrelated workflows into one skill.
- Keep SKILL.md focused (400-800 lines). Move heavy reference to `references/`.
- Include copy-paste-ready code examples in fenced blocks.
- Use checklists for prerequisites.

### MCP Configuration
- Always include the `$schema` field
- Always include `type` on each server entry
- Use `${PLUGIN_ROOT}` for bundled files, `${PLUGIN_DATA}` for generated/cached state
- Never embed secrets in `env` or `headers`

### Keywords
- Use 5-7 specific keywords that match how users search
- Avoid overly broad terms ("test", "api", "data") that cause false activations
- Include the tool/service name and specific domain terms

## References

- [Agent Plugins Specification v1.0.0](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md)
- [Agent Plugins Website](https://agent-plugins.org/)
- [Plugin Manifest Schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json)
- [MCP Configuration Schema](https://agent-plugins.org/schemas/1.0.0/mcp.schema.json)
- [Agent Skills Specification](https://agentskills.io/specification)
- [Kiro Powers Documentation](https://kiro.dev/docs/powers/)
