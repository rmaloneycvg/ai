"""Git tools — mirrors Kiro MCP git server functionality."""

from __future__ import annotations

import subprocess

from langchain_core.tools import tool


@tool
def git_status(cwd: str = ".") -> str:
    """Get parsed git status showing staged, unstaged, and untracked files.

    Args:
        cwd: Working directory (defaults to current).
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"

        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        staged, unstaged, untracked = [], [], []

        for line in lines:
            if not line:
                continue
            index_status = line[0]
            work_status = line[1]
            filename = line[3:]

            if index_status in "MADRC":
                staged.append({"status": index_status, "file": filename})
            if work_status in "MD":
                unstaged.append({"status": work_status, "file": filename})
            if index_status == "?" and work_status == "?":
                untracked.append(filename)

        import json

        return json.dumps(
            {
                "staged": staged,
                "unstaged": unstaged,
                "untracked": untracked,
                "clean": len(lines) == 0,
            },
            indent=2,
        )
    except subprocess.TimeoutExpired:
        return "Error: git status timed out"
    except Exception as e:
        return f"Error: {e}"


@tool
def git_diff(path: str = "", staged: bool = False, cwd: str = ".") -> str:
    """Show git diff for working tree or staged changes.

    Args:
        path: Specific file path to diff (empty for all).
        staged: If True, show staged changes (--cached).
        cwd: Working directory.
    """
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--cached")
    if path:
        cmd.extend(["--", path])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        return result.stdout or "(no diff)"
    except Exception as e:
        return f"Error: {e}"


@tool
def git_log(count: int = 10, oneline: bool = True, cwd: str = ".") -> str:
    """Show recent git log entries.

    Args:
        count: Number of commits to show.
        oneline: If True, show compact one-line format.
        cwd: Working directory.
    """
    cmd = ["git", "log", f"-{count}"]
    if oneline:
        cmd.append("--oneline")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        return result.stdout or "(no commits)"
    except Exception as e:
        return f"Error: {e}"
