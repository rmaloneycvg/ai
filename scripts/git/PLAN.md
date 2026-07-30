# Implementation Plan — Git Workflow Skill (Python + pytest)

## Problem Statement

Create a Kiro skill + supporting Python scripts that enforce a standardized Git workflow for microservice monorepos using submodules. The workflow covers branching strategy (prod/staging/dev with auto-promotion), conventional commits with auto-grouping, PR squash+rebase for linear history, hotfix flows from prod, and optional ticket system integration.

## Requirements

1. Skill file at `skills/git-workflow.md` following the skill schema
2. Python scripts at `scripts/git/` — reusable, idempotent, not regenerated each time
3. Git hooks for passive enforcement (commit-msg validation) — thin shell shims calling Python
4. Independent submodule lifecycle; parent repo tracks pinned versions
5. Conventional commit types: feat, fix, chore, perf, docs, build, revert, style, refactor, ci, test + hotfix tag
6. Auto-detect change groups by path + diff heuristics, present for confirmation, commit each type separately
7. Squash + rebase before review (interactive) + validation at merge time (automated)
8. Non-conforming commit messages rewritten during squash
9. Branch naming: `<type>/<TICKET-ID>-description` when ticket system configured; `<type>/description` when not
10. PR title format linked to ticket system when URL available
11. `TICKET_SYSTEM_URL` in `.zshrc` — fully permissive when absent (no blocking)
12. Hotfix: branch from prod → PR to prod → cherry-pick down to staging/dev
13. CI auto-promotes: green on dev → staging, green on staging → prod
14. All scripts idempotent — no-op with message if nothing to do
15. Python with pytest for unit and integration tests

## File Structure

```
scripts/git/
├── setup.sh              # Thin shell wrapper to install hooks + check Python env
├── pyproject.toml        # Python dependencies (managed by uv)
├── src/
│   ├── __init__.py
│   ├── commit.py         # Auto-detect, group, confirm, commit per type
│   ├── branch.py         # Validate/suggest branch name, create branch
│   ├── prepare_pr.py     # Squash + rewrite + rebase before review
│   ├── merge_pr.py       # Final validation + merge (for CI)
│   ├── hotfix.py         # Hotfix workflow
│   ├── promote.py        # Manual promotion trigger
│   └── lib/
│       ├── __init__.py
│       ├── conventional.py   # Commit type validation + rewrite helpers
│       ├── detect_changes.py # Path + diff heuristic grouping logic
│       ├── ticket.py         # Ticket system URL detection + formatting
│       └── git_ops.py        # Git subprocess wrappers (idempotent)
├── hooks/
│   ├── commit-msg        # Thin shell shim → calls Python validation
│   └── pre-push          # Thin shell shim → calls Python validation
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_conventional.py
    │   ├── test_detect_changes.py
    │   ├── test_ticket.py
    │   └── test_git_ops.py
    └── integration/
        ├── test_commit.py
        ├── test_branch.py
        ├── test_prepare_pr.py
        └── test_hotfix.py
```

## Branching Model

```
prod ← staging ← dev ← feature branches
                      ← hotfix/* (branches from prod, cherry-picks down)
```

- CI auto-promotes: green on dev → staging, green on staging → prod
- PRs only required for: feature → dev, hotfix → prod
- Hotfix cascade: after merge to prod, cherry-pick to staging, then dev

## Conventional Commit Types

Source: https://www.bavaga.com/blog/2025/01/27/my-ultimate-conventional-commit-types-cheatsheet/

| Type | Purpose |
|------|---------|
| `feat` | New feature or functionality |
| `fix` | Bug fix |
| `chore` | Maintenance and routine tasks |
| `perf` | Performance improvements |
| `docs` | Documentation |
| `build` | Build process or dependencies |
| `revert` | Revert a previous commit |
| `style` | Code formatting only |
| `refactor` | Code restructuring without behavior change |
| `ci` | CI/CD configuration |
| `test` | Tests |
| `hotfix` | Emergency fix applied to prod (ONLY valid on hotfix/* branches) |

## Commit Message Format

```
<type>(<optional-scope>): <description>

[optional body]

[optional footer: BREAKING CHANGE, ticket refs]
```

## Branch Naming Convention

- With ticket system: `<type>/<TICKET-123>-<kebab-description>`
- Without ticket system: `<type>/<kebab-description>`
- Hotfix: `hotfix/<TICKET-123>-<kebab-description>` or `hotfix/<kebab-description>`

## PR Title Format

- With ticket: `type(scope): TICKET-123 description`
- Without ticket: `type(scope): description`

## Heuristic Mapping (file path → commit type)

| Path Pattern | Detected Type |
|-------------|---------------|
| `tests/`, `**/test_*`, `**/*_test.*`, `*.test.*` | test |
| `.github/workflows/`, `.gitlab-ci*`, `Jenkinsfile`, `.circleci/` | ci |
| `docs/`, `*.md`, `CHANGELOG*` | docs |
| `Dockerfile*`, `docker-compose*`, `k8s/`, `helm/`, `Tiltfile` | build |
| `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod` (deps only) | build |
| `*.css`, `*.scss` (formatting only, no logic) | style |
| `scripts/`, `Makefile`, `.gitignore`, `.editorconfig` | chore |
| `src/` (new files) | feat |
| `src/` (modified files, bug context in diff) | fix |
| Default fallback | prompt user |

---

## Task Breakdown

### Task 1: Create the steering document for git workflow conventions

- **Objective:** Create `steering/conventions/git-workflow.md` — the reference document defining branching strategy, conventional commit rules, PR conventions, hotfix flow, submodule strategy, and CI promotion model.
- **Implementation guidance:**
  - Define the branching model (prod/staging/dev + feature branches)
  - Document conventional commit types with the hotfix addition
  - Define branch naming convention with/without ticket system
  - Document PR title format: `type(scope): TICKET-123 description`
  - Document the submodule independence model
  - Document the auto-promotion CI model
  - Include the heuristic mapping table (file paths → commit types)
  - Include the squash/rebase rules and non-conforming message rewrite strategy
  - Document rebase best practices:
    - Squash before rebase (reduce conflict surface)
    - `git rerere` enabled by default (reuse recorded resolutions)
    - Rebase resolution loop (resolve → add → continue, NEVER commit)
    - Golden rule: never rebase shared/pushed branches
    - Always `--force-with-lease` over `--force`
- **Test requirements:** Validate markdown renders correctly, all internal cross-references resolve
- **Demo:** A complete steering document that can be read and understood independently

### Task 2: Create `pyproject.toml` and project scaffolding

- **Objective:** Set up the Python project structure at `scripts/git/` with dependencies, entry points, and pytest configuration.
- **Implementation guidance:**
  - `pyproject.toml` with: `click` (CLI), `rich` (terminal UI for interactive prompts), `pytest`, `pytest-mock` as dev deps
  - Entry points: `git-commit = "src.commit:main"`, `git-branch = "src.branch:main"`, `git-prepare-pr = "src.prepare_pr:main"`, `git-hotfix = "src.hotfix:main"`, `git-merge-pr = "src.merge_pr:main"`, `git-promote = "src.promote:main"`
  - pytest config: markers for `unit` and `integration`, coverage settings
  - Create all `__init__.py` files
  - `.python-version` for uv
- **Test requirements:** `uv sync` succeeds; `uv run pytest --collect-only` runs with no import errors
- **Demo:** `uv run git-commit --help` prints usage (stub); `uv run pytest` collects tests

### Task 3: Create the library modules (`scripts/git/src/lib/`)

- **Objective:** Implement `conventional.py`, `detect_changes.py`, `ticket.py`, and `git_ops.py`.
- **Implementation guidance:**
  - `conventional.py`: regex validation, valid types list, message rewrite function, hotfix branch validation
  - `detect_changes.py`: file path → type mapping, grouping function, configurable heuristic rules
  - `ticket.py`: env var check for `TICKET_SYSTEM_URL`, ticket ID extraction from branch names, PR title formatting, ticket system type detection (Jira, Linear, etc.)
  - `git_ops.py`: subprocess wrappers for git commands (status, commit, branch, rebase, cherry-pick), typed results, idempotent checks
- **Test requirements:** Full unit tests in `tests/unit/` — mocked subprocess calls. Target 95%+ coverage.
- **Demo:** `python -c "from src.lib.conventional import validate; print(validate('feat: add login'))"` → True

### Task 4: Create `src/branch.py` — branch creation with naming validation

- **Objective:** Click CLI that creates properly named branches with interactive prompts.
- **Implementation guidance:**
  - Click CLI: `--type`, `--ticket`, `--description`, `--from` (base branch, default: dev)
  - Interactive prompts when args not provided
  - Idempotent: if on target branch, exit 0 with message
  - Format: `<type>/<TICKET-123>-<kebab-description>` or `<type>/<kebab-description>`
  - Submodule detection via `git rev-parse --show-superproject-working-tree`
- **Test requirements:** Unit tests for formatting; integration tests with tmp_path git repos
- **Demo:** `uv run git-branch --type feat --description "add user auth"` creates `feat/add-user-auth`

### Task 5: Create `src/commit.py` — auto-grouped conventional commits

- **Objective:** Click CLI that auto-detects, groups, confirms, and commits changes per type.
- **Implementation guidance:**
  - Options: `--no-interactive`, `--dry-run`
  - If clean: exit 0 "Nothing to commit"
  - Group by heuristic → present table (rich) → allow override → commit each group
  - Auto-detect scope from common path prefix
  - Multiple types → multiple separate commits
- **Test requirements:** Unit tests for grouping; integration tests with real git repos verifying commit count and messages
- **Demo:** Changes in `tests/` and `src/` → two properly formatted commits

### Task 6: Create git hooks (shell shims + Python validation)

- **Objective:** `hooks/commit-msg` and `hooks/pre-push` — thin shell calling Python.
- **Implementation guidance:**
  - `commit-msg`: calls `python -m src.lib.conventional validate-file "$1"`, helpful error on failure
  - `pre-push`: calls `python -m src.lib.ticket validate-branch`, warns without ticket URL, blocks with it
  - Both chmod +x, installed via setup.sh as symlinks
- **Test requirements:** Integration tests: init repo, install hooks, verify rejection/acceptance
- **Demo:** `git commit -m "fixed stuff"` → rejected with suggestion

### Task 7: Create `src/prepare_pr.py` — squash + rewrite + rebase

- **Objective:** Interactive squash/rebase preparation for clean PR history.
- **Implementation guidance:**
  - Options: `--target` (default: dev), `--dry-run`, `--force`
  - List commits, group by type, squash per group, rewrite non-conforming messages
  - Rebase onto target
  - Idempotent: already clean → exit 0
  - Suggest PR title, warn about force-push
- **Test requirements:** Integration tests with multi-commit branches; test message rewrite
- **Demo:** 5 messy commits → 2 clean commits, rebased, PR title suggested

### Task 8: Create `src/hotfix.py` — hotfix workflow

- **Objective:** Full hotfix flow from prod with cherry-pick cascade.
- **Implementation guidance:**
  - Options: `--ticket`, `--description`, `--cherry-pick`
  - Branch from prod, `hotfix:` type validation
  - Guide PR creation (detect gh CLI)
  - Cherry-pick to staging/dev with conflict guidance
  - Idempotent: existing hotfix branch → offer resume
- **Test requirements:** Integration tests for branch creation; unit tests for hotfix type validation
- **Demo:** `uv run git-hotfix --description "fix payment timeout"` → full guided workflow

### Task 9: Create `setup.sh` — installation and environment configuration

- **Objective:** One-time setup: install hooks, validate Python env, configure workflow.
- **Implementation guidance:**
  - Check prerequisites: git ≥ 2.28, python ≥ 3.11, uv
  - `uv sync` to install deps
  - Symlink hooks (parent repo + submodules)
  - Report TICKET_SYSTEM_URL status
  - Suggest aliases/PATH
  - Idempotent
- **Test requirements:** Verify idempotent re-run; hooks installed correctly
- **Demo:** `./scripts/git/setup.sh` installs everything, bad commit immediately rejected

### Task 10: Create the skill file `skills/git-workflow.md` using the create-kiro-skill workflow

- **Objective:** Use the `create-kiro-skill` skill workflow to create the Kiro skill that ties everything together.
- **Implementation guidance — follow create-kiro-skill execution workflow:**
  1. **Pre-Flight** — Check if `skills/git-workflow.md` exists. Run git status on .kiro/
  2. **Bounded Overlap Check** — List skills/, identify candidates (deploy.md, refactor.md). Read those to confirm no overlap.
  3. **Clarify** — No overlap expected (deploy covers terraform/infra, this covers git workflow)
  4. **Draft Skill** — Write following schema:
     - `name: git-workflow`
     - `description: Use when performing Git operations following the team's branching strategy — creating branches, making conventional commits, preparing PRs with squash/rebase, executing hotfix flows, or managing submodule versioning in microservice monorepos. NOT for deploying (use deploy) or CI pipeline configuration files (use the ci type in conventional commits directly).`
     - Role & Tone: senior platform/DevOps engineer, concise, script-oriented
     - Environment Scope: write+execute
     - Workflow: check state → determine operation → execute appropriate Python script → verify
     - Failure Recovery: merge conflicts, rebase failures, hook rejections (max 3 retries)
     - Rollback: `git reflog` based recovery
     - Guardrails: never force-push without confirmation, never commit directly to prod/staging/dev, never skip hook validation, never use hotfix: type on non-hotfix branches
     - References: `steering/conventions/git-workflow.md`
  5. **Present for Approval** — Show draft to user
  6. **Save & Register** — Write to `skills/git-workflow.md`, add `skill://../skills/git-workflow.md` to `agents/dev.json` and `agents/infra.json`
  7. **Verify** — Confirm file parses, agent configs valid JSON

### Task 11: Update README.md and agent configuration

- **Objective:** Register new skill, scripts, and steering in project documentation.
- **Implementation guidance:**
  - Add `scripts/git/` to README directory structure
  - Add `skills/git-workflow.md` to skills list
  - Add `steering/conventions/git-workflow.md` to steering list
  - Document `setup.sh` usage
  - Verify all paths exist; agent configs valid JSON
- **Test requirements:** All referenced paths exist; `uv run pytest` passes from scripts/git/
- **Demo:** README accurately reflects new structure; `kiro --agent dev` shows git-workflow skill
