"""Git subprocess wrappers with typed results and idempotent checks."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StatusEntry:
    """A single file entry from git status."""

    path: str
    index: str  # Status in index (staging area)
    work_tree: str  # Status in working tree


@dataclass
class GitStatus:
    """Parsed git status output."""

    staged: list[StatusEntry] = field(default_factory=list)
    unstaged: list[StatusEntry] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)


@dataclass
class CommitInfo:
    """Minimal info about a commit."""

    sha: str
    message: str


def _run(args: list[str], cwd: Path | str | None = None) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the result."""
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def get_status(cwd: Path | str | None = None) -> GitStatus:
    """Get parsed git status.

    Returns:
        GitStatus with staged, unstaged, and untracked files.
    """
    result = _run(["status", "--porcelain=v1"], cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"git status failed: {result.stderr}")

    status = GitStatus()
    for line in result.stdout.splitlines():
        if not line:
            continue
        index = line[0]
        work_tree = line[1]
        path = line[3:]

        if index == "?":
            status.untracked.append(path)
        else:
            if index not in (" ", "?"):
                status.staged.append(StatusEntry(path=path, index=index, work_tree=work_tree))
            if work_tree not in (" ", "?"):
                status.unstaged.append(StatusEntry(path=path, index=index, work_tree=work_tree))

    return status


def get_current_branch(cwd: Path | str | None = None) -> str:
    """Get the name of the current branch.

    Returns:
        Branch name string, or 'HEAD' if detached.
    """
    result = _run(["branch", "--show-current"], cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"git branch --show-current failed: {result.stderr}")
    branch = result.stdout.strip()
    return branch if branch else "HEAD"


def branch_exists(name: str, cwd: Path | str | None = None) -> bool:
    """Check if a branch exists locally.

    Args:
        name: Branch name to check.

    Returns:
        True if the branch exists.
    """
    result = _run(["rev-parse", "--verify", f"refs/heads/{name}"], cwd=cwd)
    return result.returncode == 0


def create_branch(name: str, from_branch: str, cwd: Path | str | None = None) -> None:
    """Create a new branch from the specified base and switch to it.

    Idempotent: if already on the target branch, does nothing.

    Args:
        name: Name of the new branch.
        from_branch: Base branch to create from.
    """
    current = get_current_branch(cwd=cwd)
    if current == name:
        return  # Already on target branch

    if branch_exists(name, cwd=cwd):
        # Branch exists, just switch to it
        result = _run(["checkout", name], cwd=cwd)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to checkout '{name}': {result.stderr}")
        return

    result = _run(["checkout", "-b", name, from_branch], cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create branch '{name}' from '{from_branch}': {result.stderr}")


def get_commits_ahead(target: str, cwd: Path | str | None = None) -> list[CommitInfo]:
    """Get commits on current branch that are not in the target branch.

    Args:
        target: Branch to compare against.

    Returns:
        List of CommitInfo for commits ahead of target.
    """
    result = _run(["log", f"{target}..HEAD", "--oneline", "--format=%H %s"], cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"git log failed: {result.stderr}")

    commits = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        sha, message = line.split(" ", 1)
        commits.append(CommitInfo(sha=sha, message=message))
    return commits


def is_submodule(cwd: Path | str | None = None) -> bool:
    """Detect if the current directory is inside a git submodule.

    Returns:
        True if inside a submodule.
    """
    result = _run(["rev-parse", "--show-superproject-working-tree"], cwd=cwd)
    return result.returncode == 0 and bool(result.stdout.strip())


def stage_files(files: list[str], cwd: Path | str | None = None) -> None:
    """Stage specific files for commit.

    Args:
        files: List of file paths to stage.
    """
    if not files:
        return
    result = _run(["add"] + files, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"git add failed: {result.stderr}")


def commit(message: str, cwd: Path | str | None = None) -> str:
    """Create a commit with the given message.

    Args:
        message: Commit message (will be validated by hook).

    Returns:
        The SHA of the created commit.
    """
    result = _run(["commit", "-m", message], cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"git commit failed: {result.stderr}")

    # Get the SHA of the new commit
    sha_result = _run(["rev-parse", "HEAD"], cwd=cwd)
    return sha_result.stdout.strip()
