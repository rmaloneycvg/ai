# Revert Workflow

## When to Revert vs Forward-Fix

| Situation | Action |
|-----------|--------|
| Bad commit merged to `dev`, CI still green | Forward-fix preferred (new commit fixing the issue) |
| Bad commit merged to `dev`, CI broken | Revert immediately to unblock team |
| Bad commit on `staging` | Revert — staging must stay deployable |
| Bad commit on `prod` | Use hotfix flow OR revert, depending on severity |
| Merge commit needs backing out | Revert with `-m 1` flag |

## Reverting a Regular Commit

```bash
# Identify the bad commit
git log --oneline -10

# Create the revert commit
git revert <sha> --no-edit

# Verify the revert looks correct
git diff HEAD~1

# Push
git push
```

Commit message is auto-generated: `Revert "<original message>"`. This is acceptable — do not override.

## Reverting a Merge Commit

Merge commits have two parents. You must specify which parent to keep:

```bash
# -m 1 keeps the mainline (the branch you merged INTO)
git revert -m 1 <merge-commit-sha>
```

- `-m 1`: keeps the target branch history (almost always what you want)
- `-m 2`: keeps the feature branch history (rarely correct)

## Reverting on Shared Branches

When reverting on `dev`, `staging`, or `prod`:

1. **Do not rebase or force-push** — always use `git revert` (creates a new commit)
2. Notify the team that the commit was reverted and why
3. If the original work needs to be re-landed later, the author must:
   - Revert the revert: `git revert <revert-sha>`
   - OR rebase their branch onto the reverted state and re-submit

## Re-landing Reverted Work

After a revert, Git considers those changes "already applied" during future merges. To re-land:

**Option A — Revert the revert (preferred for simple cases):**
```bash
git revert <revert-commit-sha>
```

**Option B — Rebase with new commits (preferred if the code needs fixes):**
```bash
git checkout feature/original-work
git rebase dev
# Fix the issue that caused the revert
git commit -m "fix(scope): resolve issue that caused revert"
# Submit new PR
```

## Revert Commit Type

Use the auto-generated `Revert "..."` message for simple reverts. For complex reverts with context, use:

```
revert(scope): back out feature X due to Y

Reverts commit <sha>.
The original change caused <specific issue>.
Will re-land after <condition>.
```

## Integration with Hotfix Flow

If a revert is needed on `prod` and the commit exists only on `prod` (was a hotfix):
1. Use the normal revert flow on `prod`
2. Cherry-pick the revert down to `staging` and `dev`
3. Use `uv run git-hotfix` if additional fixes are needed alongside the revert

## Do NOT

- Force-push to remove the bad commit from history on shared branches
- Use `git reset` on shared branches — this rewrites history others depend on
- Revert without verifying CI passes on the reverted state
- Leave reverts unexplained — always note why in the commit body or PR description
