"""Hotfix workflow: branch from prod, guide fix, PR to prod, cherry-pick cascade."""

import shutil
import sys

import click
from rich.console import Console
from rich.table import Table

from src.lib.conventional import VALID_TYPES
from src.lib.git_ops import (
    get_current_branch,
    branch_exists,
    create_branch,
    get_commits_ahead,
    _run,
)
from src.lib.ticket import get_ticket_url, format_branch_name, format_pr_title

console = Console()


@click.command()
@click.option("--ticket", type=str, default=None, help="Ticket ID for the hotfix.")
@click.option("--description", type=str, help="Hotfix description in kebab-case.")
@click.option(
    "--cherry-pick",
    "do_cherry_pick",
    is_flag=True,
    help="Cherry-pick to staging and dev after merge to prod.",
)
def main(ticket: str | None, description: str | None, do_cherry_pick: bool) -> None:
    """Execute hotfix workflow: branch from prod, fix, PR, cherry-pick cascade."""
    current = get_current_branch()

    # If already on a hotfix branch, offer to continue the workflow
    if current.startswith("hotfix/"):
        _resume_hotfix(current, do_cherry_pick)
        return

    # Interactive prompts
    if not description:
        description = click.prompt("Hotfix description (use spaces or kebab-case)")

    ticket_url = get_ticket_url()
    if ticket_url and not ticket:
        ticket = click.prompt("Ticket ID (e.g., INC-123, leave empty to skip)", default="", show_default=False)
        if not ticket.strip():
            ticket = None

    branch_name = format_branch_name("hotfix", description, ticket)

    # Check if hotfix branch already exists (resume flow)
    if branch_exists(branch_name):
        console.print(f"⚠️  Hotfix branch '[bold]{branch_name}[/bold]' already exists.")
        if click.confirm("Switch to it and resume?", default=True):
            create_branch(branch_name, "prod")  # Idempotent — switches if exists
            _resume_hotfix(branch_name, do_cherry_pick)
        return

    # Ensure we can branch from prod
    if not branch_exists("prod"):
        console.print("❌ Branch 'prod' does not exist. Cannot create hotfix.")
        sys.exit(1)

    # Show summary
    console.print()
    table = Table(title="Hotfix Branch", show_header=False, border_style="dim")
    table.add_row("Branch", f"[bold]{branch_name}[/bold]")
    table.add_row("From", "prod")
    if ticket:
        table.add_row("Ticket", ticket)
    if ticket_url and ticket:
        table.add_row("Link", f"{ticket_url}/browse/{ticket}")
    console.print(table)
    console.print()

    # Create hotfix branch from prod
    try:
        create_branch(branch_name, "prod")
    except RuntimeError as e:
        console.print(f"❌ {e}")
        sys.exit(1)

    console.print(f"✅ Created hotfix branch '[bold]{branch_name}[/bold]' from 'prod'.\n")
    _show_next_steps(branch_name, ticket)


def _resume_hotfix(branch_name: str, do_cherry_pick: bool) -> None:
    """Resume an in-progress hotfix workflow."""
    console.print(f"\n[bold]Resuming hotfix on:[/bold] {branch_name}\n")

    commits = get_commits_ahead("prod")

    if not commits:
        console.print("No commits yet on this hotfix branch.")
        _show_next_steps(branch_name, None)
        return

    # Show commits made so far
    console.print(f"[bold]Commits on this hotfix branch:[/bold]")
    for c in commits:
        console.print(f"  • {c.sha[:7]} {c.message}")
    console.print()

    # Determine next step
    choices = [
        "Prepare PR for review (squash + rebase onto prod)",
        "Create PR now (using gh CLI)",
        "Cherry-pick to staging and dev",
        "Show next steps and exit",
    ]

    for i, choice in enumerate(choices, 1):
        console.print(f"  {i}. {choice}")

    action = click.prompt("\nWhat would you like to do?", type=click.IntRange(1, len(choices)))

    if action == 1:
        _prepare_hotfix_pr(branch_name)
    elif action == 2:
        _create_pr(branch_name)
    elif action == 3:
        _cherry_pick_cascade(commits)
    else:
        _show_next_steps(branch_name, None)


def _prepare_hotfix_pr(branch_name: str) -> None:
    """Run prepare-pr targeting prod."""
    console.print("\n[dim]Running: git-prepare-pr --target prod[/dim]\n")
    # Import and call prepare_pr directly
    from src.prepare_pr import main as prepare_pr_main

    try:
        prepare_pr_main.main(["--target", "prod"], standalone_mode=False)
    except SystemExit:
        pass


def _create_pr(branch_name: str) -> None:
    """Create a PR using gh CLI if available."""
    if not shutil.which("gh"):
        console.print("⚠️  GitHub CLI (gh) not found. Create PR manually:")
        console.print(f"   Target: prod")
        console.print(f"   Branch: {branch_name}")
        return

    ticket = None
    from src.lib.ticket import extract_ticket_from_branch
    ticket = extract_ticket_from_branch(branch_name)

    # Extract description from branch name
    parts = branch_name.split("/", 1)
    description = parts[1] if len(parts) == 2 else branch_name
    description = description.replace("-", " ")
    if ticket:
        description = description.replace(ticket, "").strip(" -")

    pr_title = format_pr_title("hotfix", description, ticket=ticket)

    console.print(f"\n[bold]Creating PR:[/bold]")
    console.print(f"  Title: {pr_title}")
    console.print(f"  Base: prod")
    console.print(f"  Head: {branch_name}")

    if click.confirm("\nCreate this PR?", default=True):
        result = _run(["gh", "pr", "create", "--title", pr_title, "--base", "prod", "--fill"])
        if result.returncode == 0:
            console.print(f"✅ PR created successfully.")
        else:
            console.print(f"❌ Failed to create PR: {result.stderr}")


def _cherry_pick_cascade(commits: list) -> None:
    """Cherry-pick hotfix commits to staging and dev."""
    if not commits:
        console.print("❌ No commits to cherry-pick.")
        return

    shas = [c.sha for c in commits]
    console.print(f"\n[bold]Cherry-picking {len(shas)} commit(s) to staging and dev:[/bold]")

    for target in ("staging", "dev"):
        if not branch_exists(target):
            console.print(f"  ⚠️  Branch '{target}' does not exist. Skipping.")
            continue

        console.print(f"\n  → Cherry-picking to '{target}'...")

        # Switch to target branch
        result = _run(["checkout", target])
        if result.returncode != 0:
            console.print(f"  ❌ Could not switch to '{target}': {result.stderr}")
            continue

        # Cherry-pick each commit
        for sha in shas:
            result = _run(["cherry-pick", sha])
            if result.returncode != 0:
                console.print(f"  ⚠️  Conflict cherry-picking {sha[:7]} to '{target}'.")
                console.print(f"      Resolve conflicts, then:")
                console.print(f"        git add <resolved-files>")
                console.print(f"        git cherry-pick --continue")
                console.print(f"      Or abort: git cherry-pick --abort")
                return

        console.print(f"  ✅ Cherry-picked to '{target}' successfully.")

    # Return to original branch
    _run(["checkout", "-"])
    console.print("\n✅ Cherry-pick cascade complete.")


def _show_next_steps(branch_name: str, ticket: str | None) -> None:
    """Display next steps for the hotfix workflow."""
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Make your fix")
    console.print("  2. Run: [bold]git-commit[/bold] (uses 'hotfix:' type on this branch)")
    console.print("  3. Run: [bold]git-prepare-pr --target prod[/bold]")
    console.print("  4. Create PR targeting 'prod'")
    if shutil.which("gh"):
        console.print("     Or: [bold]git-hotfix --cherry-pick[/bold] (after merge)")
    console.print("  5. After merge: cherry-pick to staging and dev")
    console.print("     [dim]git checkout staging && git cherry-pick <sha>[/dim]")
    console.print("     [dim]git checkout dev && git cherry-pick <sha>[/dim]")


if __name__ == "__main__":
    main()
