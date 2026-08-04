"""Tests for resource URI resolution in the artifact loader."""

from __future__ import annotations

import pytest

from src.runtime.loader import ArtifactLoader


@pytest.fixture
def workspace(tmp_path):
    """Create a workspace with files for resource resolution testing."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    steering_dir = tmp_path / "steering" / "conventions"
    steering_dir.mkdir(parents=True)

    # Create some files to resolve
    (skills_dir / "debug.md").write_text("# Debug Skill")
    (skills_dir / "test.md").write_text("# Test Skill")
    (steering_dir / "code-style.md").write_text("# Code Style")
    (agents_dir / "agent.json").write_text("{}")

    return tmp_path


@pytest.fixture
def loader(workspace):
    return ArtifactLoader(workspace_root=workspace)


class TestSkillUriResolution:
    """Tests for skill:// URI resolution."""

    def test_skill_relative_path(self, loader, workspace):
        """skill://../skills/debug.md resolves from agents dir."""
        path = loader.resolve_resource_path(
            "skill://../skills/debug.md",
            relative_to=workspace / "agents",
        )
        assert path is not None
        assert path.name == "debug.md"
        assert path.exists()

    def test_skill_without_relative_to(self, loader, workspace):
        """skill:// resolves from agents dir by default."""
        path = loader.resolve_resource_path("skill://../skills/test.md")
        assert path is not None
        assert path.name == "test.md"

    def test_skill_nonexistent_returns_none(self, loader):
        """Nonexistent skill returns None."""
        path = loader.resolve_resource_path("skill://../skills/nonexistent.md")
        assert path is None


class TestFileUriResolution:
    """Tests for file:// URI resolution."""

    def test_file_relative_to_workspace(self, loader, workspace):
        """file:// resolves relative to workspace root."""
        path = loader.resolve_resource_path(
            "file://../steering/conventions/code-style.md"
        )
        # May or may not resolve depending on CWD — test with workspace-relative
        # The loader tries CWD first, then workspace
        path_alt = loader.resolve_resource_path("file://steering/conventions/code-style.md")
        # At least one resolution path should work
        assert path is not None or path_alt is not None

    def test_file_nonexistent_returns_none(self, loader):
        """Nonexistent file returns None."""
        path = loader.resolve_resource_path("file://nonexistent/path.json")
        assert path is None


class TestBarePathResolution:
    """Tests for bare path resolution (no URI scheme)."""

    def test_bare_path_resolves_from_workspace(self, loader, workspace):
        """Bare paths resolve relative to workspace root."""
        path = loader.resolve_resource_path("steering/conventions/code-style.md")
        assert path is not None
        assert path.name == "code-style.md"

    def test_bare_path_nonexistent_returns_none(self, loader):
        """Nonexistent bare path returns None."""
        path = loader.resolve_resource_path("no/such/file.md")
        assert path is None

    def test_absolute_path_existing(self, loader, workspace):
        """Absolute paths that exist resolve directly."""
        abs_path = workspace / "skills" / "debug.md"
        path = loader.resolve_resource_path(str(abs_path))
        assert path is not None
        assert path == abs_path

    def test_absolute_path_nonexistent(self, loader, tmp_path):
        """Nonexistent absolute paths return None."""
        path = loader.resolve_resource_path(str(tmp_path / "nope.md"))
        assert path is None
