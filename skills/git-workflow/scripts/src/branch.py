"""Create branches with naming convention validation and ticket system integration."""

import sys

import click
from rich.console import Console
from rich.table import Table

from src.lib.conventional import VALID_TYPES
from src.lib.git_ops import get_current_branch, create_branch, branch_exists, is_submodule
from src.lib.ticket import (
    get_ticket_url,
    format_branch_name,
    validate_branch_name,
    extract_ticket_from_branch,
)

console = Console()

# Types commonly used for branches (exclude revert — that's a commit-only type)
BRANCH_TYPES = sorted(VALID_TYPES - {"revert"})


@click.command()
@click.option("--type", "branch_type", type=click.Choice(BRANCH_TYPES), help="Conventional commit type for the branch.")
@click.option("--ticket", type=str, default=None, help="Ticket ID (e.g., PROJ-123).")
@click.option("--description", type=str, help="Branch description in kebab-case.")
@click.option("--from", "from_branch", type=str, default="dev", show_default=True, help="Base branch to create from.")
@click.option("--rename", is_flag=True, help="Rename current branch to match conventions.")
def main(branch_type: str | None, ticket: str | None, description: str | None, from_branch: str, rename: bool) -> None:
    """Create a properly named branch following team conventions."""
    current = get_current_branch()

    # Detect submodule context
    if is_submodule():
        console.print("[dim]ℹ️  Inside a git submodule[/dim]")

    # Check if current branch already conforms
    if not rename:
        is_valid, _ = validate_branch_name(current)
        if is_valid and current not in ("prod", "staging", "dev", "main", "master"):
            console.print(f"✅ Already on branch '[bold]{current}[/bold]'.")
            sys.exit(0)

    # If current branch doesn't match conventions, suggest rename
    if not rename and current not in ("prod", "staging", "dev", "main", "master"):
        is_valid, error = validate_branch_name(current)
        if not is_valid:
            console.print(f"⚠️  Current branch '[bold]{current}[/bold]' doesn't follow conventions.")
            console.print(f"   {error}")
            if click.confirm("Would you like to create a new branch instead?", default=True):
                pass  # Continue to branch creation flow below
            else:
                sys.exit(0)

    # Interactive prompts for missing options
    if not branch_type:
        _show_type_table()
        branch_type = click.prompt(
            "Branch type",
            type=click.Choice(BRANCH_TYPES),
        )

    # Hotfix branches must come from prod
    if branch_type == "hotfix":
        from_branch = "prod"
        console.print("[dim]ℹ️  Hotfix branches always branch from 'prod'[/dim]")

    if not description:
        description = click.prompt("Branch description (use spaces or kebab-case)")

    # Ticket system integration
    ticket_url = get_ticket_url()
    if ticket_url and not ticket:
        ticket = click.prompt("Ticket ID (e.g., PROJ-123, leave empty to skip)", default="", show_default=False)
        if not ticket.strip():
            ticket = None

    # Format the branch name
    name = format_branch_name(branch_type, description, ticket)

    # Validate the generated name
    is_valid, error = validate_branch_name(name)
    if not is_valid:
        console.print(f"❌ Generated branch name is invalid: {error}")
        sys.exit(1)

    # Check if already on this branch (idempotent)
    if current == name:
        console.print(f"✅ Already on branch '[bold]{name}[/bold]'.")
        sys.exit(0)

    # Check if branch already exists
    if branch_exists(name):
        console.print(f"⚠️  Branch '[bold]{name}[/bold]' already exists.")
        if click.confirm("Switch to it?", default=True):
            create_branch(name, from_branch)  # Idempotent — switches if exists
            console.print(f"✅ Switched to '[bold]{name}[/bold]'.")
        sys.exit(0)

    # Show summary before creating
    console.print()
    table = Table(title="New Branch", show_header=False, border_style="dim")
    table.add_row("Name", f"[bold]{name}[/bold]")
    table.add_row("Type", branch_type)
    table.add_row("From", from_branch)
    if ticket:
        table.add_row("Ticket", ticket)
    if ticket_url:
        table.add_row("Ticket System", ticket_url)
    console.print(table)
    console.print()

    # Create the branch
    try:
        create_branch(name, from_branch)
    except RuntimeError as e:
        console.print(f"❌ {e}")
        sys.exit(1)

    console.print(f"✅ Created and switched to branch '[bold]{name}[/bold]'.")


def _show_type_table() -> None:
    """Display a table of available branch types."""
    type_descriptions = {
        "feat": "New feature or functionality",
        "fix": "Bug fix",
        "chore": "Maintenance and routine tasks",
        "perf": "Performance improvements",
        "docs": "Documentation",
        "build": "Build process or dependencies",
        "style": "Code formatting only",
        "refactor": "Code restructuring without behavior change",
        "ci": "CI/CD configuration",
        "test": "Tests",
        "hotfix": "Emergency fix (branches from prod)",
    }
    table = Table(title="Branch Types", border_style="dim")
    table.add_column("Type", style="bold cyan")
    table.add_column("Purpose")
    for t in BRANCH_TYPES:
        table.add_row(t, type_descriptions.get(t, ""))
    console.print(table)
    console.print()


if __name__ == "__main__":
    main()
