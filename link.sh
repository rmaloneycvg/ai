#!/usr/bin/env bash
# link.sh — Create a .kiro/ directory with symlinks back to this workspace.
#
# Two linking strategies are used:
#
#   File-level symlinks (FILE_LINK_DIRS): each file is linked individually so the
#   target .kiro/ mirrors the directory structure while every file resolves to the
#   canonical source here. Used for small text-config trees (agents, steering,
#   skills, hooks) so unrelated local files never leak in.
#
#   Directory-level symlinks (DIR_LINK_DIRS): the whole directory is linked as a
#   single symlink. Used for runnable project trees (mcp) and shared config where
#   node_modules resolution, virtualenvs, and relative imports must see a real,
#   intact tree — file-level linking would break module/venv resolution.
#
# Existing symlinks are removed/refreshed before re-linking so the result is
# always current.
#
# Usage:
#   ./link.sh [target-directory]
#
# Defaults to ~/.kiro/ if no target directory is provided.
# Creates <target>/.kiro/ (or <target>/ if it already ends in .kiro).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Linked file-by-file (small config/text trees).
FILE_LINK_DIRS=(agents steering skills hooks config)
# Linked as whole-directory symlinks (runnable trees / shared config).
DIR_LINK_DIRS=(mcp)
DIRS_TO_LINK=("${FILE_LINK_DIRS[@]}")

# Default to ~/.kiro/ if no argument provided
if [[ $# -lt 1 ]]; then
    KIRO_DIR="$HOME/.kiro"
else
    TARGET="$(cd "$1" 2>/dev/null && pwd)" || { echo "Error: '$1' is not a valid directory."; exit 1; }
    KIRO_DIR="$TARGET/.kiro"
fi

echo "Target: $KIRO_DIR"

# Remove existing symlinks that point back into the SAME managed source dir of
# THIS workspace (e.g. a link in .kiro/agents/ that resolves into ./agents/).
# Symlinks pointing elsewhere — another top-level module such as ./dev-env-setup/,
# or an entirely different workspace — are left untouched, so re-running this
# script never clobbers a sibling module's links.
for dir in "${DIRS_TO_LINK[@]}"; do
    if [[ -d "$KIRO_DIR/$dir" ]]; then
        src_root="$SCRIPT_DIR/$dir/"
        while IFS= read -r -d '' link; do
            resolved="$(readlink -f "$link" 2>/dev/null || true)"
            if [[ -n "$resolved" && "$resolved" == "$src_root"* ]]; then
                rm -f "$link"
            fi
        done < <(find "$KIRO_DIR/$dir" -type l -print0 2>/dev/null || true)

        # Remove empty directories left behind
        find "$KIRO_DIR/$dir" -type d -empty -delete 2>/dev/null || true

        echo "  Cleaned this workspace's symlinks in $KIRO_DIR/$dir/"
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
    done < <(find "$SCRIPT_DIR/$dir" -type f \
        -not -path '*/__pycache__/*' \
        -not -path '*/pytest_cache/*' \
        -not -path '*/.pytest_cache/*' \
        -not -path '*/tests/*'\
        -not -path '*/node_modules/*' \
        -not -path '*/.venv/*' \
        -not -path '*/venv/*' \
        -not -path '*/.next/*' \
        -not -path '*/dist/*' \
        -not -path '*/build/*' \
        -not -path '*/.cache/*' \
        -not -path '*/.git/*' \
        -not -name '*.pyc' \
        -not -name '*.pyo' \
        -print0) || true

    echo "  Linked $count files in $KIRO_DIR/$dir/"
done

# Directory-level symlinks: link the whole directory as one symlink so runnable
# trees (node_modules, .venv, relative imports) resolve against an intact tree.
for dir in "${DIR_LINK_DIRS[@]}"; do
    if [[ ! -d "$SCRIPT_DIR/$dir" ]]; then
        echo "  Warning: $SCRIPT_DIR/$dir not found, skipping."
        continue
    fi

    link_path="$KIRO_DIR/$dir"

    # Refresh: remove an existing symlink so we always point at the current source.
    if [[ -L "$link_path" ]]; then
        rm -f "$link_path"
    elif [[ -e "$link_path" ]]; then
        echo "  Warning: $link_path exists and is not a symlink, skipping to avoid data loss."
        continue
    fi

    ln -s "$SCRIPT_DIR/$dir" "$link_path"
    echo "  Linked directory $link_path -> $SCRIPT_DIR/$dir"
done

echo "Done. $KIRO_DIR is up to date."
