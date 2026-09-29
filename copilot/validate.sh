#!/usr/bin/env bash
# Thin wrapper around validate.py. Validates the Copilot staging tree.
# Usage: ./validate.sh [root]   (root defaults to this script's directory)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/validate.py" "${1:-$SCRIPT_DIR}"
