"""Integration tests for git-hotfix command."""

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.hotfix import main


@pytest.mark.integration
class TestHotfixCommand:
    """Tests for the git-hotfix CLI in a real git repo."""

    def test_creates_hotfix_branch_from_prod(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--description", "fix-payment-timeout"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "hotfix/fix-payment-timeout" in result.output

        # Verify we're on the hotfix branch
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=git_repo_with_branches,
            capture_output=True,
            text=True,
        )
        assert branch.stdout.strip() == "hotfix/fix-payment-timeout"

    def test_creates_hotfix_with_ticket(self, git_repo_with_branches, env_with_ticket_url, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--description", "payment-crash", "--ticket", "INC-789"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "INC-789" in result.output

    def test_resumes_existing_hotfix(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        # Create the hotfix branch first
        subprocess.run(
            ["git", "checkout", "-b", "hotfix/fix-crash", "prod"],
            cwd=git_repo_with_branches,
            check=True,
            capture_output=True,
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--description", "fix-crash"],
            input="4\n",  # Choose "Show next steps and exit"
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Resuming hotfix" in result.output or "Next steps" in result.output

    def test_fails_without_prod_branch(self, git_repo, monkeypatch):
        """Test that hotfix fails gracefully when prod doesn't exist."""
        monkeypatch.chdir(git_repo)
        subprocess.run(
            ["git", "checkout", "-b", "feat/something"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--description", "fix-thing"],
        )
        assert result.exit_code == 1
        assert "prod" in result.output.lower()
