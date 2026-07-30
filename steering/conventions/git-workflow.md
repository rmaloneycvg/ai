# Git Workflow Conventions

## Why This Exists

Without a standardized Git workflow, microservice monorepos with submodules devolve into inconsistent branching, unreadable commit histories, and merge conflicts that compound across services. This document defines the single source of truth for branching strategy, conventional commits, PR conventions, rebase practices, hotfix flows, and CI promotion — so every developer and agent follows the same playbook.

---

## Branching Model

```
prod ← staging ← dev ← feature branches
                      ← hotfix/* (branches from prod, cherry-picks down)
```

### Branch Purposes

| Branch | Purpose | Accepts PRs From | Deploys To |
|--------|---------|-----------------|------------|
| `prod` | Production-ready code | `hotfix/*` only | Production |
| `staging` | Pre-production validation | Auto-promoted from `dev` | Staging |
| `dev` | Integration branch | `feat/*`, `fix/*`, `chore/*`, etc. | Development |
| `feat/*` | Feature development | — | — |
| `fix/*` | Bug fixes | — | — |
| `hotfix/*` | Emergency prod fixes | — | — |

### Rules

- **Never commit directly** to `prod`, `staging`, or `dev`
- Feature branches always branch from `dev`
- Hotfix branches always branch from `prod`
- All PRs target `dev` unless it's a hotfix (targets `prod`)
- Branches are deleted after merge

---

## CI Auto-Promotion

```
feature branch → PR → dev → [CI green] → staging → [CI green] → prod
```

| Trigger | Action | Gate |
|---------|--------|------|
| PR merged to `dev` | CI runs tests + lint + build | Must pass all checks |
| All `dev` CI green | Auto-merge to `staging` | No manual approval needed |
| All `staging` CI green | Auto-merge to `prod` | No manual approval needed |
| CI fails at any stage | Promotion halts | Fix required on `dev` |

### Promotion Implementation

- CI pipeline detects successful build on `dev` → creates fast-forward merge to `staging`
- CI pipeline detects successful build on `staging` → creates fast-forward merge to `prod`
- If fast-forward is not possible (divergence), CI alerts and blocks — manual intervention required
- Rollback: revert the offending commit on `dev`, which cascades through promotion

---

## Submodule Strategy (Independent Lifecycle)

Each microservice is a Git submodule with its own branching and release lifecycle.

### Parent Repo Responsibilities

- Tracks which submodule commit each environment uses (pinned versions)
- Submodule pointer updates are commits in the parent repo: `build(submodules): update service-name to v1.2.3`
- Parent repo has its own `prod`/`staging`/`dev` branches — submodule pointers differ per branch

### Submodule Repo Responsibilities

- Follows the same branching model independently (prod/staging/dev)
- Tags releases with semver: `v1.2.3`
- CI within the submodule runs its own test suite
- Parent repo CI runs integration tests across pinned submodule versions

### Updating a Submodule

```bash
cd services/payment-service
git checkout dev && git pull
cd ../..
git add services/payment-service
git commit -m "build(submodules): update payment-service to <commit-sha>"
```

---

## Conventional Commit Types

Source: https://www.bavaga.com/blog/2025/01/27/my-ultimate-conventional-commit-types-cheatsheet/

| Type | Purpose | Example |
|------|---------|---------|
| `feat` | New feature or functionality | `feat(auth): add OAuth2 PKCE flow` |
| `fix` | Bug fix | `fix(api): handle null response from payment gateway` |
| `chore` | Maintenance, routine tasks | `chore: update .gitignore for IDE files` |
| `perf` | Performance improvements | `perf(db): add index on users.email` |
| `docs` | Documentation | `docs: update API endpoint examples` |
| `build` | Build process or dependencies | `build(deps): upgrade express to v4.18.1` |
| `revert` | Revert a previous commit | `revert: "feat: add social login"` |
| `style` | Code formatting only (no logic change) | `style: reformat with prettier` |
| `refactor` | Code restructuring without behavior change | `refactor: extract validation into shared util` |
| `ci` | CI/CD configuration | `ci: add security scan step in pipeline` |
| `test` | Tests | `test(auth): add integration tests for token refresh` |
| `hotfix` | Emergency fix for prod (ONLY on `hotfix/*` branches) | `hotfix(payments): fix timeout on large transactions` |

### Commit Message Format

```
<type>(<optional-scope>): <description>

[optional body — explains WHY, not WHAT]

[optional footer]
BREAKING CHANGE: <explanation>
Refs: TICKET-123
```

### Rules

- **Subject line:** max 72 characters, imperative mood ("add" not "added"), no period at end
- **Scope:** auto-detected from common path prefix of staged files (e.g., `src/auth/` → scope `auth`)
- **Body:** wrapped at 72 characters, explains motivation not implementation
- **Footer:** `BREAKING CHANGE:` for breaking API changes, `Refs:` for ticket references
- **`hotfix` type** is ONLY valid on `hotfix/*` branches — hook rejects it elsewhere

### Non-Conforming Message Rewrite

During squash operations, messages that don't follow conventional format are rewritten:

| Original Message | Rewritten As |
|-----------------|--------------|
| `fixed the bug` | `fix: fixed the bug` |
| `WIP` | (dropped — squashed into parent commit) |
| `typo` | (dropped — squashed into parent commit) |
| `updated tests` | `test: updated tests` |
| `refactoring stuff` | `refactor: refactoring stuff` |
| `added new endpoint` | `feat: added new endpoint` |

Heuristic: scan message for keywords (`fix`, `add`, `update`, `test`, `refactor`, `docs`). If no match, prompt user.

---

## Branch Naming Convention

### Format

```
<type>/<TICKET-ID>-<kebab-case-description>    # With ticket system
<type>/<kebab-case-description>                  # Without ticket system
```

### Valid Branch Type Prefixes

Same as conventional commit types: `feat`, `fix`, `chore`, `perf`, `docs`, `build`, `revert`, `style`, `refactor`, `ci`, `test`, `hotfix`

### Examples

```
feat/PROJ-123-add-user-authentication
fix/BUG-456-null-pointer-in-payment-handler
hotfix/INC-789-payment-timeout-fix
chore/cleanup-unused-imports
docs/update-api-documentation
```

### Validation Rules

- Must start with a valid type prefix followed by `/`
- Description is kebab-case (lowercase, hyphens)
- Ticket ID is uppercase letters + hyphen + digits (e.g., `PROJ-123`, `BUG-456`)
- Maximum branch name length: 80 characters
- No special characters beyond hyphens and forward slash

---

## Ticket System Integration

### Environment Variable

```bash
# Set in .zshrc or shell profile
export TICKET_SYSTEM_URL="https://mycompany.atlassian.net"
```

### Behavior Matrix

| `TICKET_SYSTEM_URL` Set? | Branch Naming | PR Title | Commit Footer |
|--------------------------|---------------|----------|---------------|
| Yes | `type/TICKET-123-desc` required | `type(scope): TICKET-123 desc` | `Refs: TICKET-123` |
| No | `type/desc` (no ticket required) | `type(scope): desc` | No refs required |

### Ticket System Detection

| URL Pattern | System | Ticket Format |
|-------------|--------|---------------|
| `*.atlassian.net` | Jira | `PROJ-123` |
| `linear.app` | Linear | `TEAM-123` |
| `app.shortcut.com` | Shortcut | `sc-12345` |
| `*.youtrack.cloud` | YouTrack | `PROJ-123` |
| Other | Generic | `[A-Z]+-\d+` pattern |

### PR Title Format

```
type(scope): TICKET-123 description     # With ticket
type(scope): description                 # Without ticket
```

---

## PR Workflow

### Creating a PR

1. Feature branch must be rebased onto target (`dev`) with clean history
2. All commits must follow conventional format
3. PR title follows the naming convention (with ticket if configured)
4. PR description links to ticket (auto-generated from branch name)

### PR Preparation (Squash + Rebase)

The `git-prepare-pr` script enforces this sequence:

1. **Squash first** — Group commits by type, squash each group into one commit
2. **Rewrite non-conforming messages** — Any message not matching conventional format is rewritten or user is prompted
3. **Rebase onto target** — After squashing, rebase the clean commits onto the target branch
4. **Force-push** — Use `--force-with-lease` to update the remote branch

### At Merge Time (Final Validation)

The `git-merge-pr` script validates:

1. Branch is rebased (no merge commits, linear with target)
2. All commit messages conform to conventional format
3. CI is green
4. Branch name matches conventions

### Merge Strategy

- Always **rebase + fast-forward** (no merge commits) for feature → dev
- Result: perfectly linear git history on `dev`

---

## Rebase Best Practices

### Squash Before You Rebase

If a feature branch has N intermediate commits, rebasing against the target replays all N individually. If the target diverged, you resolve conflicts N times.

**Rule:** Always squash WIP/intermediate commits into logical units BEFORE rebasing against the target.

```
# Bad: 15 WIP commits rebased against diverged target = up to 15 conflict rounds
# Good: squash to 2 logical commits first, then rebase = max 2 conflict rounds
```

### Enable `git rerere`

Reuse Recorded Resolution — Git saves conflict resolutions and auto-applies them if the same conflict appears again.

```bash
git config --global rerere.enabled true
```

- Enabled automatically by `setup.sh`
- Saved in `.git/rr-cache/`
- Critical for rebase workflows where the same file conflicts across multiple commits

### The Rebase Resolution Loop

When a rebase pauses with conflicts:

```
1. Resolve → Edit conflicted files, remove <<<<<<< markers
2. Stage   → git add <resolved-files>
3. Continue → git rebase --continue
4. Repeat  → If next commit conflicts, go to step 1
```

**NEVER** run `git commit` during rebase resolution. Only `git add` + `git rebase --continue`.

**Escape hatch:** `git rebase --abort` — cancels everything, restores branch to pre-rebase state.

### The Golden Rule: Never Rebase Shared Code

- Only rebase your own local, unpushed work
- If a branch has been pushed and others pulled it: use `git merge` instead
- After squash+rebase on your own feature branch: force-push with `--force-with-lease` is expected
- Once merged to `dev`/`staging`/`prod`: NEVER rebase those branches

### Force-Push Safety

- **Always** use `--force-with-lease` instead of `--force`
- `--force-with-lease` fails if someone else pushed to the remote branch since your last fetch
- Prevents accidentally overwriting a colleague's work

---

## Hotfix Flow

### When to Use

- Critical bug in production that can't wait for the normal dev → staging → prod cycle
- Security vulnerability requiring immediate patch
- Data corruption or service outage fix

### Procedure

```
1. Branch from prod     → hotfix/TICKET-123-description
2. Fix + commit         → hotfix(scope): description
3. PR to prod           → Reviewed, CI green, merged
4. Cherry-pick to staging → git cherry-pick <sha>
5. Cherry-pick to dev     → git cherry-pick <sha>
6. Delete hotfix branch
```

### Rules

- `hotfix:` commit type is ONLY valid on `hotfix/*` branches
- Hotfix branches MUST branch from `prod` (never from dev or staging)
- After merge to prod, MUST be cherry-picked to staging and dev to prevent regression on next promotion
- Cherry-pick conflicts require manual resolution — staging/dev may have diverged from prod
- If cherry-pick fails, create a follow-up fix on `dev` rather than forcing the cherry-pick

---

## Heuristic Mapping (File Path → Commit Type)

Used by `git-commit` to auto-detect commit types from changed file paths.

| Path Pattern | Detected Type | Confidence |
|-------------|---------------|------------|
| `tests/`, `**/test_*`, `**/*_test.*`, `*.test.*`, `*.spec.*` | `test` | High |
| `.github/workflows/`, `.gitlab-ci*`, `Jenkinsfile`, `.circleci/`, `bitbucket-pipelines.yml` | `ci` | High |
| `docs/`, `*.md` (non-root), `CHANGELOG*`, `LICENSE` | `docs` | High |
| `Dockerfile*`, `docker-compose*`, `k8s/`, `helm/`, `Tiltfile`, `*.tf` | `build` | High |
| `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml` (deps section only) | `build` | Medium |
| `*.css`, `*.scss`, `*.less` (formatting only, no logic) | `style` | Medium |
| `scripts/`, `Makefile`, `.gitignore`, `.editorconfig`, `.prettierrc`, `.eslintrc*` | `chore` | Medium |
| `src/` (new files — `git status` shows `A` or `??`) | `feat` | Medium |
| `src/` (modified files — `git status` shows `M`) | `fix` or `refactor` | Low (prompt user) |
| Root `README.md` | `docs` | High |
| `*.py`, `*.ts`, `*.go` with "perf" in diff hunks | `perf` | Low (prompt user) |
| Default fallback | Prompt user to select type | — |

### Confidence Levels

- **High:** Auto-assign without prompting (user can still override)
- **Medium:** Auto-assign but highlight in the confirmation table
- **Low:** Present as suggestion, require user confirmation

### Scope Detection

Scope is auto-detected from the common path prefix of files in a commit group:

```
src/auth/login.ts + src/auth/session.ts → scope: auth
src/api/users.ts + src/api/orders.ts    → scope: api
tests/auth/test_login.py                → scope: auth
```

If files span multiple top-level directories, scope is omitted.

---

## Accumulated Changes → Multiple Commits

When uncommitted changes span multiple conventional types, the `git-commit` script creates separate commits for each type:

### Algorithm

1. Run `git status --porcelain` to get all changed files
2. Apply heuristic mapping to assign each file a commit type
3. Group files by assigned type
4. Present the grouping table to the user for confirmation/override
5. For each group (in deterministic order):
   a. Stage only the files in that group
   b. Prompt for commit description
   c. Auto-detect scope from group's file paths
   d. Format message: `<type>(<scope>): <description>`
   e. Validate against conventional format
   f. Commit

### Commit Order

Types are committed in this order (infrastructure first, features last):

1. `ci` — CI changes that affect everything
2. `build` — Build/deps that other changes may depend on
3. `chore` — Housekeeping
4. `docs` — Documentation
5. `style` — Formatting
6. `refactor` — Restructuring
7. `perf` — Performance
8. `test` — Tests
9. `fix` — Bug fixes
10. `feat` — New features

### Idempotency

- If `git status` shows no changes: exit with "Nothing to commit"
- If all changed files map to a single type: create one commit
- Re-running after a successful commit: "Nothing to commit" (clean tree)

---

## Scripts Reference

All scripts live in `scripts/git/` and are Python-based, run via `uv`:

| Entry Point | Script | Purpose |
|-------------|--------|---------|
| `git-branch` | `src/branch.py` | Create/validate branch with naming convention |
| `git-commit` | `src/commit.py` | Auto-group changes, commit per type |
| `git-prepare-pr` | `src/prepare_pr.py` | Squash + rewrite + rebase for PR review |
| `git-merge-pr` | `src/merge_pr.py` | Final validation + merge at merge time |
| `git-hotfix` | `src/hotfix.py` | Full hotfix flow from prod |
| `git-promote` | `src/promote.py` | Manual environment promotion trigger |

### Installation

```bash
cd scripts/git && ./setup.sh
```

This installs git hooks, enables `rerere`, validates prerequisites, and makes entry points available.

---

## Anti-Patterns

- ❌ Committing directly to `prod`, `staging`, or `dev`
- ❌ Merge commits on feature branches (rebase + fast-forward only)
- ❌ Rebasing shared/pushed branches that others have pulled
- ❌ Using `--force` instead of `--force-with-lease`
- ❌ Rebasing against a diverged target without squashing WIP first
- ❌ Running `git commit` during rebase conflict resolution
- ❌ Using `hotfix:` type on non-hotfix branches
- ❌ Skipping cherry-pick cascade after hotfix merge to prod
- ❌ Non-conventional commit messages on `dev`/`staging`/`prod`
- ❌ Branch names without type prefix
- ❌ Multiple unrelated changes in a single commit (split by type)
- ❌ Force-pushing to `prod`, `staging`, or `dev` under any circumstances
- ❌ Ignoring hook rejections (fix the message, don't bypass with `--no-verify`)
