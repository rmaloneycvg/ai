# Project instructions

This repository's AI configuration was ported from a Kiro setup. Guidance is
organized so Copilot loads only what's relevant to the current task.

## How guidance is organized

- **Path-scoped instructions** live in `.github/instructions/*.instructions.md`
  and attach automatically when you edit a matching file (via each file's
  `applyTo` glob). Examples: React hook rules apply to `**/src/**/*.tsx`,
  Next.js rules to `app/**` routes, security policies to Dockerfiles / nginx /
  auth code. Do not restate these here — they self-attach.
- **Skills** in `.github/skills/` provide task workflows (planning with
  `design`, execution with `execute`, debugging with `diagnose`, etc.). Invoke
  them with `/<skill>` or let Copilot load them by relevance.
- **Custom agents** in `.github/agents/` provide role-specialized personas
  (e.g. `spec-planner` is read-only/plan-only; `react-orchestrator` delegates to
  react subagents via handoffs).

## Always-on conventions

- **Security first.** Never commit secrets; use env vars / a secret store. The
  repo enforces this with a pre-commit hook and a CI secret scan
  (`.pre-commit-config.yaml`, `.github/workflows/security-guards.yml`). Prefer
  parameterized queries, per-origin CORS, non-root containers — see
  `security-policies.instructions.md` (auto-applies to security-relevant files).
- **Least privilege.** Agents declare a minimal `tools:` allow-list. Read-only
  agents (planners/reviewers) have no `edit`/`runCommands`.
- **Match existing patterns.** Follow the conventions in the relevant
  `*.instructions.md` for the stack you're touching (React, Next.js, .NET/EF Core).

## Notes

Some capabilities that existed in the original Kiro setup do not map 1:1 to
Copilot. See `MIGRATION-NOTES.md` for the full mapping, known gaps, and
deployment recipes for the Copilot CLI, VS Code IDE, and cloud coding agent.
