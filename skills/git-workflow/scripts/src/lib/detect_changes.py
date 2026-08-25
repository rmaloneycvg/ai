"""File path → commit type heuristic detection and grouping."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from src.lib.git_ops import GitStatus


@dataclass
class HeuristicRule:
    """A rule that maps file patterns to a commit type."""

    patterns: list[str]  # Glob-like patterns
    commit_type: str
    confidence: str  # 'high', 'medium', 'low'


# Ordered by priority — first match wins
HEURISTIC_RULES: list[HeuristicRule] = [
    HeuristicRule(
        patterns=["tests/", "test_*", "*_test.*", "*.test.*", "*.spec.*"],
        commit_type="test",
        confidence="high",
    ),
    HeuristicRule(
        patterns=[
            ".github/workflows/",
            ".gitlab-ci*",
            "Jenkinsfile",
            ".circleci/",
            "bitbucket-pipelines.yml",
        ],
        commit_type="ci",
        confidence="high",
    ),
    HeuristicRule(
        patterns=["docs/", "CHANGELOG*", "LICENSE"],
        commit_type="docs",
        confidence="high",
    ),
    HeuristicRule(
        patterns=["*.md"],
        commit_type="docs",
        confidence="high",
    ),
    HeuristicRule(
        patterns=[
            "Dockerfile*",
            "docker-compose*",
            "k8s/",
            "helm/",
            "Tiltfile",
            "*.tf",
        ],
        commit_type="build",
        confidence="high",
    ),
    HeuristicRule(
        patterns=[
            "package.json",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "requirements.txt",
            "poetry.lock",
            "package-lock.json",
            "uv.lock",
        ],
        commit_type="build",
        confidence="medium",
    ),
    HeuristicRule(
        patterns=["*.css", "*.scss", "*.less"],
        commit_type="style",
        confidence="medium",
    ),
    HeuristicRule(
        patterns=[
            "scripts/",
            "Makefile",
            ".gitignore",
            ".editorconfig",
            ".prettierrc*",
            ".eslintrc*",
        ],
        commit_type="chore",
        confidence="medium",
    ),
]


def _matches_pattern(file_path: str, pattern: str) -> bool:
    """Check if a file path matches a heuristic pattern.

    Supports:
    - Directory prefix: 'tests/' matches 'tests/foo/bar.py'
    - Glob prefix: 'test_*' matches 'test_foo.py'
    - Glob suffix: '*.test.*' matches 'foo.test.ts'
    - Exact match: 'Makefile' matches 'Makefile'
    """
    path = PurePosixPath(file_path)
    name = path.name

    # Directory prefix match
    if pattern.endswith("/"):
        return file_path.startswith(pattern) or f"/{pattern}" in f"/{file_path}"

    # Glob patterns
    if "*" in pattern:
        # Convert glob to regex
        regex = pattern.replace(".", r"\.").replace("*", ".*")
        return bool(re.match(regex, name))

    # Exact filename match
    return name == pattern


def detect_type(file_path: str, is_new: bool = False) -> tuple[str, str]:
    """Detect the commit type for a single file based on path heuristics.

    Args:
        file_path: The path of the changed file.
        is_new: Whether the file is newly created (untracked or added).

    Returns:
        Tuple of (commit_type, confidence).
    """
    for rule in HEURISTIC_RULES:
        for pattern in rule.patterns:
            if _matches_pattern(file_path, pattern):
                return rule.commit_type, rule.confidence

    # Default heuristics for source files
    if is_new:
        return "feat", "medium"
    else:
        return "fix", "low"


def detect_scope(files: list[str]) -> str | None:
    """Auto-detect scope from the common path prefix of a file group.

    Args:
        files: List of file paths in a commit group.

    Returns:
        A scope string, or None if files span too many directories.
    """
    if not files:
        return None

    # Get the first meaningful directory component for each file
    dirs = set()
    for f in files:
        parts = PurePosixPath(f).parts
        if len(parts) >= 2:
            # Use second component if first is a common root directory
            if parts[0] in ("src", "lib", "app", "api", "services", "tests", "test"):
                dirs.add(parts[1] if len(parts) > 1 else parts[0])
            else:
                dirs.add(parts[0])
        else:
            dirs.add(parts[0] if parts else "")

    # Only return scope if all files share the same directory
    if len(dirs) == 1:
        scope = dirs.pop()
        # Don't use file extensions as scope
        if "." not in scope:
            return scope

    return None


def group_changes(status: GitStatus) -> dict[str, list[str]]:
    """Group changed files by detected commit type.

    Args:
        status: Parsed git status output.

    Returns:
        Dict mapping commit_type to list of file paths.
    """
    groups: dict[str, list[str]] = {}

    # Process staged files
    for entry in status.staged:
        is_new = entry.index == "A"
        commit_type, _ = detect_type(entry.path, is_new=is_new)
        groups.setdefault(commit_type, []).append(entry.path)

    # Process unstaged files
    for entry in status.unstaged:
        commit_type, _ = detect_type(entry.path, is_new=False)
        # Avoid duplicates if file is both staged and unstaged
        if entry.path not in groups.get(commit_type, []):
            groups.setdefault(commit_type, []).append(entry.path)

    # Process untracked files (always new)
    for path in status.untracked:
        commit_type, _ = detect_type(path, is_new=True)
        groups.setdefault(commit_type, []).append(path)

    return groups


# Commit order — infrastructure first, features last
COMMIT_ORDER: list[str] = [
    "ci",
    "build",
    "chore",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "fix",
    "feat",
    "hotfix",
    "revert",
]


def sort_groups(groups: dict[str, list[str]]) -> list[tuple[str, list[str]]]:
    """Sort commit groups by the standard commit order.

    Args:
        groups: Dict mapping commit_type to file list.

    Returns:
        List of (type, files) tuples in commit order.
    """
    order_map = {t: i for i, t in enumerate(COMMIT_ORDER)}
    return sorted(
        groups.items(),
        key=lambda item: order_map.get(item[0], len(COMMIT_ORDER)),
    )
