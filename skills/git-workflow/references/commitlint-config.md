# Commitlint Configuration

## Valid Types

| Type | When to Use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `chore` | Maintenance, dependency updates, config changes |
| `perf` | Performance improvement (no functional change) |
| `docs` | Documentation only |
| `build` | Build system or external dependency changes |
| `revert` | Reverting a previous commit |
| `style` | Code style (formatting, whitespace — no logic change) |
| `refactor` | Code restructuring (no feature or fix) |
| `ci` | CI/CD pipeline configuration |
| `test` | Adding or modifying tests |
| `hotfix` | Emergency fix — ONLY valid on `hotfix/*` branches |

## Accepted Scopes

Scopes are auto-detected from the common path prefix of staged files. The following are the canonical scopes accepted by the commit-msg hook:

| Scope | Matches |
|-------|---------|
| `api` | `services/api/`, `src/api/` |
| `ui` | `services/ui/`, `src/ui/`, `frontend/` |
| `db` | `migrations/`, `src/db/`, `schemas/` |
| `deps` | `package.json`, `pyproject.toml`, `uv.lock`, `go.sum` |
| `infra` | `terraform/`, `pulumi/`, `docker/`, `k8s/` |
| `auth` | `src/auth/`, `services/auth/` |
| `config` | `.env*`, `config/`, `settings/` |
| `scripts` | `scripts/`, `tools/`, `bin/` |
| `docs` | `docs/`, `*.md` (except CHANGELOG) |

## Scope Rules

- If staged files span multiple scopes: omit scope entirely
- If all staged files share a common prefix that maps to a scope: use it
- Custom scopes are allowed but will trigger a warning (not a block)
- Scope is always lowercase, no spaces, no special characters

## Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Validation Rules

- **Header max length:** 72 characters
- **Description:** imperative mood, lowercase start, no trailing period
- **Body:** wrapped at 100 characters, separated from header by blank line
- **Footer:** `BREAKING CHANGE: <description>` or `Refs: TICKET-123`

### Examples

```
feat(api): add pagination to /users endpoint

Adds limit/offset query params with a default page size of 25.
Returns X-Total-Count header for client-side pagination UI.

Refs: PROJ-456
```

```
fix(db): prevent duplicate key on concurrent inserts

Adds ON CONFLICT DO NOTHING clause to the upsert query.
Previously, parallel requests could trigger unique constraint violations.
```

```
chore(deps): bump express from 4.18.2 to 4.19.0
```

## Hook Behavior

The `commit-msg` hook (`hooks/commit-msg`) validates:
1. Type is in the valid list
2. Format matches `type(scope): description` or `type: description`
3. Header length <= 72 characters
4. `hotfix` type only on `hotfix/*` branches

On failure: prints the violation and blocks the commit. Fix the message and retry.
