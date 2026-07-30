---
name: git-workflow
description: Use when performing Git operations following the team's branching strategy — creating branches, making conventional commits, preparing PRs with squash/rebase, executing hotfix flows, or managing submodule versioning in microservice monorepos. NOT for deploying (use deploy) or CI pipeline configuration files (use the ci type in conventional commits directly).
---

# Git Workflow

## Role & Tone

Act as a senior platform engineer specializing in Git workflow automation. Be concise and script-oriented. Prefer running existing standard scripts over writing ad-hoc commands. Ask for confirmation before any force-push or history-rewriting operation.

## Environment Scope

**write+execute** — Runs Python scripts from `scripts/git/` that execute git commands (commit, branch, rebase, cherry-pick). Writes no application code. May force-push after explicit user approval. Lists all destructive commands before execution.

## Workflow

1. **Check Existing State** — Run `git status`, identify current branch, determine if inside a submodule or parent repo. If working tree is clean and no operation is pending, report "Nothing to do" and stop.
2. **Determine Operation** — Based on user request, select the appropriate script:
   - Creating a branch → `uv run git-branch`
   - Committing changes → `uv run git-commit`
   - Preparing a PR → `uv run git-prepare-pr`
   - Merging a PR → `uv run git-merge-pr`
   - Hotfix workflow → `uv run git-hotfix`
   - Promoting between environments → `uv run git-promote`
3. **Validate Prerequisites** — Ensure `scripts/git/` is set up (`setup.sh` has been run). Check branch naming matches conventions. If branch name is non-conforming, prompt user to rename or provide ticket/type info.
4. **Execute Script** — Run the selected script with appropriate arguments. Present interactive prompts for confirmation (change grouping, commit messages, squash targets).
5. **Verify** — Confirm the operation completed: check `git log`, branch state, and commit message format. If verification fails, enter failure recovery.
6. **Report** — Summarize what was done: commits created, branches modified, PR title suggested.

### Failure Recovery (max 3 retries)

5a. **Diagnose** — Read git error output. Common issues: merge conflicts (rebase), hook rejection (bad message format), detached HEAD (submodule state).
5b. **Fix** — For conflicts: follow the Rebase Resolution Loop (resolve → `git add` → `git rebase --continue`). For hook rejection: suggest conforming message. For detached HEAD: checkout appropriate branch.
5c. **Re-verify** — Run verification again.
5d. **Escalate** — After 3 failures, show full error context + `git reflog` state, ask user for direction. Offer `git rebase --abort` as the escape hatch.

### Rollback

If user cancels mid-operation or result is unwanted:
1. Use `git reflog` to identify the pre-operation state
2. `git reset --hard <ref>` to restore (confirm with user first — destructive)
3. If branches were created, offer to delete them
4. If force-push already happened, warn that remote history was altered and provide the reflog ref for team recovery
5. Report what was reverted

## Standard Scripts Reference

All scripts live in `scripts/git/` and are run via `uv run <entry-point>`:

| Command | Script | Purpose |
|---------|--------|---------|
| `uv run git-branch` | `src/branch.py` | Create branch with naming convention |
| `uv run git-commit` | `src/commit.py` | Auto-group changes, commit per type |
| `uv run git-prepare-pr` | `src/prepare_pr.py` | Squash + rewrite + rebase for PR |
| `uv run git-merge-pr` | `src/merge_pr.py` | Final validation + merge |
| `uv run git-hotfix` | `src/hotfix.py` | Hotfix flow from prod |
| `uv run git-promote` | `src/promote.py` | Manual environment promotion |

## Branching Strategy

```
prod ← staging ← dev ← feature branches
                      ← hotfix/* (branches from prod, cherry-picks down)
```

- **Feature development:** branch from `dev`, PR back to `dev`
- **Auto-promotion:** CI promotes green `dev` → `staging` → `prod`
- **Hotfix:** branch from `prod`, PR to `prod`, cherry-pick to `staging` then `dev`
- **Submodules:** each microservice has independent lifecycle; parent repo tracks pinned versions

## Rebase Best Practices

### Squash Before You Rebase (The Ultimate Time-Saver)

If a feature branch has many intermediate commits (wip, fixed typo, actually fixing bug), rebasing against the target means Git re-applies each commit individually. If the target changed, you resolve conflicts N times — once per commit.

**The rule:** Before rebasing against the target branch, squash messy commits into logical units first.

- Fewer commits = fewer replays = fewer conflict interruptions
- `git-prepare-pr` enforces this: squash per type FIRST, then rebase onto target
- Never rebase a branch with 5+ unsquashed WIP commits against a diverged target

### Enable `git rerere` (Reuse Recorded Resolution)

`rerere` watches as you resolve conflicts and saves solutions. If the same conflict appears again during multi-commit rebase, Git auto-applies your previous fix.

```bash
git config --global rerere.enabled true
```

- `setup.sh` enables this automatically during installation
- Critical for rebase-heavy workflows where the same file conflicts across multiple commits
- Saved resolutions persist in `.git/rr-cache/`

### The Rebase Resolution Loop

When Git pauses a rebase with conflicts, follow this exact loop:

1. **Resolve** — Open conflicted files, remove `<<<<<<<` markers, make code correct
2. **Stage** — `git add <resolved-files>` to mark as resolved
3. **Continue** — `git rebase --continue` (Git packages the commit and moves to next)
4. **Repeat** — If next commit also conflicts, repeat steps 1-3

**Critical:** Do NOT run `git commit` during rebase conflict resolution. Only `git add` + `git rebase --continue`.

**Escape hatch:** `git rebase --abort` cancels the entire operation and restores the branch to its pre-rebase state. Use when resolutions are going wrong.

### The Golden Rule: Never Rebase Shared Code

Rebasing rewrites commit history (creates new commit IDs). Only rebase your own local, unpushed work.

- If a branch has been pushed and others have pulled it, use `git merge` instead
- `git-prepare-pr` checks: if the branch has been pushed and has remote tracking with other contributors, it WARNS and asks for confirmation
- After squash+rebase on your own feature branch, force-push is expected (with `--force-with-lease` for safety)
- Once merged to `dev`/`staging`/`prod`, NEVER rebase those branches

## Conventional Commit Types

Valid types: `feat`, `fix`, `chore`, `perf`, `docs`, `build`, `revert`, `style`, `refactor`, `ci`, `test`, `hotfix`

- `hotfix` type is ONLY valid on `hotfix/*` branches
- Format: `<type>(<optional-scope>): <description>`
- Scope auto-detected from common path prefix of staged files

## Ticket System Integration

- If `TICKET_SYSTEM_URL` is set in environment: branch names and PR titles include ticket references
- If NOT set: fully permissive — no ticket references required, conventional commits still enforced
- Branch format with ticket: `<type>/<TICKET-123>-<kebab-description>`
- PR title with ticket: `type(scope): TICKET-123 description`

## Guardrails

- NEVER force-push without explicit user confirmation and showing what will be overwritten
- NEVER commit directly to `prod`, `staging`, or `dev` — always use feature branches or hotfix branches
- NEVER skip commit-msg hook validation — if hook rejects, fix the message
- NEVER use `hotfix:` type on non-hotfix branches
- NEVER squash/rebase commits that have already been pushed to a shared branch without user approval
- NEVER rebase a branch that other developers have pulled — use merge for shared branches
- NEVER proceed with a merge if the branch has not been rebased onto its target
- NEVER create a branch without validating the naming convention first
- NEVER run destructive git operations (reset --hard, clean -f, branch -D) without listing what will be lost
- NEVER rebase against a diverged target without squashing local WIP commits first
- NEVER run `git commit` during rebase conflict resolution — only `git add` + `git rebase --continue`
- ALWAYS use `--force-with-lease` instead of `--force` when force-pushing (prevents overwriting others' work)
- ALWAYS enable `git rerere` in project setup for rebase conflict reuse

## References

- `steering/conventions/git-workflow.md` — Full branching strategy, conventional commit rules, heuristic mapping, squash/rebase procedures
- `scripts/git/PLAN.md` — Implementation plan and task breakdown for the Python scripts

## Precedence

This skill is the authoritative source for ALL Git operations. If other skills (deploy, debug, refactor, etc.) reference git commands incidentally (e.g., `git checkout` for reverting, noting commit SHAs), this skill's conventions and guardrails take precedence for how those git operations are performed.
