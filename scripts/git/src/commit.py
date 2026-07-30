"""Auto-detect, group, confirm, and commit changes per conventional commit type."""

import sys

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from src.lib.conventional import VALID_TYPES, validate, is_hotfix_allowed
from src.lib.detect_changes import detect_type, group_changes, sort_groups, detect_scope, COMMIT_ORDER
from src.lib.git_ops import get_status, get_current_branch, stage_files, commit

console = Console()


@click.command()
@click.option("--no-interactive", is_flag=True, help="Auto-accept grouping without prompts.")
@click.option("--dry-run", is_flag=True, help="Show what would be committed without committing.")
def main(no_interactive: bool, dry_run: bool) -> None:
    """Auto-group uncommitted changes by type and commit each group separately."""
    current_branch = get_current_branch()

    # Guard: don't commit to protected branches
    if current_branch in ("prod", "staging", "dev"):
        console.print(f"❌ Cannot commit directly to protected branch '[bold]{current_branch}[/bold]'.")
        console.print("   Create a feature branch first: [dim]git-branch[/dim]")
        sys.exit(1)

    status = get_status()
    all_files = status.staged + status.unstaged
    has_changes = bool(all_files) or bool(status.untracked)

    if not has_changes:
        console.print("✅ Nothing to commit — working tree is clean.")
        sys.exit(0)

    # Group changes by detected type
    groups = group_changes(status)
    sorted_groups = sort_groups(groups)

    # Display the grouping
    _display_groups(sorted_groups)

    if not no_interactive and not dry_run:
        # Allow user to override grouping
        sorted_groups = _interactive_override(sorted_groups)

    if dry_run:
        console.print("\n[dim][DRY RUN] No commits were created.[/dim]")
        sys.exit(0)

    # Commit each group
    commits_created = 0
    for commit_type, files in sorted_groups:
        # Validate hotfix type is only used on hotfix branches
        if commit_type == "hotfix" and not is_hotfix_allowed(current_branch):
            console.print(f"⚠️  Skipping 'hotfix' type — only valid on hotfix/* branches.")
            commit_type = "fix"  # Fallback to fix

        scope = detect_scope(files)

        # Get commit description from user
        if no_interactive:
            description = f"update {', '.join(files[:3])}"
            if len(files) > 3:
                description += f" and {len(files) - 3} more"
        else:
            scope_hint = f" (scope: {scope})" if scope else ""
            description = Prompt.ask(
                f"  [{commit_type}]{scope_hint} commit message"
            )

        # Format the commit message
        scope_part = f"({scope})" if scope else ""
        message = f"{commit_type}{scope_part}: {description}"

        # Validate the message
        if not validate(message):
            console.print(f"  ⚠️  Message doesn't conform: '{message}'")
            if not no_interactive:
                message = Prompt.ask("  Corrected message", default=message)
                if not validate(message):
                    console.print(f"  ❌ Still invalid. Skipping this group.")
                    continue

        # Stage and commit
        try:
            stage_files(files)
            sha = commit(message)
            console.print(f"  ✅ [{sha[:7]}] {message}")
            commits_created += 1
        except RuntimeError as e:
            console.print(f"  ❌ Failed: {e}")
            if not no_interactive:
                if not click.confirm("  Continue with remaining groups?", default=True):
                    sys.exit(1)

    # Summary
    console.print()
    if commits_created == 0:
        console.print("⚠️  No commits created.")
    elif commits_created == 1:
        console.print(f"✅ Created {commits_created} commit.")
    else:
        console.print(f"✅ Created {commits_created} commits.")


def _display_groups(sorted_groups: list[tuple[str, list[str]]]) -> None:
    """Display the detected change groups as a rich table."""
    table = Table(title="Detected Change Groups", border_style="dim")
    table.add_column("#", style="dim", width=3)
    table.add_column("Type", style="bold cyan")
    table.add_column("Files", style="white")
    table.add_column("Scope", style="dim")

    for i, (commit_type, files) in enumerate(sorted_groups, 1):
        scope = detect_scope(files) or ""
        # Show first 5 files, then "and N more"
        if len(files) <= 5:
            file_list = "\n".join(files)
        else:
            file_list = "\n".join(files[:5]) + f"\n[dim]... and {len(files) - 5} more[/dim]"
        table.add_row(str(i), commit_type, file_list, scope)

    console.print()
    console.print(table)
    console.print()


def _interactive_override(sorted_groups: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
    """Allow user to override the detected grouping."""
    if not click.confirm("Accept this grouping?", default=True):
        console.print("\n[dim]Entering override mode. For each file, enter the commit type or press Enter to keep.[/dim]")
        console.print(f"[dim]Valid types: {', '.join(sorted(VALID_TYPES))}[/dim]\n")

        # Flatten all files with their current assignments
        reassignments: dict[str, list[str]] = {}
        for commit_type, files in sorted_groups:
            for file_path in files:
                new_type = Prompt.ask(
                    f"  {file_path} [{commit_type}]",
                    default=commit_type,
                )
                if new_type not in VALID_TYPES:
                    console.print(f"  ⚠️  Invalid type '{new_type}', keeping '{commit_type}'")
                    new_type = commit_type
                reassignments.setdefault(new_type, []).append(file_path)

        # Re-sort by commit order
        order_map = {t: i for i, t in enumerate(COMMIT_ORDER)}
        sorted_groups = sorted(
            reassignments.items(),
            key=lambda item: order_map.get(item[0], len(COMMIT_ORDER)),
        )
        console.print()
        _display_groups(sorted_groups)

    return sorted_groups


if __name__ == "__main__":
    main()
