"""Shared pytest fixtures for git workflow tests."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository with an initial commit."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    # Create initial commit
    readme = tmp_path / "README.md"
    readme.write_text("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: initial commit"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    return tmp_path


@pytest.fixture
def git_repo_with_branches(git_repo: Path) -> Path:
    """Create a git repo with prod, staging, and dev branches."""
    for branch in ("prod", "staging", "dev"):
        subprocess.run(
            ["git", "branch", branch],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )
    subprocess.run(
        ["git", "checkout", "dev"],
        cwd=git_repo,
        check=True,
        capture_output=True,
    )
    return git_repo


@pytest.fixture
def env_with_ticket_url(monkeypatch: pytest.MonkeyPatch) -> str:
    """Set TICKET_SYSTEM_URL to a Jira-like URL."""
    url = "https://mycompany.atlassian.net"
    monkeypatch.setenv("TICKET_SYSTEM_URL", url)
    return url


@pytest.fixture
def env_without_ticket_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure TICKET_SYSTEM_URL is not set."""
    monkeypatch.delenv("TICKET_SYSTEM_URL", raising=False)
