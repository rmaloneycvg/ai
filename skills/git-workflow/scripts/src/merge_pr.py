"""Final validation and merge for PRs — ensures linear history and conforming messages."""

import sys

import click
from rich.console import Console

from src.lib.conventional import validate
from src.lib.git_ops import get_current_branch, get_commits_ahead, branch_exists, _run

console = Console()


@click.command()
@click.option("--target", default="dev", show_default=True, help="Target branch to merge into.")
@click.option("--dry-run", is_flag=True, help="Validate without merging.")
@click.option("--squash", is_flag=True, help="Squash merge (single commit on target).")
def main(target: str, dry_run: bool, squash: bool) -> None:
    """Validate PR branch and merge into target with appropriate strategy."""
    current = get_current_branch()

    if current in ("prod", "staging", "dev"):
        console.print(f"❌ Cannot merge from protected branch '[bold]{current}[/bold]'.")
        console.print("   Switch to the feature/hotfix branch you want to merge.")
        sys.exit(1)

    if not branch_exists(target):
        console.print(f"❌ Target branch '[bold]{target}[/bold]' does not exist.")
        sys.exit(1)

    commits = get_commits_ahead(target)
    if not commits:
        console.print(f"✅ Branch '[bold]{current}[/bold]' has no commits ahead of '{target}'.")
        sys.exit(0)

    # Validate all commit messages
    invalid = []
    for commit in commits:
        if not validate(commit.message):
            invalid.append(commit)

    if invalid:
        console.print("❌ Non-conforming commit messages found:")
        for commit in invalid:
            console.print(f"  {commit.sha[:7]} {commit.message}")
        console.print("\nRun [bold]uv run git-prepare-pr[/bold] to fix these before merging.")
        sys.exit(1)

    # Check if branch is rebased onto target (no merge commits needed)
    merge_base = _run(["merge-base", "HEAD", target])
    target_head = _run(["rev-parse", target])
    if merge_base.stdout.strip() != target_head.stdout.strip():
        console.print(f"⚠️  Branch is not rebased onto '{target}'.")
        console.print(f"   Run: [bold]uv run git-prepare-pr --target {target}[/bold]")
        sys.exit(1)

    console.print(f"\n[bold]Branch:[/bold] {current}")
    console.print(f"[bold]Target:[/bold] {target}")
    console.print(f"[bold]Commits:[/bold] {len(commits)}")
    console.print(f"[bold]Strategy:[/bold] {'squash' if squash else 'fast-forward'}\n")

    if dry_run:
        console.print(f"[dim][DRY RUN] Would {'squash merge' if squash else 'fast-forward'} "
                      f"'{current}' into '{target}'.[/dim]")
        sys.exit(0)

    # Confirm
    if not click.confirm(f"Merge '{current}' into '{target}'?", default=True):
        console.print("Cancelled.")
        sys.exit(0)

    # Switch to target
    result = _run(["checkout", target])
    if result.returncode != 0:
        console.print(f"❌ Could not switch to '{target}': {result.stderr}")
        sys.exit(1)

    if squash:
        # Squash merge: combine all commits into one on target
        result = _run(["merge", "--squash", current])
        if result.returncode != 0:
            console.print(f"❌ Squash merge failed: {result.stderr}")
            _run(["checkout", current])
            sys.exit(1)

        # Commit the squashed result with the primary commit message
        primary_message = commits[0].message
        result = _run(["commit", "-m", primary_message])
        if result.returncode != 0:
            console.print(f"❌ Commit failed: {result.stderr}")
            _run(["checkout", current])
            sys.exit(1)
    else:
        # Fast-forward merge (linear history)
        result = _run(["merge", "--ff-only", current])
        if result.returncode != 0:
            console.print(f"❌ Fast-forward merge failed: {result.stderr}")
            console.print("   Branch may need rebasing. Run git-prepare-pr first.")
            _run(["checkout", current])
            sys.exit(1)

    console.print(f"✅ Merged '[bold]{current}[/bold]' into '[bold]{target}[/bold]'.")

    # Offer to delete the merged branch
    if click.confirm(f"Delete branch '{current}'?", default=True):
        result = _run(["branch", "-d", current])
        if result.returncode == 0:
            console.print(f"  🗑️  Deleted local branch '{current}'.")
        else:
            console.print(f"  ⚠️  Could not delete: {result.stderr}")


if __name__ == "__main__":
    main()
