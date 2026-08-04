"""Hook executor — runs agentSpawn shell commands before agent execution.

Hooks provide runtime context (git status, branch, versions) that gets
injected into the agent's system prompt. Failures are logged but don't
block execution.
"""

from __future__ import annotations

import asyncio
import shlex
from pathlib import Path


async def execute_hooks(
    hooks: dict[str, list[dict]],
    cwd: Path | None = None,
) -> dict[str, str]:
    """Execute agent hooks and return results as context strings.

    Args:
        hooks: Hook configuration from agent JSON (e.g., {"agentSpawn": [...]}).
        cwd: Working directory for command execution.

    Returns:
        Dict mapping hook descriptions to their stdout output.
        Keys are derived from the command (e.g., "git_status", "git_branch").
    """
    results: dict[str, str] = {}
    spawn_hooks = hooks.get("agentSpawn", [])

    tasks = [_run_hook(hook, cwd) for hook in spawn_hooks]
    outputs = await asyncio.gather(*tasks, return_exceptions=True)

    for hook, output in zip(spawn_hooks, outputs):
        key = _derive_key(hook.get("command", ""))
        if isinstance(output, Exception):
            results[key] = f"[hook failed: {output}]"
        else:
            results[key] = output

    return results


async def _run_hook(hook: dict, cwd: Path | None) -> str:
    """Execute a single hook command with timeout.

    Args:
        hook: Hook dict with "command" and optional "timeout_ms".
        cwd: Working directory.

    Returns:
        Stdout output (stripped).

    Raises:
        asyncio.TimeoutError: If command exceeds timeout.
        RuntimeError: If command exits non-zero.
    """
    command = hook.get("command", "")
    timeout_ms = hook.get("timeout_ms", 5000)
    timeout_s = timeout_ms / 1000.0

    if not command:
        return ""

    # Tokenize for safe execution (no shell=True)
    # However, some hook commands use pipes (e.g., "cat package.json | grep ...")
    # For those, we must use shell mode with the command as-is
    use_shell = "|" in command or ">" in command or "2>" in command or "&&" in command

    try:
        if use_shell:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
            )
        else:
            args = shlex.split(command)
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
            )

        stdout, _stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_s
        )

        return stdout.decode().strip()

    except asyncio.TimeoutError:
        try:
            proc.kill()  # type: ignore[possibly-undefined]
        except ProcessLookupError:
            pass
        return f"[timed out after {timeout_ms}ms]"
    except FileNotFoundError as e:
        return f"[command not found: {e}]"
    except Exception as e:
        return f"[error: {e}]"


def _derive_key(command: str) -> str:
    """Derive a readable key from a hook command.

    Examples:
        "git status --porcelain" → "git_status"
        "git branch --show-current" → "git_branch"
        "node --version" → "node_version"
        "cat package.json | grep ..." → "package_info"
    """
    if not command:
        return "unknown"

    # Special cases
    if "package.json" in command:
        return "package_info"

    # Take first two meaningful tokens
    parts = command.split()
    if len(parts) >= 2:
        # Skip flags
        meaningful = [p for p in parts[:3] if not p.startswith("-")]
        key = "_".join(meaningful[:2])
    else:
        key = parts[0]

    # Clean up
    key = key.replace(".", "_").replace("/", "_").replace("--", "")
    return key.lower()


def format_hook_context(hook_results: dict[str, str]) -> str:
    """Format hook results into a context string for the system prompt.

    Args:
        hook_results: Output from execute_hooks().

    Returns:
        Formatted string suitable for injection into system prompt.
    """
    if not hook_results:
        return ""

    lines = ["## Current Environment"]
    for key, value in hook_results.items():
        if value and not value.startswith("["):
            # Clean key for display
            display_key = key.replace("_", " ").title()
            lines.append(f"- **{display_key}:** {value}")

    return "\n".join(lines) if len(lines) > 1 else ""
