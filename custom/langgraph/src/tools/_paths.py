"""Shared path safety helper for tool modules.

Ensures all file/directory operations stay within the workspace root,
preventing path traversal attacks via user-supplied paths.
"""

from __future__ import annotations

import os
from pathlib import Path

# Workspace root: WORKSPACE_ROOT env var, or the langgraph project root
WORKSPACE_ROOT = Path(
    os.environ.get("WORKSPACE_ROOT", Path(__file__).parent.parent.parent)
).resolve()


def resolve_safe(path: str) -> Path | None:
    """Resolve a path and verify it's within the workspace root.

    Returns the resolved Path if safe, or None if the path escapes the workspace.
    """
    try:
        resolved = Path(path).expanduser().resolve()
        # Check that the resolved path is within or equal to workspace root
        resolved.relative_to(WORKSPACE_ROOT)
        return resolved
    except (ValueError, OSError):
        return None


def path_error(path: str) -> str:
    """Standard error message for rejected paths."""
    return f"Path rejected: '{path}' is outside the workspace root ({WORKSPACE_ROOT})"
