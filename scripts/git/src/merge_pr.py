"""Final validation and merge for PRs — ensures linear history and conforming messages."""

import click


@click.command()
@click.option("--target", default="dev", help="Target branch to merge into.")
@click.option("--dry-run", is_flag=True, help="Validate without merging.")
def main(target: str, dry_run: bool) -> None:
    """Validate PR branch and merge with fast-forward (linear history)."""
    from src.lib.git_ops import get_current_branch, get_commits_ahead
    from src.lib.conventional import validate

    current = get_current_branch()
    if current in ("prod", "staging", "dev"):
        click.echo(f"❌ Cannot merge from protected branch '{current}'.")
        raise SystemExit(1)

    commits = get_commits_ahead(target)
    if not commits:
        click.echo(f"✅ Branch '{current}' has no commits ahead of '{target}'.")
        raise SystemExit(0)

    # Validate all commit messages
    invalid = []
    for commit in commits:
        if not validate(commit.message):
            invalid.append(commit)

    if invalid:
        click.echo("❌ Non-conforming commit messages found:")
        for commit in invalid:
            click.echo(f"  {commit.sha[:7]} {commit.message}")
        click.echo("Run 'git-prepare-pr' to fix these before merging.")
        raise SystemExit(1)

    if dry_run:
        click.echo(f"[DRY RUN] Would fast-forward merge '{current}' into '{target}'.")
        raise SystemExit(0)

    # TODO: Implement fast-forward merge
    click.echo(f"All {len(commits)} commits valid. Full merge implementation pending.")


if __name__ == "__main__":
    main()
