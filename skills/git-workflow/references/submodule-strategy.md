# Submodule Strategy

## Overview

Each microservice is an independent Git repository added as a submodule to the parent monorepo. The parent repo pins each submodule to a specific commit SHA — never a branch tip.

## Updating a Submodule Version

1. Enter the submodule directory:
   ```bash
   cd services/<service-name>
   ```
2. Fetch and checkout the target version:
   ```bash
   git fetch origin
   git checkout <tag-or-sha>
   ```
3. Return to parent repo and stage the pointer update:
   ```bash
   cd ../..
   git add services/<service-name>
   ```
4. Commit with conventional format:
   ```
   chore(deps): bump <service-name> to <version-or-short-sha>
   ```

## Batch Updates

When promoting multiple services (e.g., after a release train):
```bash
git submodule foreach 'git fetch origin && git checkout origin/main'
git add services/
git commit -m "chore(deps): bump all services to latest main"
```

Use batch updates only when all services are known-good (CI green on each).

## Detached HEAD Recovery

Submodules are always in detached HEAD state by design. This is normal.

**If you need to make changes inside a submodule:**
1. Create a branch inside the submodule:
   ```bash
   cd services/<service-name>
   git checkout -b fix/description
   ```
2. Make changes, commit, push from within the submodule
3. Once merged upstream, update the parent's pointer as above

**If accidentally committed on detached HEAD:**
1. Note the commit SHA: `git log -1 --format=%H`
2. Create a branch to preserve it: `git branch rescue-branch <sha>`
3. Push and open a PR from within the submodule repo

## Do NOT Use

- `git submodule update --remote` in automation — it moves to branch tip which may not be tested
- `--recursive` flag without understanding which nested submodules exist
- Force-pushing inside a submodule — the parent repo's SHA reference becomes dangling

## When to Use git-promote Instead

If the goal is to advance a submodule from dev-tested to staging-tested to prod, use:
```bash
uv run git-promote --service <service-name> --from staging --to prod
```
This handles the parent pointer update, commit message, and validation.
