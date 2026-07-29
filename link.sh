#!/usr/bin/env bash
# link.sh — Create a .kiro/ directory in a target project with file-level symlinks back to this workspace.
#
# Symlinks individual files (not directories) so the target .kiro/ mirrors the
# directory structure but each file resolves to the canonical source here.
#
# Usage:
#   ./link.sh /path/to/project
#
# Creates /path/to/project/.kiro/ with file-level symlinks to agents/, steering/,
# and skills/ from this AI workspace.

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: ./link.sh <target-directory>"
    echo ""
    echo "Creates <target-directory>/.kiro/ with file-level symlinks to this workspace's"
    echo "agents/, steering/, and skills/ directories."
    exit 1
fi

TARGET="$(cd "$1" 2>/dev/null && pwd)" || { echo "Error: '$1' is not a valid directory."; exit 1; }
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIRO_DIR="$TARGET/.kiro"
DIRS_TO_LINK=(agents steering skills)

if [[ -d "$KIRO_DIR" ]]; then
    echo ".kiro/ already exists in $TARGET. Remove it first if you want to regenerate."
    exit 1
fi

mkdir -p "$KIRO_DIR"

for dir in "${DIRS_TO_LINK[@]}"; do
    if [[ ! -d "$SCRIPT_DIR/$dir" ]]; then
        echo "  Warning: $SCRIPT_DIR/$dir not found, skipping."
        continue
    fi

    # Find all files and recreate directory structure with file symlinks
    while IFS= read -r -d '' file; do
        rel="${file#"$SCRIPT_DIR/$dir/"}"
        target_dir="$KIRO_DIR/$dir/$(dirname "$rel")"
        mkdir -p "$target_dir"
        ln -s "$file" "$KIRO_DIR/$dir/$rel"
    done < <(find "$SCRIPT_DIR/$dir" -type f -print0)

    echo "  Linked $(find "$SCRIPT_DIR/$dir" -type f | wc -l) files in $KIRO_DIR/$dir/"
done

echo "Done. $KIRO_DIR created with file-level symlinks."
