#!/usr/bin/env bash
# merge.sh — Copy agents, steering, and skills from .kiro back to ~/workspace/ai.
#
# Usage:
#   ./merge.sh [SOURCE_DIR]
#
# If SOURCE_DIR is provided, merges from SOURCE_DIR/.kiro/
# If omitted, merges from .kiro/ alongside this script.

set -euo pipefail

TARGET="${HOME}/workspace/ai"
DIRS_TO_MERGE=(agents steering skills)

# Determine source .kiro directory
if [[ $# -ge 1 ]]; then
    SOURCE="$1/.kiro"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SOURCE="$SCRIPT_DIR/.kiro"
fi

for dir in "${DIRS_TO_MERGE[@]}"; do
    if [[ -d "${SOURCE}/${dir}" ]]; then
        echo "Merging ${SOURCE}/${dir}/ → ${TARGET}/${dir}/"
        rm -rf "${TARGET:?}/${dir}"
        cp -r "${SOURCE}/${dir}" "${TARGET}/${dir}"
    else
        echo "Warning: ${SOURCE}/${dir} not found, skipping."
    fi
done

echo "Done. Merged ${DIRS_TO_MERGE[*]} into ${TARGET}/"
