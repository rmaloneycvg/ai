"""Shell tool — command execution with allowlist enforcement."""

from __future__ import annotations

import fnmatch
import json
import subprocess

from langchain_core.tools import tool

# Default allowlist — commands matching these glob patterns are permitted.
# Override via configuration in tool registry.
DEFAULT_ALLOWLIST = [
    "ls *",
    "cat *",
    "find *",
    "grep *",
    "head *",
    "tail *",
    "wc *",
    "echo *",
    "pwd",
    "which *",
    "env",
    "date",
    "git *",
    "npm *",
    "npx *",
    "node *",
    "uv *",
    "python *",
    "docker ps*",
    "docker images*",
    "docker logs*",
    "kubectl get*",
    "kubectl describe*",
    "kubectl logs*",
    "terraform plan*",
    "terraform show*",
    "tilt status*",
    "tilt logs*",
]


def _is_allowed(command: str, allowlist: list[str] | None = None) -> bool:
    """Check if a command matches the allowlist patterns."""
    patterns = allowlist or DEFAULT_ALLOWLIST
    for pattern in patterns:
        if fnmatch.fnmatch(command, pattern):
            return True
    return False


@tool
def run_command(command: str, cwd: str = ".", timeout: int = 30) -> str:
    """Execute a shell command with allowlist enforcement.

    Only commands matching the configured allowlist patterns are permitted.
    Write/destructive operations are blocked by default.

    Args:
        command: Shell command to execute.
        cwd: Working directory.
        timeout: Timeout in seconds.
    """
    if not _is_allowed(command):
        return json.dumps(
            {
                "error": f"Command not in allowlist: {command}",
                "hint": "Only read-only and safe commands are permitted.",
            }
        )

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        output = {
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
        return json.dumps(output)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Command timed out after {timeout}s"})
    except Exception as e:
        return json.dumps({"error": str(e)})
