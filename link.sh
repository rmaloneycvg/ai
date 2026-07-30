#!/usr/bin/env bash
# link.sh — Create a .kiro/ directory with file-level symlinks back to this workspace.
#
# Symlinks individual files (not directories) so the target .kiro/ mirrors the
# directory structure but each file resolves to the canonical source here.
# Existing symlinks are removed before re-linking so the result is always current.
#
# Usage:
#   ./link.sh [target-directory]
#
# Defaults to ~/.kiro/ if no target directory is provided.
# Creates <target>/.kiro/ (or <target>/ if it already ends in .kiro) with
# file-level symlinks to agents/, steering/, and skills/ from this workspace.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIRS_TO_LINK=(agents steering skills)

# Default to ~/.kiro/ if no argument provided
if [[ $# -lt 1 ]]; then
    KIRO_DIR="$HOME/.kiro"
else
    TARGET="$(cd "$1" 2>/dev/null && pwd)" || { echo "Error: '$1' is not a valid directory."; exit 1; }
    KIRO_DIR="$TARGET/.kiro"
fi

echo "Target: $KIRO_DIR"

# Remove existing symlinks within the directories we manage
for dir in "${DIRS_TO_LINK[@]}"; do
    if [[ -d "$KIRO_DIR/$dir" ]]; then
        # Find and remove all symlinks in this subtree
        find "$KIRO_DIR/$dir" -type l -print0 | xargs -0 rm -f 2>/dev/null || true

        # Remove empty directories left behind
        find "$KIRO_DIR/$dir" -type d -empty -delete 2>/dev/null || true

        echo "  Cleaned existing symlinks in $KIRO_DIR/$dir/"
    fi
done

# Create the .kiro directory if it doesn't exist
mkdir -p "$KIRO_DIR"

# Link all files from each directory
for dir in "${DIRS_TO_LINK[@]}"; do
    if [[ ! -d "$SCRIPT_DIR/$dir" ]]; then
        echo "  Warning: $SCRIPT_DIR/$dir not found, skipping."
        continue
    fi

    count=0
    while IFS= read -r -d '' file; do
        rel="${file#"$SCRIPT_DIR/$dir/"}"
        target_dir="$KIRO_DIR/$dir/$(dirname "$rel")"
        mkdir -p "$target_dir"
        ln -sf "$file" "$KIRO_DIR/$dir/$rel"
        ((count++)) || true
    done < <(find "$SCRIPT_DIR/$dir" -type f -print0) || true

    echo "  Linked $count files in $KIRO_DIR/$dir/"
done

echo "Done. $KIRO_DIR is up to date."
