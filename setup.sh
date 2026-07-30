#!/usr/bin/env bash
# setup.sh — Create a local .kiro/ directory with file-level symlinks to agents/, steering/, and skills/.
#
# Symlinks individual files (not directories) so .kiro/ mirrors the directory
# structure but each file resolves to the canonical source.
#
# Usage:
#   ./setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIRO_DIR="$SCRIPT_DIR/.kiro"
DIRS_TO_LINK=(agents steering skills)

if [[ -d "$KIRO_DIR" ]]; then
    echo ".kiro/ already exists. Remove it first if you want to regenerate."
    exit 1
fi

mkdir -p "$KIRO_DIR"

# Create workspace settings with default agent
mkdir -p "$KIRO_DIR/settings"
cat > "$KIRO_DIR/settings/cli.json" <<'EOF'
{
  "chat.defaultAgent": "dev"
}
EOF
echo "  Created .kiro/settings/cli.json (defaultAgent: dev)"

for dir in "${DIRS_TO_LINK[@]}"; do
    if [[ ! -d "$SCRIPT_DIR/$dir" ]]; then
        echo "  Warning: $dir/ not found, skipping."
        continue
    fi

    # Find all files and recreate directory structure with file symlinks
    while IFS= read -r -d '' file; do
        rel="${file#"$SCRIPT_DIR/$dir/"}"
        target_dir="$KIRO_DIR/$dir/$(dirname "$rel")"
        mkdir -p "$target_dir"
        ln -s "$file" "$KIRO_DIR/$dir/$rel"
    done < <(find "$SCRIPT_DIR/$dir" -type f -print0)

    echo "  Linked $(find "$SCRIPT_DIR/$dir" -type f | wc -l) files in .kiro/$dir/"
done

echo "Done. .kiro/ created with file-level symlinks."
