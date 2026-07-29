#!/usr/bin/env bash
# sync.sh — Copy agents, steering, and skills from ~/workspace/ai into a target .kiro directory.
#
# Usage:
#   ./sync.sh [TARGET_DIR]
#
# If TARGET_DIR is provided, syncs into TARGET_DIR/.kiro/
# If omitted, syncs into .kiro/ alongside this script.

set -euo pipefail

SOURCE="${HOME}/workspace/ai"
DIRS_TO_SYNC=(agents steering skills)

# Determine target .kiro directory
if [[ $# -ge 1 ]]; then
    TARGET="$1/.kiro"
else
    # Default: sync into the .kiro directory alongside this script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    TARGET="$SCRIPT_DIR/.kiro"
fi

mkdir -p "$TARGET"

for dir in "${DIRS_TO_SYNC[@]}"; do
    if [[ -d "${SOURCE}/${dir}" ]]; then
        echo "Syncing ${dir}/ → ${TARGET}/${dir}/"
        rm -rf "${TARGET:?}/${dir}"
        cp -r "${SOURCE}/${dir}" "${TARGET}/${dir}"
    else
        echo "Warning: ${SOURCE}/${dir} not found, skipping."
    fi
done

echo "Done. Synced ${DIRS_TO_SYNC[*]} into ${TARGET}/"
