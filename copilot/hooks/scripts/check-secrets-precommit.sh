#!/usr/bin/env bash
# Pre-commit / CI secret scanner.
#
# WHY THIS EXISTS: Copilot has no always-on PreToolUse gate like Kiro's
# `01-check-secrets` hook. To keep equivalent protection, run this as a git
# pre-commit hook and/or in CI. It reuses the same secret patterns as the
# original Kiro hook (check-secrets.sh) but scans FILES instead of a hook event.
#
# Usage:
#   check-secrets-precommit.sh                # scan staged files (pre-commit mode)
#   check-secrets-precommit.sh file1 file2 …  # scan explicit files (CI mode)
#
# Exit 0 = clean, exit 1 = secret-shaped content found (blocks the commit/build).
set -euo pipefail

if [[ $# -gt 0 ]]; then
  FILES=("$@")
else
  # staged, added/copied/modified files only
  mapfile -t FILES < <(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
fi

[[ ${#FILES[@]} -eq 0 ]] && { echo "check-secrets: no files to scan"; exit 0; }

FILES_JOINED=$(printf '%s\n' "${FILES[@]}")
export _FILES="$FILES_JOINED"

python3 <<'PYEOF'
import os, re, sys, pathlib

# Allowlisted extensions where placeholder-style strings are expected.
ALLOWLISTED_EXTENSIONS = {'.md', '.example', '.sample', '.template'}

# Same patterns as the Kiro check-secrets hook (token-level, no prose allowlist).
SECRET_PATTERNS = [
    ('AWS Access Key', re.compile(r'AKIA[0-9A-Z]{16}')),
    ('AWS Secret Key', re.compile(r'(?:aws_secret_access_key|secret_access_key|AWS_SECRET)\s*[:=]\s*["\']?[A-Za-z0-9/+=]{40}', re.IGNORECASE)),
    ('Private Key', re.compile(r'-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----')),
    ('GitHub Token', re.compile(r'gh[ps]_[a-zA-Z0-9]{36,}')),
    ('Slack Token', re.compile(r'xox[bpras]-[a-zA-Z0-9\-]+')),
    ('Generic API Key', re.compile(r'api[_\-]?key\s*[:=]\s*["\'][a-zA-Z0-9]{20,}["\']', re.IGNORECASE)),
    ('Generic Token', re.compile(r'(?:auth_token|access_token|bearer)\s*[:=]\s*["\'][a-zA-Z0-9_\-\.]{20,}["\']', re.IGNORECASE)),
]
# AWS documentation canonical keys end in EXAMPLE — exempt at the token level.
EXAMPLE_RE = re.compile(r'EXAMPLE', re.IGNORECASE)

findings = []
for name in os.environ.get('_FILES', '').splitlines():
    name = name.strip()
    if not name:
        continue
    p = pathlib.Path(name)
    if not p.is_file():
        continue
    if p.suffix in ALLOWLISTED_EXTENSIONS:
        continue
    try:
        text = p.read_text(errors='replace')
    except OSError:
        continue
    for lineno, line in enumerate(text.splitlines(), 1):
        for label, pat in SECRET_PATTERNS:
            m = pat.search(line)
            if m and not EXAMPLE_RE.search(m.group(0)):
                findings.append(f"{name}:{lineno}: {label}")

if findings:
    sys.stderr.write("check-secrets: potential secret(s) detected — commit blocked:\n")
    for f in findings:
        sys.stderr.write(f"  ✗ {f}\n")
    sys.stderr.write("If this is a false positive, move the value to an env var / secret store, "
                     "or use an allowlisted extension (.example/.sample/.template) for fixtures.\n")
    sys.exit(1)
print(f"check-secrets: scanned {len([f for f in os.environ.get('_FILES','').splitlines() if f.strip()])} file(s), no secrets found.")
PYEOF
