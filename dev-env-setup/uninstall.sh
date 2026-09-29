#!/usr/bin/env bash
# uninstall.sh — Remove dev-env-setup symlinks from a Kiro config dir.
#
# Removes ONLY symlinks that resolve back into this module's directory (SCRIPT_DIR).
# Real files and foreign symlinks (pointing elsewhere) are never touched. Empty
# directories left behind within the managed subtrees are pruned.
#
# Usage:
#   ./uninstall.sh [target-directory]
#
# Defaults to ~/.kiro if no target is given. If the target already ends in .kiro it
# is used as-is; otherwise <target>/.kiro is used.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -lt 1 ]]; then
    KIRO_DIR="$HOME/.kiro"
else
    TARGET="$(cd "$1" 2>/dev/null && pwd)" || { echo "Error: '$1' is not a valid directory." >&2; exit 1; }
    if [[ "$(basename "$TARGET")" == ".kiro" ]]; then
        KIRO_DIR="$TARGET"
    else
        KIRO_DIR="$TARGET/.kiro"
    fi
fi

echo "Uninstalling dev-env-setup from: $KIRO_DIR"

removed=0

# remove_module_symlinks_in <dir>
remove_module_symlinks_in() {
    local dir="$1"
    [[ -d "$dir" ]] || return 0
    while IFS= read -r -d '' link; do
        local resolved
        resolved="$(readlink -f "$link" 2>/dev/null || true)"
        if [[ -n "$resolved" && "$resolved" == "$SCRIPT_DIR"/* ]]; then
            rm -f "$link"
            echo "  Removed $link"
            ((removed++)) || true
        fi
    done < <(find "$dir" -type l -print0 2>/dev/null || true)
    find "$dir" -type d -empty -delete 2>/dev/null || true
}

remove_module_symlinks_in "$KIRO_DIR/agents"
remove_module_symlinks_in "$KIRO_DIR/steering/dev-env-setup"

# config/preferred-stack.json — remove only if it is a symlink into this module.
dest="$KIRO_DIR/config/preferred-stack.json"
if [[ -L "$dest" ]]; then
    resolved="$(readlink -f "$dest" 2>/dev/null || true)"
    if [[ "$resolved" == "$SCRIPT_DIR"/* ]]; then
        rm -f "$dest"
        echo "  Removed $dest"
        ((removed++)) || true
    fi
fi
# prune config dir only if it became empty
find "$KIRO_DIR/config" -maxdepth 0 -type d -empty -delete 2>/dev/null || true

echo "Done. Removed $removed symlink(s). Real files and foreign symlinks were left untouched."
