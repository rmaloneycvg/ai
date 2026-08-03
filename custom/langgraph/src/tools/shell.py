"""Shell tool — command execution with allowlist enforcement."""

from __future__ import annotations

import json
import shlex
import subprocess

from langchain_core.tools import tool

# Shell metacharacters that indicate command chaining or substitution.
# If any token contains these, the command is rejected outright.
_SHELL_METACHARACTERS = frozenset(";|&`$(){}")

# Flags that allow inline code execution — blocked for interpreters.
_INLINE_CODE_FLAGS: dict[str, frozenset[str]] = {
    "python": frozenset({"-c", "--command"}),
    "python3": frozenset({"-c", "--command"}),
    "node": frozenset({"-e", "--eval", "-p", "--print", "--input-type"}),
    "npm": frozenset({"exec", "x"}),
    "npx": frozenset({"-c", "--call"}),
}

# Default allowlist — each entry is (executable, allowed_subcommands_or_None).
# A value of None means any arguments are permitted (subject to metachar and
# inline-code checks).  A list of strings means the first argument must match
# one of the listed subcommands.
DEFAULT_ALLOWLIST: dict[str, list[str] | None] = {
    "ls": None,
    "cat": None,
    "find": None,
    "grep": None,
    "head": None,
    "tail": None,
    "wc": None,
    "echo": None,
    "pwd": None,
    "which": None,
    "env": None,
    "date": None,
    "git": None,
    "npm": ["list", "ls", "outdated", "view", "info", "explain", "why", "audit"],
    "npx": None,
    "node": None,
    "uv": None,
    "python": None,
    "python3": None,
    "docker": ["ps", "images", "logs", "inspect"],
    "kubectl": ["get", "describe", "logs"],
    "terraform": ["plan", "show"],
    "tilt": ["status", "logs"],
}


def _contains_metacharacters(tokens: list[str]) -> bool:
    """Return True if any token contains shell metacharacters."""
    for token in tokens:
        if any(ch in _SHELL_METACHARACTERS for ch in token):
            return True
    return False


def _has_inline_code_flag(executable: str, args: list[str]) -> bool:
    """Return True if args contain a flag that enables inline code execution."""
    blocked = _INLINE_CODE_FLAGS.get(executable)
    if not blocked:
        return False
    for arg in args:
        # Handle both '-c code' and '-c=code' forms
        flag = arg.split("=", 1)[0]
        if flag in blocked:
            return True
    return False


def _is_allowed(
    tokens: list[str], allowlist: dict[str, list[str] | None] | None = None
) -> tuple[bool, str]:
    """Validate a tokenized command against the allowlist.

    Returns (allowed, reason) where reason describes why the command was
    rejected (empty string if allowed).
    """
    if not tokens:
        return False, "Empty command"

    rules = allowlist if allowlist is not None else DEFAULT_ALLOWLIST

    executable = tokens[0]
    args = tokens[1:]

    # 1. Check executable is in the allowlist
    if executable not in rules:
        return False, f"Executable not in allowlist: {executable}"

    # 2. Reject shell metacharacters in any token
    if _contains_metacharacters(tokens):
        return False, "Shell metacharacters are not permitted"

    # 3. Block inline code execution flags for interpreters
    if _has_inline_code_flag(executable, args):
        return False, (
            f"Inline code execution flags are not permitted for {executable}"
        )

    # 4. Check subcommand restrictions
    allowed_subcommands = rules[executable]
    if allowed_subcommands is not None:
        if not args:
            return False, f"{executable} requires a subcommand"
        subcommand = args[0]
        if subcommand not in allowed_subcommands:
            return (
                False,
                f"Subcommand '{subcommand}' not permitted for {executable}. "
                f"Allowed: {', '.join(allowed_subcommands)}",
            )

    return True, ""


@tool
def run_command(command: str, cwd: str = ".", timeout: int = 30) -> str:
    """Execute a shell command with allowlist enforcement.

    Commands are tokenized with shlex and validated against a structured
    allowlist. Shell execution is disabled — no pipes, redirects, or
    command chaining. Only read-only and safe commands are permitted.

    Args:
        command: Shell command to execute.
        cwd: Working directory.
        timeout: Timeout in seconds.
    """
    # Tokenize the command string safely
    try:
        tokens = shlex.split(command)
    except ValueError as e:
        return json.dumps({"error": f"Failed to parse command: {e}"})

    allowed, reason = _is_allowed(tokens)
    if not allowed:
        return json.dumps(
            {
                "error": f"Command not permitted: {reason}",
                "command": command,
                "hint": "Only read-only and safe commands are permitted.",
            }
        )

    try:
        result = subprocess.run(
            tokens,
            shell=False,
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
    except FileNotFoundError:
        return json.dumps({"error": f"Executable not found: {tokens[0]}"})
    except Exception as e:
        return json.dumps({"error": str(e)})
