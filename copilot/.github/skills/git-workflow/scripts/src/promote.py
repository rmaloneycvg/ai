"""Manual environment promotion trigger (dev -> staging -> prod)."""

import sys

import click
from rich.console import Console

from src.lib.git_ops import get_current_branch, branch_exists, get_commits_ahead, _run

console = Console()

VALID_PROMOTIONS = {"dev": "staging", "staging": "prod"}


@click.command()
@click.option("--from", "from_env", type=click.Choice(["dev", "staging"]), required=True, help="Source environment.")
@click.option("--to", "to_env", type=click.Choice(["staging", "prod"]), required=True, help="Target environment.")
@click.option("--dry-run", is_flag=True, help="Show what would happen without promoting.")
def main(from_env: str, to_env: str, dry_run: bool) -> None:
    """Manually promote code between environments via fast-forward merge."""
    # Validate promotion direction
    if VALID_PROMOTIONS.get(from_env) != to_env:
        console.print(f"❌ Invalid promotion: '{from_env}' -> '{to_env}'.")
        console.print(f"   Valid promotions: dev->staging, staging->prod.")
        sys.exit(1)

    # Validate both branches exist
    if not branch_exists(from_env):
        console.print(f"❌ Source branch '{from_env}' does not exist.")
        sys.exit(1)

    if not branch_exists(to_env):
        console.print(f"❌ Target branch '{to_env}' does not exist.")
        sys.exit(1)

    # Check what would be promoted
    result = _run(["log", f"{to_env}..{from_env}", "--oneline", "--format=%H %s"])
    if result.returncode != 0:
        console.print(f"❌ Could not compare branches: {result.stderr}")
        sys.exit(1)

    commits_to_promote = []
    for line in result.stdout.strip().splitlines():
        if line:
            sha, msg = line.split(" ", 1)
            commits_to_promote.append((sha[:7], msg))

    if not commits_to_promote:
        console.print(f"✅ '{to_env}' is already up to date with '{from_env}'. Nothing to promote.")
        sys.exit(0)

    # Display what will be promoted
    console.print(f"\n[bold]Promotion:[/bold] {from_env} -> {to_env}")
    console.print(f"[bold]Commits to promote:[/bold] {len(commits_to_promote)}\n")

    for sha, msg in commits_to_promote[:20]:
        console.print(f"  {sha} {msg}")
    if len(commits_to_promote) > 20:
        console.print(f"  [dim]... and {len(commits_to_promote) - 20} more[/dim]")

    if dry_run:
        console.print(f"\n[dim][DRY RUN] Would fast-forward '{to_env}' to match '{from_env}'.[/dim]")
        sys.exit(0)

    # Confirm
    console.print()
    if not click.confirm(f"Promote {len(commits_to_promote)} commit(s) from '{from_env}' to '{to_env}'?", default=True):
        console.print("Cancelled.")
        sys.exit(0)

    # Save current branch to return to it
    original_branch = get_current_branch()

    # Switch to target and fast-forward
    result = _run(["checkout", to_env])
    if result.returncode != 0:
        console.print(f"❌ Could not switch to '{to_env}': {result.stderr}")
        sys.exit(1)

    result = _run(["merge", "--ff-only", from_env])
    if result.returncode != 0:
        console.print(f"❌ Fast-forward failed: {result.stderr}")
        console.print(f"   '{to_env}' has diverged from '{from_env}'. Manual intervention required.")
        _run(["checkout", original_branch])
        sys.exit(1)

    console.print(f"\n✅ Promoted '{from_env}' -> '{to_env}' ({len(commits_to_promote)} commits).")

    # Return to original branch
    if original_branch != to_env:
        _run(["checkout", original_branch])
        console.print(f"  Returned to '{original_branch}'.")

    console.print(f"\n[yellow]⚠️  Don't forget to push: git push origin {to_env}[/yellow]")


if __name__ == "__main__":
    main()
