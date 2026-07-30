"""Squash commits per type, rewrite non-conforming messages, and rebase onto target."""

import sys
from collections import defaultdict

import click
from rich.console import Console
from rich.table import Table

from src.lib.conventional import validate, parse, rewrite_message, VALID_TYPES
from src.lib.git_ops import get_current_branch, get_commits_ahead, _run, CommitInfo
from src.lib.ticket import extract_ticket_from_branch, format_pr_title, get_ticket_url

console = Console()


@click.command()
@click.option("--target", default="dev", show_default=True, help="Target branch to rebase onto.")
@click.option("--dry-run", is_flag=True, help="Show what would happen without modifying history.")
@click.option("--force", is_flag=True, help="Skip confirmations.")
def main(target: str, dry_run: bool, force: bool) -> None:
    """Prepare branch for PR: squash per type, rewrite messages, rebase onto target."""
    current = get_current_branch()

    # Guard: don't prepare PR from protected branches
    if current in ("prod", "staging", "dev"):
        console.print(f"❌ Cannot prepare PR from protected branch '[bold]{current}[/bold]'.")
        sys.exit(1)

    # Get commits ahead of target
    commits = get_commits_ahead(target)

    if not commits:
        console.print(f"✅ Already up to date with '[bold]{target}[/bold]'. Nothing to prepare.")
        sys.exit(0)

    # Check if already clean (all commits conform, single commit per type)
    all_valid = all(validate(c.message) for c in commits)
    type_groups = _group_commits_by_type(commits)
    already_clean = all_valid and all(len(group) <= 1 for group in type_groups.values())

    if already_clean and len(commits) <= len(type_groups):
        console.print(f"✅ Branch is already prepared ({len(commits)} clean commits).")
        _suggest_pr_title(current, commits, target)
        sys.exit(0)

    # Display current state
    console.print(f"\n[bold]Branch:[/bold] {current}")
    console.print(f"[bold]Target:[/bold] {target}")
    console.print(f"[bold]Commits ahead:[/bold] {len(commits)}\n")

    _display_commits(commits)

    # Show plan
    console.print("\n[bold]Preparation plan:[/bold]")
    console.print(f"  1. Squash {len(commits)} commits into {len(type_groups)} (one per type)")

    non_conforming = [c for c in commits if not validate(c.message)]
    if non_conforming:
        console.print(f"  2. Rewrite {len(non_conforming)} non-conforming message(s)")

    console.print(f"  3. Rebase onto '{target}'")
    console.print(f"  4. Force-push with --force-with-lease")
    console.print()

    if dry_run:
        _display_planned_result(commits, type_groups)
        console.print("\n[dim][DRY RUN] No changes were made.[/dim]")
        sys.exit(0)

    # Confirm
    if not force:
        console.print("[yellow]⚠️  This will rewrite git history on this branch.[/yellow]")
        console.print("[yellow]   Force-push will be required after this operation.[/yellow]")
        if not click.confirm("\nProceed?", default=True):
            console.print("Cancelled.")
            sys.exit(0)

    # Execute: soft reset to target merge-base, then recommit per type
    merge_base = _get_merge_base(target)
    if not merge_base:
        console.print(f"❌ Could not find merge base with '{target}'.")
        sys.exit(1)

    # Soft reset to merge base (keeps changes staged)
    result = _run(["reset", "--soft", merge_base])
    if result.returncode != 0:
        console.print(f"❌ Reset failed: {result.stderr}")
        sys.exit(1)

    # Recommit grouped by type
    new_commits = []
    for commit_type, group_commits in sorted(
        type_groups.items(),
        key=lambda x: list(VALID_TYPES).index(x[0]) if x[0] in VALID_TYPES else 99,
    ):
        # Compose a new message for this group
        messages = [c.message for c in group_commits]
        new_message = _compose_group_message(commit_type, messages)

        if not force:
            console.print(f"\n  Commit message for [bold cyan]{commit_type}[/bold cyan] group:")
            console.print(f"    {new_message}")
            edited = click.prompt("    Edit message (Enter to accept)", default=new_message, show_default=False)
            if edited.strip():
                new_message = edited.strip()

        # Commit (all changes are staged from the soft reset)
        result = _run(["commit", "-m", new_message, "--allow-empty"])
        if result.returncode != 0:
            # If nothing to commit for this group (all changes in other groups), skip
            if "nothing to commit" in result.stdout + result.stderr:
                continue
            console.print(f"  ❌ Commit failed: {result.stderr}")
            console.print("  Run 'git rebase --abort' or 'git reflog' to recover.")
            sys.exit(1)

        new_commits.append(new_message)
        console.print(f"  ✅ {new_message}")

    # Rebase onto target
    console.print(f"\n  Rebasing onto '{target}'...")
    result = _run(["rebase", target])
    if result.returncode != 0:
        console.print(f"\n  ⚠️  Rebase has conflicts. Resolve them with:")
        console.print(f"    1. Edit conflicted files")
        console.print(f"    2. git add <resolved-files>")
        console.print(f"    3. git rebase --continue")
        console.print(f"    Escape: git rebase --abort")
        sys.exit(1)

    console.print(f"  ✅ Rebased onto '{target}'")

    # Suggest PR title
    _suggest_pr_title(current, [CommitInfo(sha="", message=m) for m in new_commits], target)

    console.print(f"\n[yellow]⚠️  Run: git push --force-with-lease[/yellow]")


def _group_commits_by_type(commits: list[CommitInfo]) -> dict[str, list[CommitInfo]]:
    """Group commits by their conventional type. Non-conforming → 'unknown'."""
    groups: dict[str, list[CommitInfo]] = defaultdict(list)
    for c in commits:
        parsed = parse(c.message)
        if parsed:
            groups[parsed["type"]].append(c)
        else:
            # Try to guess type from the message
            rewritten = rewrite_message(c.message)
            if rewritten:
                guessed = parse(rewritten)
                if guessed:
                    groups[guessed["type"]].append(c)
                    continue
            groups["chore"].append(c)  # Default non-conforming to chore
    return dict(groups)


def _compose_group_message(commit_type: str, messages: list[str]) -> str:
    """Compose a single commit message from a group of messages."""
    if len(messages) == 1:
        msg = messages[0]
        if validate(msg):
            return msg
        rewritten = rewrite_message(msg)
        return rewritten if rewritten else f"{commit_type}: {msg}"

    # Multiple messages — combine descriptions
    descriptions = []
    for msg in messages:
        parsed = parse(msg)
        if parsed:
            descriptions.append(parsed["description"])
        else:
            # Strip any type-like prefix and use raw
            descriptions.append(msg.split(":", 1)[-1].strip() if ":" in msg else msg)

    # If all descriptions are similar, use the most descriptive one
    if len(set(descriptions)) == 1:
        return f"{commit_type}: {descriptions[0]}"

    # Combine meaningfully — use first substantial one + note count
    substantial = [d for d in descriptions if d.lower() not in ("wip", "tmp", "temp", "typo", "save")]
    if substantial:
        combined = substantial[0]
        if len(substantial) > 1:
            combined += f" (+{len(substantial) - 1} related changes)"
        return f"{commit_type}: {combined}"

    return f"{commit_type}: accumulated changes"


def _get_merge_base(target: str) -> str | None:
    """Get the merge base between current branch and target."""
    result = _run(["merge-base", "HEAD", target])
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _display_commits(commits: list[CommitInfo]) -> None:
    """Display commits in a table."""
    table = Table(title="Current Commits", border_style="dim")
    table.add_column("SHA", style="dim", width=8)
    table.add_column("Message")
    table.add_column("Valid?", width=6)

    for c in commits:
        valid = "✅" if validate(c.message) else "❌"
        table.add_row(c.sha[:7], c.message, valid)

    console.print(table)


def _display_planned_result(commits: list[CommitInfo], type_groups: dict[str, list[CommitInfo]]) -> None:
    """Show what the squashed result would look like."""
    console.print("\n[bold]Planned result:[/bold]")
    table = Table(border_style="dim")
    table.add_column("Type", style="bold cyan")
    table.add_column("New Message")
    table.add_column("Squashes", style="dim")

    for commit_type, group in type_groups.items():
        messages = [c.message for c in group]
        new_msg = _compose_group_message(commit_type, messages)
        table.add_row(commit_type, new_msg, str(len(group)))

    console.print(table)


def _suggest_pr_title(branch: str, commits: list[CommitInfo], target: str) -> None:
    """Suggest a PR title based on branch and commits."""
    ticket = extract_ticket_from_branch(branch)
    ticket_url = get_ticket_url()

    # Determine primary type and scope from commits
    primary_type = "feat"
    description = ""
    for c in commits:
        parsed = parse(c.message)
        if parsed:
            primary_type = parsed["type"]
            description = parsed["description"]
            break

    if not description:
        # Extract from branch name
        parts = branch.split("/", 1)
        if len(parts) == 2:
            description = parts[1].replace("-", " ")
            if ticket:
                description = description.replace(ticket, "").strip(" -")

    pr_title = format_pr_title(primary_type, description, ticket=ticket)
    console.print(f"\n[bold]Suggested PR title:[/bold] {pr_title}")
    if ticket and ticket_url:
        console.print(f"[dim]Ticket: {ticket_url}/browse/{ticket}[/dim]")


if __name__ == "__main__":
    main()
