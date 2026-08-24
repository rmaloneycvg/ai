"""Integration tests for git-commit command."""

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.commit import main


@pytest.mark.integration
class TestCommitCommand:
    """Tests for the git-commit CLI in a real git repo."""

    def test_commits_new_file_as_feat(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        # Switch to a feature branch
        subprocess.run(
            ["git", "checkout", "-b", "feat/test-feature", "dev"],
            cwd=git_repo_with_branches,
            check=True,
            capture_output=True,
        )
        # Create a new source file
        src_dir = git_repo_with_branches / "src"
        src_dir.mkdir()
        (src_dir / "login.ts").write_text("export function login() {}\n")

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--no-interactive"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Created" in result.output or "✅" in result.output

        # Verify commit was made
        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=git_repo_with_branches,
            capture_output=True,
            text=True,
        )
        assert "feat" in log.stdout

    def test_commits_test_file_as_test(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        subprocess.run(
            ["git", "checkout", "-b", "feat/add-tests", "dev"],
            cwd=git_repo_with_branches,
            check=True,
            capture_output=True,
        )
        tests_dir = git_repo_with_branches / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_auth.py").write_text("def test_auth(): pass\n")

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--no-interactive"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=git_repo_with_branches,
            capture_output=True,
            text=True,
        )
        assert "test" in log.stdout

    def test_blocks_commit_on_protected_branch(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        # Should be on dev from fixture
        (git_repo_with_branches / "file.txt").write_text("change\n")

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--no-interactive"],
        )
        assert result.exit_code == 1
        assert "protected branch" in result.output.lower() or "Cannot commit" in result.output

    def test_nothing_to_commit(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        subprocess.run(
            ["git", "checkout", "-b", "feat/clean-branch", "dev"],
            cwd=git_repo_with_branches,
            check=True,
            capture_output=True,
        )
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--no-interactive"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Nothing to commit" in result.output or "clean" in result.output.lower()

    def test_dry_run_does_not_commit(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        subprocess.run(
            ["git", "checkout", "-b", "feat/dry-run", "dev"],
            cwd=git_repo_with_branches,
            check=True,
            capture_output=True,
        )
        (git_repo_with_branches / "src").mkdir(exist_ok=True)
        (git_repo_with_branches / "src" / "new.ts").write_text("x\n")

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--dry-run"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

        # Verify no commit was made
        log = subprocess.run(
            ["git", "log", "--oneline", "dev..HEAD"],
            cwd=git_repo_with_branches,
            capture_output=True,
            text=True,
        )
        assert log.stdout.strip() == ""
