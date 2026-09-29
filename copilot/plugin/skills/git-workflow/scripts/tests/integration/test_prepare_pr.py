"""Integration tests for git-prepare-pr command."""

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.prepare_pr import main


@pytest.mark.integration
class TestPreparePrCommand:
    """Tests for the git-prepare-pr CLI in a real git repo."""

    def _make_commits(self, repo: Path, commits: list[tuple[str, str, str]]) -> None:
        """Helper: create files and commit them.

        Args:
            commits: list of (filename, content, message) tuples.
        """
        for filename, content, message in commits:
            filepath = repo / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content)
            subprocess.run(["git", "add", filename], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=repo,
                check=True,
                capture_output=True,
            )

    def test_squashes_multiple_commits_per_type(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        subprocess.run(
            ["git", "checkout", "-b", "feat/multi-commit", "dev"],
            cwd=git_repo_with_branches,
            check=True,
            capture_output=True,
        )
        self._make_commits(git_repo_with_branches, [
            ("src/a.ts", "a", "feat: add feature A"),
            ("src/b.ts", "b", "feat: add feature B"),
            ("tests/test_a.py", "t", "test: add tests"),
        ])

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--target", "dev", "--force"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Verify squashed commits
        log = subprocess.run(
            ["git", "log", "--oneline", "dev..HEAD"],
            cwd=git_repo_with_branches,
            capture_output=True,
            text=True,
        )
        lines = [l for l in log.stdout.strip().splitlines() if l]
        # Should have 2 commits: one feat, one test
        assert len(lines) == 2

    def test_already_clean_branch(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        subprocess.run(
            ["git", "checkout", "-b", "feat/clean", "dev"],
            cwd=git_repo_with_branches,
            check=True,
            capture_output=True,
        )
        self._make_commits(git_repo_with_branches, [
            ("src/a.ts", "a", "feat: single clean commit"),
        ])

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--target", "dev", "--force"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "already prepared" in result.output.lower()

    def test_blocks_on_protected_branch(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--target", "dev"],
        )
        assert result.exit_code == 1
        assert "protected branch" in result.output.lower() or "Cannot prepare" in result.output

    def test_nothing_to_prepare(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        subprocess.run(
            ["git", "checkout", "-b", "feat/empty", "dev"],
            cwd=git_repo_with_branches,
            check=True,
            capture_output=True,
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--target", "dev"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "up to date" in result.output.lower()

    def test_dry_run_does_not_modify(self, git_repo_with_branches, monkeypatch):
        monkeypatch.chdir(git_repo_with_branches)
        subprocess.run(
            ["git", "checkout", "-b", "feat/dry", "dev"],
            cwd=git_repo_with_branches,
            check=True,
            capture_output=True,
        )
        self._make_commits(git_repo_with_branches, [
            ("src/a.ts", "a", "feat: first"),
            ("src/b.ts", "b", "feat: second"),
        ])

        # Get current HEAD before dry run
        head_before = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=git_repo_with_branches,
            capture_output=True,
            text=True,
        ).stdout.strip()

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--target", "dev", "--dry-run"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

        # HEAD should not have changed
        head_after = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=git_repo_with_branches,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert head_before == head_after
