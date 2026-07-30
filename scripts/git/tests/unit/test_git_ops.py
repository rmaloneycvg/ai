"""Unit tests for git subprocess wrappers."""

import subprocess

import pytest
from unittest.mock import patch, MagicMock

from src.lib.git_ops import (
    get_status,
    get_current_branch,
    branch_exists,
    create_branch,
    get_commits_ahead,
    is_submodule,
    stage_files,
    commit,
    GitStatus,
    StatusEntry,
    CommitInfo,
)


@pytest.mark.unit
class TestGetStatus:
    """Tests for get_status() function."""

    @patch("src.lib.git_ops._run")
    def test_parses_staged_files(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="A  src/new.ts\nM  src/mod.ts\n")
        status = get_status()
        assert len(status.staged) == 2
        assert status.staged[0].path == "src/new.ts"
        assert status.staged[0].index == "A"
        assert status.staged[1].path == "src/mod.ts"
        assert status.staged[1].index == "M"

    @patch("src.lib.git_ops._run")
    def test_parses_unstaged_files(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=" M src/changed.ts\n")
        status = get_status()
        assert len(status.unstaged) == 1
        assert status.unstaged[0].path == "src/changed.ts"

    @patch("src.lib.git_ops._run")
    def test_parses_untracked_files(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="?? new_file.ts\n?? another.ts\n")
        status = get_status()
        assert status.untracked == ["new_file.ts", "another.ts"]

    @patch("src.lib.git_ops._run")
    def test_empty_status(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        status = get_status()
        assert status.staged == []
        assert status.unstaged == []
        assert status.untracked == []

    @patch("src.lib.git_ops._run")
    def test_raises_on_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="fatal: not a git repo")
        with pytest.raises(RuntimeError, match="git status failed"):
            get_status()

    @patch("src.lib.git_ops._run")
    def test_mixed_status(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="A  src/new.ts\n M src/mod.ts\n?? untracked.txt\n"
        )
        status = get_status()
        assert len(status.staged) == 1
        assert len(status.unstaged) == 1
        assert len(status.untracked) == 1


@pytest.mark.unit
class TestGetCurrentBranch:
    """Tests for get_current_branch() function."""

    @patch("src.lib.git_ops._run")
    def test_returns_branch_name(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="feat/add-login\n")
        assert get_current_branch() == "feat/add-login"

    @patch("src.lib.git_ops._run")
    def test_returns_head_when_detached(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="\n")
        assert get_current_branch() == "HEAD"

    @patch("src.lib.git_ops._run")
    def test_raises_on_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="fatal: error")
        with pytest.raises(RuntimeError):
            get_current_branch()


@pytest.mark.unit
class TestBranchExists:
    """Tests for branch_exists() function."""

    @patch("src.lib.git_ops._run")
    def test_returns_true_when_exists(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert branch_exists("feat/my-branch") is True

    @patch("src.lib.git_ops._run")
    def test_returns_false_when_not_exists(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        assert branch_exists("nonexistent") is False


@pytest.mark.unit
class TestGetCommitsAhead:
    """Tests for get_commits_ahead() function."""

    @patch("src.lib.git_ops._run")
    def test_parses_commits(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc1234 feat: add login\ndef5678 test: add auth tests\n",
        )
        commits = get_commits_ahead("dev")
        assert len(commits) == 2
        assert commits[0].sha == "abc1234"
        assert commits[0].message == "feat: add login"
        assert commits[1].sha == "def5678"
        assert commits[1].message == "test: add auth tests"

    @patch("src.lib.git_ops._run")
    def test_empty_when_no_commits_ahead(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        commits = get_commits_ahead("dev")
        assert commits == []

    @patch("src.lib.git_ops._run")
    def test_raises_on_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="fatal: bad ref")
        with pytest.raises(RuntimeError):
            get_commits_ahead("dev")


@pytest.mark.unit
class TestIsSubmodule:
    """Tests for is_submodule() function."""

    @patch("src.lib.git_ops._run")
    def test_returns_true_in_submodule(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="/parent/repo\n")
        assert is_submodule() is True

    @patch("src.lib.git_ops._run")
    def test_returns_false_in_normal_repo(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="\n")
        assert is_submodule() is False

    @patch("src.lib.git_ops._run")
    def test_returns_false_on_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert is_submodule() is False


@pytest.mark.unit
class TestCreateBranch:
    """Tests for create_branch() function."""

    @patch("src.lib.git_ops.branch_exists")
    @patch("src.lib.git_ops.get_current_branch")
    @patch("src.lib.git_ops._run")
    def test_creates_new_branch(self, mock_run, mock_current, mock_exists):
        mock_current.return_value = "dev"
        mock_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)
        create_branch("feat/add-login", "dev")
        mock_run.assert_called_once_with(["checkout", "-b", "feat/add-login", "dev"], cwd=None)

    @patch("src.lib.git_ops.get_current_branch")
    def test_noop_when_already_on_branch(self, mock_current):
        mock_current.return_value = "feat/add-login"
        # Should not raise or call any git commands
        create_branch("feat/add-login", "dev")

    @patch("src.lib.git_ops.branch_exists")
    @patch("src.lib.git_ops.get_current_branch")
    @patch("src.lib.git_ops._run")
    def test_switches_to_existing_branch(self, mock_run, mock_current, mock_exists):
        mock_current.return_value = "dev"
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        create_branch("feat/add-login", "dev")
        mock_run.assert_called_once_with(["checkout", "feat/add-login"], cwd=None)

    @patch("src.lib.git_ops.branch_exists")
    @patch("src.lib.git_ops.get_current_branch")
    @patch("src.lib.git_ops._run")
    def test_raises_on_failure(self, mock_run, mock_current, mock_exists):
        mock_current.return_value = "dev"
        mock_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=1, stderr="error: pathspec")
        with pytest.raises(RuntimeError, match="Failed to create branch"):
            create_branch("feat/bad", "nonexistent")


@pytest.mark.unit
class TestStageFiles:
    """Tests for stage_files() function."""

    @patch("src.lib.git_ops._run")
    def test_stages_files(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        stage_files(["src/a.ts", "src/b.ts"])
        mock_run.assert_called_once_with(["add", "src/a.ts", "src/b.ts"], cwd=None)

    @patch("src.lib.git_ops._run")
    def test_noop_empty_list(self, mock_run):
        stage_files([])
        mock_run.assert_not_called()

    @patch("src.lib.git_ops._run")
    def test_raises_on_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="fatal: pathspec")
        with pytest.raises(RuntimeError, match="git add failed"):
            stage_files(["nonexistent.ts"])


@pytest.mark.unit
class TestCommit:
    """Tests for commit() function."""

    @patch("src.lib.git_ops._run")
    def test_commits_and_returns_sha(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git commit
            MagicMock(returncode=0, stdout="abc1234def\n"),  # git rev-parse HEAD
        ]
        sha = commit("feat: add login")
        assert sha == "abc1234def"

    @patch("src.lib.git_ops._run")
    def test_raises_on_commit_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="nothing to commit")
        with pytest.raises(RuntimeError, match="git commit failed"):
            commit("feat: add login")
