#!/usr/bin/env bash
# install.sh — Install the dev-env-setup module into a Kiro config dir via file-level symlinks.
#
# Mirrors the workspace root link.sh approach: individual files (not directories)
# are symlinked so the target .kiro/ subfolders mirror this module's structure while
# each file resolves back to the canonical source here. Existing symlinks that point
# into this module are removed before re-linking so the result is always current.
#
# Symlinks created:
#   <target>/agents/<name>.json                -> agents/<name>.json
#   <target>/steering/dev-env-setup/<file>     -> steering/dev-env-setup/<file>
#   <target>/config/preferred-stack.json       -> config/preferred-stack.json
#
# Usage:
#   ./install.sh [target-directory]
#
# Defaults to ~/.kiro if no target is given. If the target already ends in .kiro it
# is used as-is; otherwise <target>/.kiro is used.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Resolve the Kiro config directory.
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

echo "Installing dev-env-setup into: $KIRO_DIR"
echo "Source module: $SCRIPT_DIR"

# link_file <source-abs-path> <dest-abs-path>
link_file() {
    local src="$1" dest="$2"
    mkdir -p "$(dirname "$dest")"
    ln -sf "$src" "$dest"
}

# clean_module_symlinks_in <dir> — remove only symlinks that resolve back into SCRIPT_DIR.
clean_module_symlinks_in() {
    local dir="$1"
    [[ -d "$dir" ]] || return 0
    while IFS= read -r -d '' link; do
        local resolved
        resolved="$(readlink -f "$link" 2>/dev/null || true)"
        if [[ -n "$resolved" && "$resolved" == "$SCRIPT_DIR"/* ]]; then
            rm -f "$link"
        fi
    done < <(find "$dir" -type l -print0 2>/dev/null || true)
    # prune empty dirs left behind (only within the managed subtree)
    find "$dir" -type d -empty -delete 2>/dev/null || true
}

# --- agents/*.json (top-level only) ---
clean_module_symlinks_in "$KIRO_DIR/agents"
agent_count=0
if [[ -d "$SCRIPT_DIR/agents" ]]; then
    while IFS= read -r -d '' file; do
        link_file "$file" "$KIRO_DIR/agents/$(basename "$file")"
        ((agent_count++)) || true
    done < <(find "$SCRIPT_DIR/agents" -maxdepth 1 -type f -name '*.json' -print0)
fi
echo "  Linked $agent_count agent file(s) -> $KIRO_DIR/agents/"

# --- steering/dev-env-setup/** (preserve nested structure) ---
clean_module_symlinks_in "$KIRO_DIR/steering/dev-env-setup"
steering_count=0
if [[ -d "$SCRIPT_DIR/steering/dev-env-setup" ]]; then
    while IFS= read -r -d '' file; do
        rel="${file#"$SCRIPT_DIR/steering/dev-env-setup/"}"
        link_file "$file" "$KIRO_DIR/steering/dev-env-setup/$rel"
        ((steering_count++)) || true
    done < <(find "$SCRIPT_DIR/steering/dev-env-setup" -type f -print0)
fi
echo "  Linked $steering_count steering file(s) -> $KIRO_DIR/steering/dev-env-setup/"

# --- config/preferred-stack.json ---
config_count=0
if [[ -f "$SCRIPT_DIR/config/preferred-stack.json" ]]; then
    # Remove a stale module-owned symlink if present, then relink.
    dest="$KIRO_DIR/config/preferred-stack.json"
    if [[ -L "$dest" ]]; then
        resolved="$(readlink -f "$dest" 2>/dev/null || true)"
        [[ "$resolved" == "$SCRIPT_DIR"/* ]] && rm -f "$dest"
    fi
    link_file "$SCRIPT_DIR/config/preferred-stack.json" "$dest"
    config_count=1
fi
echo "  Linked $config_count config file(s) -> $KIRO_DIR/config/"

echo "Done. dev-env-setup is installed at $KIRO_DIR."
