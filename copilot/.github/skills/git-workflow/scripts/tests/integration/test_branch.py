"""Integration tests for git-branch command."""

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.branch import main


@pytest.mark.integration
class TestBranchCommand:
    """Tests for the git-branch CLI in a real git repo."""

    def test_creates_feature_branch_from_dev(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--type", "feat", "--description", "add-login", "--from", "dev"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "add-login" in result.output

        # Verify we're on the new branch
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=git_repo_with_branches,
            capture_output=True,
            text=True,
        )
        assert branch.stdout.strip() == "feat/add-login"

    def test_creates_hotfix_branch_from_prod(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--type", "hotfix", "--description", "fix-payment"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "hotfix/fix-payment" in result.output

    def test_creates_branch_with_ticket(self, git_repo_with_branches, env_with_ticket_url, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--type", "feat", "--description", "add auth", "--ticket", "PROJ-123", "--from", "dev"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "PROJ-123" in result.output

    def test_idempotent_when_already_on_branch(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        runner = CliRunner()
        # Create first
        runner.invoke(
            main,
            ["--type", "feat", "--description", "my-feature", "--from", "dev"],
            catch_exceptions=False,
        )
        # Run again — should be a no-op
        result = runner.invoke(
            main,
            ["--type", "feat", "--description", "my-feature", "--from", "dev"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Already on branch" in result.output

    def test_rejects_invalid_type(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--type", "invalid", "--description", "test"],
        )
        assert result.exit_code != 0
