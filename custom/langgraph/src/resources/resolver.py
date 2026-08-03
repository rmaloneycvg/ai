"""Resource resolver — steering docs with symlink + overlay priority.

Resolution order:
1. steering-local/ (local overrides take precedence)
2. steering/ (symlinked to ~/workspace/ai/steering/)

This allows model-specific adaptations without modifying the shared steering.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
STEERING_LOCAL = PROJECT_ROOT / "steering-local"
STEERING_SYMLINK = PROJECT_ROOT / "steering"


def _is_contained(root: Path, candidate: Path) -> bool:
    """Check that candidate is contained within root after resolving symlinks.

    Returns False for path traversal attempts (../) and absolute paths that
    escape the root.
    """
    try:
        resolved_root = root.resolve(strict=False)
        resolved_candidate = candidate.resolve(strict=False)
        # Use is_relative_to (Python 3.9+) to check containment
        return resolved_candidate.is_relative_to(resolved_root)
    except (OSError, ValueError):
        return False


class ResourceResolver:
    """Resolves steering resources with overlay priority."""

    def __init__(
        self,
        local_dir: Path = STEERING_LOCAL,
        base_dir: Path = STEERING_SYMLINK,
    ):
        self._local = local_dir
        self._base = base_dir

    def resolve(self, relative_path: str) -> Path | None:
        """Resolve a relative steering path with overlay priority.

        Checks local override first, then base symlink.
        Returns None if not found in either location or if the path
        escapes the root directories.
        """
        # Check local override
        local_path = self._local / relative_path
        if _is_contained(self._local, local_path) and local_path.exists():
            return local_path

        # Fall back to symlinked base
        base_path = self._base / relative_path
        if _is_contained(self._base, base_path) and base_path.exists():
            return base_path

        return None

    def read(self, relative_path: str) -> str | None:
        """Read a steering resource. Returns content or None if not found."""
        path = self.resolve(relative_path)
        if path is None:
            return None
        return path.read_text()

    def list_available(self, subdirectory: str = "") -> list[str]:
        """List available resources in both locations (deduplicated).

        Returns relative paths with local overrides taking precedence.
        """
        seen: set[str] = set()
        results: list[str] = []

        # Local first (higher priority)
        local_dir = self._local / subdirectory
        if _is_contained(self._local, local_dir) and local_dir.exists():
            for path in sorted(local_dir.rglob("*.md")):
                rel = str(path.relative_to(self._local))
                if rel not in seen:
                    seen.add(rel)
                    results.append(rel)

        # Then base (lower priority, skip duplicates)
        base_dir = self._base / subdirectory
        if _is_contained(self._base, base_dir) and base_dir.exists():
            for path in sorted(base_dir.rglob("*.md")):
                rel = str(path.relative_to(self._base))
                if rel not in seen:
                    seen.add(rel)
                    results.append(rel)

        return results

    def get_metadata(self, relative_path: str) -> dict | None:
        """Extract metadata (name, first heading) from a resource without full read.

        Used for progressive disclosure metadata tier.
        """
        path = self.resolve(relative_path)
        if path is None:
            return None

        # Read only first 500 chars for metadata extraction
        try:
            with open(path) as f:
                head = f.read(500)
        except OSError:
            return None

        # Extract title from first heading
        title = ""
        for line in head.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break

        return {
            "path": relative_path,
            "title": title,
            "source": "local" if (self._local / relative_path).exists() else "base",
            "size_bytes": path.stat().st_size,
        }
