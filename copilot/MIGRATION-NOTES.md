# Kiro → GitHub Copilot migration notes

This staging tree (`~/workspace/ai/copilot/`) is a one-time conversion of the Kiro
configuration in `~/workspace/ai/` (agents, skills, steering, hooks, hook scripts,
MCP servers, knowledge bases) into GitHub Copilot equivalents for the **CLI**, the
**VS Code IDE**, and the **cloud coding agent**. It is self-contained and does not
modify the original Kiro sources.

Regenerate everything from source with the converter scripts in this directory
(`convert_steering.py`, `convert_skills.py`, `convert_agents.py`,
`convert_orchestrator.py`, `build_plugin.py`) and validate with `./validate.sh`.

---

## What was produced

| Area | Source | Output | Count |
|---|---|---|---|
| Instructions | `steering/**/*.md` | `.github/instructions/*.instructions.md` | 25 |
| Skills | `skills/**/SKILL.md` | `.github/skills/<name>/SKILL.md` | 13 |
| Simple agents | `agents/*.json` | `.github/agents/*.agent.md` | 9 |
| Orchestrator | `agents/react-orchestrator.json` | `.github/agents/react-orchestrator.agent.md` | 1 |
| MCP registration | `mcp/mcp-scripts/servers/*.ts` | `.vscode/mcp.json`, `mcp/copilot-cli-mcp.json` | 10 servers |
| Hooks/guards | `hooks/**` | `hooks/`, `.pre-commit-config.yaml`, `.github/workflows/security-guards.yml` | 7 scripts |
| Plugin bundle | all of the above | `plugin/` (Agent Plugins 1.0) | 1 |
| Project instructions | — | `.github/copilot-instructions.md` | 1 |

---

## Format mapping

| Kiro construct | Copilot construct | Notes |
|---|---|---|
| `SKILL.md` (`name`, `description`) | Agent Skill `.github/skills/<name>/SKILL.md` | Near 1:1; portable across CLI/IDE/cloud. |
| Steering (`inclusion: manual`, `fileMatchPattern`) | `*.instructions.md` (`applyTo`) | `fileMatchPattern` array → comma-joined `applyTo`; **now auto-attaches** on matching file edits (net-new). |
| Agent JSON (`prompt`, `tools`, `model`) | `*.agent.md` frontmatter + body | `prompt`→body; `tools`→`tools:`; `model`→`model:`. |
| `crew.availableAgents` | `agents:` allow-list | Explicit list (see gap #5). |
| — (Kiro had none) | `handoffs:` | Net-new guided-workflow buttons on the orchestrator. |
| stdio MCP servers | `.vscode/mcp.json` + CLI `mcpServers` | Server code unchanged; only registration is new. |
| Global PreToolUse hooks | pre-commit + CI | No always-on gate in Copilot (see gap #2). |
| Enrichment hooks | agent-scoped `hooks:` | Local harness/Preview only. |

### Net-new Copilot capabilities seeded from existing content
- **`applyTo` auto-activation** of the 25 instruction files (Kiro steering was manual-only).
- **`context: fork`** on read-heavy skills (`diagnose`, `harvest-debt`, `flywheel`) for isolated subagent execution.
- **`handoffs:`** chain on `react-orchestrator` (architecture → scaffold → styling → testing).
- **Agent Plugin** bundling everything into one installable unit (`plugin/`).

---

## Documented gaps (no clean Copilot equivalent)

1. **`config/permissions.yaml` deny/ask/allow engine.** Kiro's restrictiveness-ranked
   policy (SSRF blocks, recursive-delete carve-outs, secret-write denials,
   never-legitimate shell) has no Copilot equivalent. Intent is preserved only via
   per-agent `tools:` allow-lists. There is no runtime shell/read interception.

2. **Global PreToolUse guard hooks.** Kiro ran `check-secrets`, `guard-secret-reads`,
   `guard-config-writes`, `guard-destructive-commands` on *every* tool call. Copilot
   agent-scoped `hooks:` run only in the VS Code **Local** harness (Preview) and do
   not cover the CLI or cloud agent. Mitigations shipped here:
   - `check-secrets` and `guard-config-writes` → `.pre-commit-config.yaml` + CI
     (`.github/workflows/security-guards.yml`, using `check-secrets-precommit.sh`).
   - `guard-secret-reads` / `guard-destructive-commands` guarded *execution-time* tool
     calls; git hooks cannot intercept a mid-session read or `rm -rf`. Mitigation:
     scope each agent's `tools:` (done) and withhold `runCommands` from agents that
     don't need it. See `hooks/README.md`.
   - **`guard-config-writes.sh` is Kiro-specific and needs manual re-scoping.** Its
     purpose was protecting Kiro's own enforcement surface (`~/.kiro/settings/`,
     `permissions.yaml`, `~/.kiro/hooks/`, `~/.kiro/agents/`) — paths that do not exist
     in Copilot. It is copied verbatim (retaining `.kiro` references in its guard logic
     and comments) so nothing is silently broken, but it will not meaningfully guard a
     Copilot setup until you re-point its protected-path list at whatever config you
     want to protect. It is intentionally **commented out** in `.pre-commit-config.yaml`
     for this reason. `check-secrets` is the guard that ports cleanly and is active.

3. **Per-subagent / per-stage model overrides.** Kiro's orchestrator assigned a model
   per pipeline stage. Copilot does not support this in `agents:`/`handoffs:`; each
   subagent uses the `model:` in its own `.agent.md`. The model table in the
   orchestrator prompt is now descriptive only.

4. **`model: auto`.** No Copilot equivalent — omitted from converted agents (the model
   picker's current selection applies). `claude-sonnet-4` → `model: [Claude Sonnet 4]`.

5. **`trustedAgents: ['react-*']` glob trust.** Replaced by the explicit `agents:`
   allow-list on the orchestrator (`react-scaffold`, `react-architecture`,
   `react-styling`, `react-testing`).

6. **Prompt files deprecated for Agent Host.** Skills are used throughout instead of
   `.prompt.md` files (which Copilot Agent Host no longer loads).

7. **Kiro path conventions inside skill/agent bodies.** `.kiro/…` and `~/.kiro/…`
   references were rewritten to `.copilot/…` for consistency (0 residual `.kiro`
   strings). The underlying Kiro *infrastructure* some skills assume still has no
   Copilot equivalent — notably `flywheel` (reads `~/.copilot/sessions/`,
   `permissions.yaml`, `~/.copilot/agents/*.md`) and `design`/`execute` (reference a
   `delivery-workflow` steering doc). These skills will need manual adaptation to
   Copilot's session/agent layout before they function end to end.

8. **MCP server credentials.** The ported servers read connection details from **tool
   parameters** (e.g. `database`, `sql`) or their own backend — not env vars — so no
   secrets appear in the registration files. Supply real credentials per environment;
   never commit them.

### Items requiring manual follow-up
- **`sqlserver-modernization` skill was skipped** — its source `SKILL.md` is empty
  (1 byte) with no `name`/`description`. Its `references/schema-drift.md` exists.
  Author a proper `SKILL.md` to include it.
- **`react-refactor` subagent** is referenced by the orchestrator's Kiro crew but has
  **no source agent definition**. It was dropped from `agents:`/`handoffs:`. Author
  `react-refactor.agent.md` to re-enable that route.
- **`rag` MCP server backend is missing.** `servers/rag.ts` expects
  `~/workspace/ai/rag/` with a `.venv` Python indexer. That directory does not exist.
  The `knowledge/{csharp,mssql,nextjs}` Markdown docs are the intended index source,
  but the Python indexing layer must be built before `rag` will run.
- **Pre-existing MCP test failures** (not caused by this migration; source untouched):
  `vitest run` reports 5 failed / 345 passed / 28 skipped across `jira.test`,
  `linear.test`, and `work-summary` (`renderer`, `kiro-collector`). All failures are
  date/timezone-sensitive (`isSessionOnDate` midnight-spanning cases, `parseSessionMeta`,
  `countCategories`). Servers build and run (the `git` server was smoke-tested live).
- **Kiro-only frontmatter keys** (`allowed-tools`, `metadata`) remain in the
  `diagram-spec` and `resume-content-writer` skills. Copilot ignores them; harmless.

---

## Deployment recipes

### GitHub Copilot CLI
- **Skills:** copy `.github/skills/*` into `~/.copilot/skills/` (or install the plugin —
  see below).
- **Agents:** copy `.github/agents/*.agent.md` into `~/.copilot/agents/`.
- **MCP:** merge `mcp/copilot-cli-mcp.json` (`mcpServers` object) into your CLI MCP
  config.
- **Guards:** run `pre-commit install` in each repo you work in.

### VS Code IDE (Copilot)
- Drop the entire `.github/` directory into your repository root. Instructions,
  skills, and agents are discovered automatically.
- Copy `.vscode/mcp.json` into your repo's `.vscode/` (or merge into an existing one).
- Enable settings as needed: `chat.useHooks` (for agent-scoped enrichment hooks),
  `github.copilot.chat.organizationInstructions.enabled` (org instructions).

### Cloud coding agent
- Ensure `.github/copilot-instructions.md` and `.github/instructions/*` are committed
  to the repo; the cloud agent uses them on issues/PRs.
- Skills and agents under `.github/` are also picked up.

### As an Agent Plugin (all surfaces)
The `plugin/` directory is a conformant **Agent Plugins 1.0** package:
```
plugin/
  plugin.json                 # $schema = agent-plugins 1.0
  skills/                     # portable
  mcp.json                    # portable
  com.github.copilot/
    agents/                   # Copilot custom agents
    hooks/hooks.json          # enrichment hooks (SessionStart, UserPromptSubmit)
  scripts/                    # referenced via ${PLUGIN_ROOT}
```
- **CLI:** install from a git URL / marketplace; plugins land in
  `~/.copilot/installed-plugins/`.
- **VS Code:** `Chat: Install Plugin From Source` (git URL), or register a local path
  with `chat.pluginLocations`.
- Bump `plugin.json` `version` on changes.

---

## Validation

`./validate.sh` checks the whole tree: instruction `applyTo` presence, skill
`name`/dir/charset/description rules, agent `name`/`description` and that every
`agents:`/`handoffs.agent` reference resolves, and that all MCP JSON parses.
