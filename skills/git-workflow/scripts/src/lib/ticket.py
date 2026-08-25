"""Ticket system integration: URL detection, ticket ID extraction, and formatting."""

from __future__ import annotations

import os
import re


# Ticket ID pattern: uppercase letters + hyphen + digits (e.g., PROJ-123)
TICKET_PATTERN = re.compile(r"[A-Z]+-\d+")


def get_ticket_url() -> str | None:
    """Get the ticket system URL from environment.

    Checks TICKET_SYSTEM_URL environment variable.

    Returns:
        The URL string if set, None otherwise.
    """
    url = os.environ.get("TICKET_SYSTEM_URL", "").strip()
    return url if url else None


def detect_ticket_system(url: str) -> str:
    """Detect the ticket system type from its URL.

    Args:
        url: The ticket system URL.

    Returns:
        One of: 'jira', 'linear', 'shortcut', 'youtrack', 'generic'
    """
    url_lower = url.lower()
    if "atlassian.net" in url_lower:
        return "jira"
    elif "linear.app" in url_lower:
        return "linear"
    elif "shortcut.com" in url_lower:
        return "shortcut"
    elif "youtrack" in url_lower:
        return "youtrack"
    return "generic"


def extract_ticket_from_branch(branch_name: str) -> str | None:
    """Extract a ticket ID from a branch name.

    Looks for patterns like PROJ-123 in the branch name.

    Args:
        branch_name: The git branch name.

    Returns:
        The ticket ID string, or None if not found.
    """
    match = TICKET_PATTERN.search(branch_name)
    return match.group(0) if match else None


def format_branch_name(
    branch_type: str,
    description: str,
    ticket: str | None = None,
) -> str:
    """Format a branch name following team conventions.

    Args:
        branch_type: Conventional commit type (feat, fix, etc.)
        description: Human-readable description (will be kebab-cased).
        ticket: Optional ticket ID (e.g., PROJ-123).

    Returns:
        Formatted branch name.
    """
    # Kebab-case the description
    slug = re.sub(r"[^a-z0-9]+", "-", description.lower()).strip("-")

    if ticket:
        return f"{branch_type}/{ticket.upper()}-{slug}"
    return f"{branch_type}/{slug}"


def format_pr_title(
    commit_type: str,
    description: str,
    scope: str | None = None,
    ticket: str | None = None,
) -> str:
    """Format a PR title following team conventions.

    Args:
        commit_type: Conventional commit type.
        description: PR description.
        scope: Optional scope.
        ticket: Optional ticket ID.

    Returns:
        Formatted PR title string.
    """
    scope_part = f"({scope})" if scope else ""
    ticket_part = f"{ticket.upper()} " if ticket else ""
    return f"{commit_type}{scope_part}: {ticket_part}{description}"


def validate_branch_name(branch_name: str) -> tuple[bool, str]:
    """Validate a branch name against team conventions.

    Args:
        branch_name: The branch name to validate.

    Returns:
        Tuple of (is_valid, error_message). error_message is empty if valid.
    """
    from src.lib.conventional import VALID_TYPES

    # Protected branches are valid by definition
    if branch_name in ("prod", "staging", "dev", "main", "master"):
        return True, ""

    # Must have type prefix
    parts = branch_name.split("/", 1)
    if len(parts) != 2:
        return False, f"Branch must be formatted as '<type>/<description>'. Got: '{branch_name}'"

    branch_type, rest = parts
    if branch_type not in VALID_TYPES:
        return False, (
            f"Invalid branch type '{branch_type}'. "
            f"Valid types: {', '.join(sorted(VALID_TYPES))}"
        )

    if not rest:
        return False, "Branch description cannot be empty."

    # Check for valid characters (kebab-case + ticket IDs)
    if not re.match(r"^[A-Za-z0-9][-A-Za-z0-9]*$", rest):
        return False, f"Branch description must be kebab-case. Got: '{rest}'"

    # Length check
    if len(branch_name) > 80:
        return False, f"Branch name too long ({len(branch_name)} chars, max 80)."

    return True, ""


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.lib.ticket validate-branch")
        sys.exit(1)

    command = sys.argv[1]
    if command == "validate-branch":
        from src.lib.git_ops import get_current_branch

        branch = get_current_branch()
        is_valid, error = validate_branch_name(branch)

        ticket_url = get_ticket_url()
        if not is_valid:
            if ticket_url:
                print(f"❌ {error}")
                sys.exit(1)
            else:
                print(f"⚠️  {error} (non-blocking — TICKET_SYSTEM_URL not set)")
                sys.exit(0)
        sys.exit(0)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
