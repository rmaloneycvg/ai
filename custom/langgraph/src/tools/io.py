"""IO tools — file read/write operations, mirrors Kiro MCP io server."""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.tools import tool


@tool
def read_json(path: str) -> str:
    """Read and parse a JSON file with validation.

    Args:
        path: Path to the JSON file to read.
    """
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return json.dumps({"success": False, "error": f"File not found: {path}"})
        content = p.read_text()
        data = json.loads(content)
        return json.dumps({"success": True, "data": data}, indent=2)
    except json.JSONDecodeError as e:
        return json.dumps({"success": False, "error": f"Invalid JSON: {e}"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def write_json(path: str, data: str, indent: int = 2) -> str:
    """Write JSON to a file with configurable formatting.

    Args:
        path: Path to write the JSON file.
        data: JSON string to write (will be parsed to validate).
        indent: Indentation spaces (default: 2).
    """
    try:
        parsed = json.loads(data)
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w") as f:
            json.dump(parsed, f, indent=indent)
        return json.dumps({"success": True, "path": str(p)})
    except json.JSONDecodeError:
        return json.dumps({"success": False, "error": "Invalid JSON data"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def read_file(path: str, max_lines: int = 0) -> str:
    """Read a text file, optionally limiting to first N lines.

    Args:
        path: Path to the file.
        max_lines: Maximum lines to read (0 = all).
    """
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return f"Error: File not found: {path}"
        content = p.read_text()
        if max_lines > 0:
            lines = content.split("\n")[:max_lines]
            content = "\n".join(lines)
        return content
    except Exception as e:
        return f"Error: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a text file, creating parent directories if needed.

    Args:
        path: Path to write the file.
        content: Text content to write.
    """
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return json.dumps({"success": True, "path": str(p), "bytes": len(content)})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
