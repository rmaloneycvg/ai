# PR Template

## Title Format

```
<type>(<scope>): <short description>
```

- Must follow conventional commit format
- Max 70 characters
- If ticket system is configured: `<type>(<scope>): TICKET-123 <description>`

## Body Structure

```markdown
## Summary

One to three sentences explaining what this PR does and why.

## Changes

- Bullet list of specific changes made
- Group by logical unit if multiple files affected
- Reference specific functions/modules changed

## Testing

- [ ] Unit tests pass (`uv run pytest tests/unit`)
- [ ] Integration tests pass (`uv run pytest tests/integration`)
- [ ] Manual verification: <describe what was manually tested>

## Notes

Optional section for:
- Migration steps required
- Breaking changes
- Follow-up work needed
- Dependencies on other PRs
```

## Rules

- `git-prepare-pr` auto-generates the title from squashed commit messages
- Body is populated from commit descriptions (one bullet per squashed commit)
- If a single commit PR: title = commit message, body = commit body (if any)
- Reviewers are NOT auto-assigned — user must specify or use CODEOWNERS

## Hotfix PRs

Hotfix PRs to `prod` must include an additional section:

```markdown
## Impact

- Services affected: <list>
- Rollback plan: <revert commit SHA or feature flag>
- Urgency: <P0/P1/P2>
```

## Merge Strategy

- PRs to `dev`: squash merge (single clean commit on dev)
- PRs to `prod` (hotfix): merge commit (preserves hotfix branch history for audit)
- Never use rebase merge on shared branches
