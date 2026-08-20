---
name: "migrate-plugin"
description: "Migrate an existing POWER.md-based Kiro Power to the Agent Plugins v1.0.0 specification. Use when converting a power that uses POWER.md frontmatter and steering files to the plugin.json and skills/ format."
license: "MIT"
metadata:
  author: "Kiro Team"
  version: "1.0.0"
---

# Migrate a POWER.md-Based Power to Agent Plugins

Step-by-step guide for converting an existing Kiro Power (POWER.md format) to the Agent Plugins v1.0.0 standard.

## Overview

This skill converts the old Kiro Power structure into the portable agent-plugins format:

```
Old Kiro Power:                  Agent Plugin:
├── POWER.md          →          ├── plugin.json
│   (frontmatter)                ├── skills/
│   (body content)               │   ├── skill-1/
├── mcp.json          →          │   │   ├── SKILL.md
└── steering/         →          │   │   ├── scripts/
    ├── workflow1.md             │   │   └── references/
    └── workflow2.md             │   └── skill-2/
                                 │       └── SKILL.md
                                 └── mcp.json (with $schema + type)
```

## Prerequisites Checklist

- [ ] Existing power with POWER.md (and optionally mcp.json, steering/)
- [ ] Access to read all existing power files
- [ ] Understanding of what the power does and its workflows

## Step-by-Step Guide

### 1. Read the Existing Power

Read all files to understand what needs migrating:

1. Read `POWER.md` - note the frontmatter fields and body sections
2. Read `mcp.json` if it exists - note server configurations
3. Read all `steering/*.md` files - note independent workflows

Identify:
- The power's name, description, keywords, author (from frontmatter)
- Major sections/workflows in the body (each may become a skill)
- Steering files (each independent one may become a skill)
- MCP server configuration details

### 2. Create the Plugin Directory

```bash
mkdir -p {workspace}/powers/{plugin-name}
mkdir -p {workspace}/powers/{plugin-name}/skills
```

**Name validation:** 1-64 chars, only `a-z`, `0-9`, `-`, `.`, no consecutive `--` or `..`, must start and end alphanumeric.

If the old power name doesn't satisfy these rules, adapt it (e.g., remove uppercase, replace underscores with hyphens).

### 3. Convert Frontmatter to plugin.json

Map the POWER.md frontmatter fields:

| POWER.md Frontmatter | plugin.json | Notes |
|---------------------|-------------|-------|
| `name` | `name` | Validate against naming rules |
| `displayName` | `description` (incorporate) | No direct equivalent |
| `description` | `description` | Direct mapping |
| `keywords` | `keywords` | Direct mapping (array of strings) |
| `author` | `author.name` | String becomes object with `name` field |

**Template transformation:**

Given old frontmatter:
```yaml
---
name: "my-power"
displayName: "My Power"
description: "Does something useful"
keywords: ["tool", "workflow"]
author: "John Doe"
---
```

Produce:
```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "my-power",
  "version": "1.0.0",
  "description": "Does something useful",
  "author": {
    "name": "John Doe"
  },
  "keywords": ["tool", "workflow"],
  "license": "MIT"
}
```

**New fields to add:**
- `$schema` - Always required
- `version` - Start at `"1.0.0"` for the migrated version
- `license` - Choose appropriate license
- `repository` - Add if the power has a GitHub repo

**Fields that don't carry over:**
- `displayName` - No equivalent. Incorporate into description if needed.

### 4. Convert Body Content to Skills

The most involved step. POWER.md body and steering files decompose into discrete skills.

#### 4.1: Identify Skill Boundaries

| Existing Content | Becomes |
|-----------------|---------|
| Single focused POWER.md (< 800 lines) | One skill |
| POWER.md with multiple independent sections | Multiple skills (one per section) |
| Each independent `steering/*.md` file | Its own skill |
| Related steering files that share context | One skill with references/ |
| Onboarding/setup section | Skill named `getting-started` or `setup` |
| Troubleshooting section | Included in relevant skill, or separate `troubleshooting` skill |

**Examples:**

A power with `POWER.md` (overview + setup) and `steering/advanced.md`:
```
skills/
├── getting-started/    # from POWER.md setup/overview sections
│   └── SKILL.md
└── advanced/           # from steering/advanced.md
    └── SKILL.md
```

A power with `POWER.md` (everything in one file, < 800 lines):
```
skills/
└── main/              # entire POWER.md body
    └── SKILL.md
```

A power with multiple steering files:
```
skills/
├── web-scraping/      # from steering/web-scraping.md
│   └── SKILL.md
├── e2e-testing/       # from steering/e2e-testing.md
│   └── SKILL.md
└── performance/       # from steering/performance.md
    └── SKILL.md
```

#### 4.2: Write SKILL.md for Each Skill

For each identified skill:

```bash
mkdir -p {workspace}/powers/{plugin-name}/skills/{skill-name}
```

**Transform the content:**

1. **Add frontmatter** - Every SKILL.md needs:
   ```yaml
   ---
   name: "{skill-name}"
   description: "{What it does}. Use when {trigger conditions}."
   license: "MIT"
   metadata:
     author: "{author from old power}"
     version: "1.0.0"
   ---
   ```

2. **Restructure the body:**
   - Add `## Overview` section (from old overview/intro)
   - Add `## Prerequisites Checklist` with checkboxes
   - Convert workflows to `## Step-by-Step Guide` with numbered steps
   - Keep `## Troubleshooting` section
   - Keep `## Best Practices` section

3. **Extract heavy content** if skill exceeds 800 lines:
   - Reference tables, API docs → `references/`
   - Code examples, templates → `assets/`
   - Helper scripts → `scripts/`
   - Link from SKILL.md: `See [API reference](references/api.md)`

#### 4.3: Handle Cross-Cutting Content

Content that applies to all skills (general overview, common config):

1. **Deduplicate into each skill** - If short (< 10 lines), include in each overview
2. **Create a `getting-started` skill** - For shared setup/onboarding
3. **Use references/** - Put shared docs in one skill's references and link from others

### 5. Convert mcp.json

If the old power has mcp.json, it needs two additions:

#### 5.1: Add Schema Reference

Old:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "@example/server"],
      "env": {
        "API_KEY": "API_KEY"
      }
    }
  }
}
```

New:
```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@example/server"],
      "env": {
        "API_KEY": "API_KEY"
      }
    }
  }
}
```

#### 5.2: Determine Transport Type

| Old Configuration | Type to Add |
|------------------|-------------|
| Has `command` (and optionally `args`, `env`, `cwd`) | `"stdio"` |
| Has `url` pointing to HTTP endpoint | `"streamable-http"` |
| Has `url` with SSE endpoint (legacy) | `"sse"` |

#### 5.3: Remove Non-Spec Fields

Remove from mcp.json (these are Kiro-specific):
- `disabled`
- `autoApprove`
- `disabledTools`

If these need to be preserved, put them in plugin.json extensions:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "my-plugin",
  "extensions": {
    "dev.kiro": {
      "disabledTools": ["tool1", "tool2"],
      "autoApprove": ["tool3"]
    }
  }
}
```

#### 5.4: Fix Field Compatibility

- **`command` must be a single token** - If it's a shell string, extract executable and put args in `args`
- **Check `env` keys** - Remove any `PLUGIN_ROOT` or `PLUGIN_DATA` entries
- **Check `cwd`** - Must start with `./`, `${PLUGIN_ROOT}`, or `${PLUGIN_DATA}` if present

### 6. Remove Old Files

Once migration is complete and validated:

- Delete `POWER.md` (replaced by `plugin.json` + `skills/*/SKILL.md`)
- Delete `steering/` directory (content moved to skills)
- Keep `mcp.json` (updated in place with $schema and type)

Or, if creating in a new directory, use the new directory as the power source.

### 7. Validate the Migration

#### Structure Validation

```
{plugin-name}/
├── plugin.json                    # Has $schema, name
├── skills/
│   └── {skill}/
│       └── SKILL.md              # Has name, description in frontmatter
└── mcp.json                       # Has $schema, mcpServers with type
```

#### Content Validation Checklist

- [ ] `plugin.json` has required `$schema` and `name` fields
- [ ] `plugin.json` `name` satisfies naming constraints
- [ ] All skills have `SKILL.md` with `name` and `description` in frontmatter
- [ ] Each skill `name` matches its directory name
- [ ] Each skill `description` starts with a verb and includes when to use
- [ ] SKILL.md files are 400-800 lines (excess moved to references/)
- [ ] `mcp.json` (if present) has `$schema` field
- [ ] Each MCP server entry has a `type` field
- [ ] No Kiro-specific fields remain in mcp.json
- [ ] No files reference paths outside the plugin root
- [ ] No secrets in configuration files
- [ ] All code examples are complete and copy-paste ready

#### Functional Validation

1. Install the new plugin locally via Kiro Powers UI
2. Test that skills trigger for relevant user queries
3. Test MCP tools work (if applicable)
4. Verify all workflows still function end-to-end
5. Compare behavior with the old power to ensure nothing was lost

## Migration Examples

### Example 1: Simple Power (Single POWER.md, No Steering)

**Before:**
```
weather/
├── POWER.md    (frontmatter + all docs in body)
└── mcp.json
```

**After:**
```
weather/
├── plugin.json
├── skills/
│   └── weather/
│       └── SKILL.md    (body content from old POWER.md)
└── mcp.json            (+ $schema + type on each server)
```

### Example 2: Power with Steering Files

**Before:**
```
playwright/
├── POWER.md             (overview + common patterns)
├── mcp.json
└── steering/
    ├── web-scraping.md
    ├── e2e-testing.md
    └── performance.md
```

**After:**
```
playwright/
├── plugin.json
├── skills/
│   ├── web-scraping/
│   │   └── SKILL.md    (from steering/web-scraping.md)
│   ├── e2e-testing/
│   │   └── SKILL.md    (from steering/e2e-testing.md)
│   └── performance/
│       └── SKILL.md    (from steering/performance.md)
└── mcp.json             (+ $schema + type)
```

### Example 3: Knowledge Base Power (No MCP)

**Before:**
```
testing-strategies/
├── POWER.md             (overview/index)
└── steering/
    ├── unit-testing.md
    ├── integration-testing.md
    └── e2e-testing.md
```

**After:**
```
testing-strategies/
├── plugin.json
└── skills/
    ├── unit-testing/
    │   └── SKILL.md
    ├── integration-testing/
    │   └── SKILL.md
    └── e2e-testing/
        └── SKILL.md
```

## Troubleshooting

### Issue: POWER.md body is too large for one skill
**Solution:** Break into multiple skills by workflow area. Each independent section becomes its own skill. Shared setup becomes a `getting-started` skill.

### Issue: Steering file references other steering files
**Solution:** Skills can reference each other using relative paths from the plugin root: `See [related skill](../other-skill/SKILL.md)`. Or consolidate related content into one skill with references/.

### Issue: mcp.json has fields not in the spec
**Solution:** Move Kiro-specific fields (`disabled`, `autoApprove`, `disabledTools`) to `extensions.dev.kiro` in plugin.json. Remove them from mcp.json.

### Issue: Power name has uppercase or underscores
**Solution:** Convert to lowercase with hyphens. `MyPower_Name` becomes `my-power-name`.

### Issue: Single POWER.md under 800 lines
**Solution:** Simplest case. Create one skill with the body as SKILL.md. Frontmatter moves to plugin.json.

## Agent Guidelines

### Process
1. Always read ALL existing files before starting migration
2. Present a migration plan to the user before generating files
3. Show the proposed skill breakdown and get confirmation
4. Generate all files, then validate
5. Offer to test the migrated plugin

### Content Transformation
- Don't just copy-paste. Restructure to fit the SKILL.md format.
- Add proper frontmatter with `name` and `description` to every SKILL.md
- Ensure `description` includes trigger conditions ("Use when...")
- Convert prose overviews to structured sections (Overview, Prerequisites, Steps)
- Extract code into fenced blocks with language tags

### Preserve Intent
- Don't lose workflows or troubleshooting content
- If the old power had tool-disabling logic, preserve it in extensions
- Keep all MCP tool documentation accurate
- Maintain keyword specificity
