"""Conventional commit validation and message rewriting."""

import re

VALID_TYPES: set[str] = {
    "feat",
    "fix",
    "chore",
    "perf",
    "docs",
    "build",
    "revert",
    "style",
    "refactor",
    "ci",
    "test",
    "hotfix",
}

# Regex: type(optional-scope): description
COMMIT_PATTERN = re.compile(
    r"^(?P<type>" + "|".join(VALID_TYPES) + r")"
    r"(?:\((?P<scope>[a-z0-9_-]+)\))?"
    r":\s(?P<description>.+)$"
)


def validate(message: str) -> bool:
    """Validate a commit message against conventional commit format.

    Args:
        message: The first line (subject) of the commit message.

    Returns:
        True if the message conforms to conventional commit format.
    """
    subject = message.split("\n", 1)[0].strip()
    return COMMIT_PATTERN.match(subject) is not None


def parse(message: str) -> dict[str, str | None] | None:
    """Parse a conventional commit message into its components.

    Returns:
        Dict with 'type', 'scope', 'description' keys, or None if invalid.
    """
    subject = message.split("\n", 1)[0].strip()
    match = COMMIT_PATTERN.match(subject)
    if not match:
        return None
    return {
        "type": match.group("type"),
        "scope": match.group("scope"),
        "description": match.group("description"),
    }


def rewrite_message(message: str) -> str | None:
    """Attempt to rewrite a non-conforming message into conventional format.

    Uses keyword heuristics to guess the type. Returns None if no guess is possible.

    Args:
        message: The non-conforming commit message.

    Returns:
        A rewritten message in conventional format, or None if type can't be guessed.
    """
    subject = message.split("\n", 1)[0].strip().lower()

    # Messages that should be dropped during squash
    drop_patterns = {"wip", "work in progress", "tmp", "temp", "typo", "save"}
    if subject in drop_patterns:
        return None

    # Keyword → type mapping (order matters — first match wins)
    keyword_map: dict[str, str] = {
        "fix": "fix",
        "bug": "fix",
        "correct": "fix",
        "resolve": "fix",
        "add": "feat",
        "implement": "feat",
        "introduce": "feat",
        "new": "feat",
        "test": "test",
        "spec": "test",
        "refactor": "refactor",
        "restructure": "refactor",
        "extract": "refactor",
        "rename": "refactor",
        "doc": "docs",
        "readme": "docs",
        "comment": "docs",
        "ci": "ci",
        "pipeline": "ci",
        "workflow": "ci",
        "upgrade": "build",
        "depend": "build",
        "format": "style",
        "lint": "style",
        "prettier": "style",
        "perf": "perf",
        "optim": "perf",
        "speed": "perf",
        "revert": "revert",
        "update": "chore",
    }

    guessed_type: str | None = None
    for keyword, commit_type in keyword_map.items():
        # Use word boundary check to avoid substring false positives
        # e.g., "ci" should not match "dependencies"
        if re.search(r"\b" + re.escape(keyword), subject):
            guessed_type = commit_type
            break

    if guessed_type is None:
        return None

    # Clean up the description — use the original message as description
    description = message.split("\n", 1)[0].strip()

    return f"{guessed_type}: {description}"


def is_hotfix_allowed(branch_name: str) -> bool:
    """Check if the 'hotfix' type is allowed on the given branch.

    Args:
        branch_name: Current git branch name.

    Returns:
        True if the branch is a hotfix branch.
    """
    return branch_name.startswith("hotfix/")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.lib.conventional validate-file <commit-msg-file>")
        sys.exit(1)

    command = sys.argv[1]
    if command == "validate-file" and len(sys.argv) >= 3:
        msg_file = sys.argv[2]
        with open(msg_file) as f:
            msg = f.read().strip()
        if validate(msg):
            sys.exit(0)
        else:
            suggestion = rewrite_message(msg)
            print(f"❌ Invalid commit message format: '{msg}'")
            print(f"   Expected: <type>(<scope>): <description>")
            print(f"   Valid types: {', '.join(sorted(VALID_TYPES))}")
            if suggestion:
                print(f"   Suggestion: {suggestion}")
            sys.exit(1)
    elif command == "validate" and len(sys.argv) >= 3:
        msg = " ".join(sys.argv[2:])
        result = validate(msg)
        print(result)
        sys.exit(0 if result else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
