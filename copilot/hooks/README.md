# Hooks — Kiro → Copilot mapping

Kiro ran shell hooks on tool/session lifecycle events, configured globally in
`hooks/*.json` and always-on for every agent. Copilot splits this into two very
different capabilities, and **neither is a full replacement**:

| Kiro hook | Trigger | Category | Copilot destination |
|---|---|---|---|
| `01-check-secrets` | PreToolUse (writes) | **security guard** | pre-commit + CI (`check-secrets-precommit.sh`) |
| `02-guard-secret-reads` | PreToolUse (reads) | **security guard** | pre-commit/CI + tool allow-lists (no read-time gate) |
| `03-guard-config-writes` | PreToolUse (shell) | **security guard** | pre-commit (`guard-config-writes.sh`) |
| `guard-destructive-commands` | (script) | **security guard** | pre-commit / manual (no shell-intercept gate) |
| `10-validate-environment` | SessionStart | context enrichment | agent-scoped `hooks:` (Local/Preview) |
| `20-git-context` | UserPromptSubmit | context enrichment | agent-scoped `hooks:` (Local/Preview) |
| `50-rtk-compress` | PreToolUse (shell) | optimization | agent-scoped `hooks:` (Local/Preview) |

## Security guards → pre-commit + CI (recommended)

Copilot has **no always-on PreToolUse gate**. Agent-scoped `hooks:` only run in
the VS Code **Local** harness (Preview) — they do not fire for the Copilot CLI or
the cloud coding agent. So the guards that actually block dangerous actions are
moved to git-level enforcement, which protects the repo no matter which agent
made the change:

- `.pre-commit-config.yaml` — runs `check-secrets` on commit (`guard-config-writes`
  is included but commented out — it is Kiro-specific and needs re-scoping first).
- `.github/workflows/security-guards.yml` — runs the secret scan in CI on PR/push.
- `hooks/scripts/check-secrets-precommit.sh` — file-scanning port of the Kiro
  `check-secrets` logic (same patterns), for pre-commit/CI use.

Install locally:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

> **Gap:** `guard-secret-reads` and `guard-destructive-commands` guarded *agent
> tool calls at execution time*. Git-level hooks cannot intercept an agent
> reading a secret or running `rm -rf` mid-session. Mitigate by scoping each
> agent's `tools:` allow-list (already done in `.github/agents/*.agent.md`) and
> by not granting `runCommands` to agents that don't need it. See MIGRATION-NOTES.md.

## Context-enrichment hooks → agent-scoped `hooks:` (Local/Preview only)

The enrichment scripts still work as agent-scoped hooks **in the VS Code Local
harness**. Add a `hooks:` block to any `.agent.md` frontmatter. Example:

```yaml
---
name: my-agent
description: …
tools: [edit, search, runCommands]
hooks:
  SessionStart:
    - type: command
      command: "./hooks/scripts/validate-environment.sh"
  UserPromptSubmit:
    - type: command
      command: "./hooks/scripts/git-context.sh"
---
```

Requires `chat.useHooks` enabled and a trusted workspace. These hooks are ignored
by the Copilot CLI and cloud agent — run the scripts manually there, or rely on
the `git` MCP server for git context.

## Scripts

All original Kiro scripts are copied verbatim into `hooks/scripts/` (with
`.kiro/hooks` paths rewritten to `.copilot/hooks`). They read a Kiro hook-event
JSON on stdin and use exit 0 = allow / exit 2 = block. The `-precommit` variant
scans files instead, for git-level use.
