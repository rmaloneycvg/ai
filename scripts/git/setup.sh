#!/bin/bash
# setup.sh — Install git-workflow hooks and validate environment.
# Idempotent: safe to re-run at any time.
#
# Usage:
#   ./scripts/git/setup.sh              # From repo root
#   ./setup.sh                          # From scripts/git/
#
# What it does:
#   1. Checks prerequisites (git, python, uv)
#   2. Installs Python dependencies via uv
#   3. Enables git rerere globally
#   4. Installs commit-msg and pre-push hooks (symlinks)
#   5. Reports TICKET_SYSTEM_URL status
#   6. Optionally installs hooks in submodules

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# Find script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$SCRIPT_DIR/hooks"

# Find repo root
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$REPO_ROOT" ]; then
    error "Not inside a git repository."
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║    Git Workflow Setup                        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ─── Prerequisites ──────────────────────────────────────────────

info "Checking prerequisites..."

# Git version check (>= 2.28 for init.defaultBranch)
GIT_VERSION=$(git --version | grep -oP '\d+\.\d+' | head -1)
GIT_MAJOR=$(echo "$GIT_VERSION" | cut -d. -f1)
GIT_MINOR=$(echo "$GIT_VERSION" | cut -d. -f2)
if [ "$GIT_MAJOR" -lt 2 ] || ([ "$GIT_MAJOR" -eq 2 ] && [ "$GIT_MINOR" -lt 28 ]); then
    error "Git >= 2.28 required. Found: git $GIT_VERSION"
    exit 1
fi
success "Git $GIT_VERSION"

# Python version check (>= 3.11)
if ! command -v python3 &>/dev/null; then
    error "Python 3.11+ required but python3 not found."
    exit 1
fi
PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+')
PY_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]); then
    error "Python >= 3.11 required. Found: python $PYTHON_VERSION"
    exit 1
fi
success "Python $PYTHON_VERSION"

# uv check
if ! command -v uv &>/dev/null; then
    error "uv not found. Install: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi
UV_VERSION=$(uv --version 2>/dev/null | grep -oP '[\d.]+' | head -1)
success "uv $UV_VERSION"

# ─── Install Dependencies ───────────────────────────────────────

info "Installing Python dependencies..."
cd "$SCRIPT_DIR"
uv sync --quiet
success "Dependencies installed"

# ─── Enable git rerere ──────────────────────────────────────────

info "Enabling git rerere (reuse recorded resolution)..."
RERERE_CURRENT=$(git config --global rerere.enabled 2>/dev/null || echo "false")
if [ "$RERERE_CURRENT" != "true" ]; then
    git config --global rerere.enabled true
    success "git rerere enabled globally"
else
    success "git rerere already enabled"
fi

# ─── Install Git Hooks ──────────────────────────────────────────

install_hooks() {
    local git_dir="$1"
    local hooks_target="$git_dir/hooks"

    # Create hooks directory if it doesn't exist
    mkdir -p "$hooks_target"

    # commit-msg hook
    local commit_msg_target="$hooks_target/commit-msg"
    if [ -L "$commit_msg_target" ] && [ "$(readlink -f "$commit_msg_target")" = "$(readlink -f "$HOOKS_DIR/commit-msg")" ]; then
        success "commit-msg hook already installed ($(dirname "$git_dir"))"
    else
        if [ -f "$commit_msg_target" ] && [ ! -L "$commit_msg_target" ]; then
            warn "Existing commit-msg hook found. Backing up to commit-msg.bak"
            mv "$commit_msg_target" "${commit_msg_target}.bak"
        fi
        ln -sf "$HOOKS_DIR/commit-msg" "$commit_msg_target"
        success "commit-msg hook installed ($(dirname "$git_dir"))"
    fi

    # pre-push hook
    local pre_push_target="$hooks_target/pre-push"
    if [ -L "$pre_push_target" ] && [ "$(readlink -f "$pre_push_target")" = "$(readlink -f "$HOOKS_DIR/pre-push")" ]; then
        success "pre-push hook already installed ($(dirname "$git_dir"))"
    else
        if [ -f "$pre_push_target" ] && [ ! -L "$pre_push_target" ]; then
            warn "Existing pre-push hook found. Backing up to pre-push.bak"
            mv "$pre_push_target" "${pre_push_target}.bak"
        fi
        ln -sf "$HOOKS_DIR/pre-push" "$pre_push_target"
        success "pre-push hook installed ($(dirname "$git_dir"))"
    fi
}

info "Installing git hooks..."

# Install in main repo
GIT_DIR="$REPO_ROOT/.git"
if [ -d "$GIT_DIR" ]; then
    install_hooks "$GIT_DIR"
elif [ -f "$GIT_DIR" ]; then
    # It's a file (submodule gitdir pointer)
    ACTUAL_GIT_DIR=$(cat "$GIT_DIR" | sed 's/gitdir: //')
    if [[ "$ACTUAL_GIT_DIR" != /* ]]; then
        ACTUAL_GIT_DIR="$REPO_ROOT/$ACTUAL_GIT_DIR"
    fi
    install_hooks "$ACTUAL_GIT_DIR"
fi

# ─── Submodule Hook Installation ────────────────────────────────

# Check for submodules
if [ -f "$REPO_ROOT/.gitmodules" ]; then
    SUBMODULE_COUNT=$(git -C "$REPO_ROOT" submodule status 2>/dev/null | wc -l)
    if [ "$SUBMODULE_COUNT" -gt 0 ]; then
        echo ""
        info "Found $SUBMODULE_COUNT submodule(s)."
        if [ "${INSTALL_SUBMODULE_HOOKS:-}" = "1" ] || ([ -t 0 ] && read -p "Install hooks in submodules too? [y/N] " -n 1 -r && echo && [[ $REPLY =~ ^[Yy]$ ]]); then
            git -C "$REPO_ROOT" submodule foreach --quiet '
                sm_git_dir=$(git rev-parse --git-dir)
                echo "  Installing hooks in: $name"
            ' 2>/dev/null | while read -r line; do
                echo "$line"
            done

            # Actually install in each submodule
            while IFS= read -r sm_path; do
                if [ -n "$sm_path" ]; then
                    SM_FULL="$REPO_ROOT/$sm_path"
                    SM_GIT="$SM_FULL/.git"
                    if [ -d "$SM_GIT" ]; then
                        install_hooks "$SM_GIT"
                    elif [ -f "$SM_GIT" ]; then
                        ACTUAL=$(cat "$SM_GIT" | sed 's/gitdir: //')
                        if [[ "$ACTUAL" != /* ]]; then
                            ACTUAL="$SM_FULL/$ACTUAL"
                        fi
                        install_hooks "$ACTUAL"
                    fi
                fi
            done < <(git -C "$REPO_ROOT" submodule foreach --quiet 'echo $sm_path' 2>/dev/null)
        fi
    fi
fi

# ─── Ticket System Status ───────────────────────────────────────

echo ""
info "Ticket system status:"
TICKET_URL="${TICKET_SYSTEM_URL:-}"
if [ -n "$TICKET_URL" ]; then
    success "TICKET_SYSTEM_URL = $TICKET_URL"
    info "Branch names and PR titles will include ticket references."
else
    warn "TICKET_SYSTEM_URL not set."
    info "Branch names will not require ticket references."
    info "To enable, add to ~/.zshrc:"
    echo "    export TICKET_SYSTEM_URL=\"https://yourcompany.atlassian.net\""
fi

# ─── Summary ────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║    Setup Complete                            ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
info "Available commands (from scripts/git/):"
echo "    uv run git-branch      Create branch with naming convention"
echo "    uv run git-commit      Auto-group and commit changes"
echo "    uv run git-prepare-pr  Squash + rebase for PR"
echo "    uv run git-hotfix      Hotfix workflow from prod"
echo "    uv run git-merge-pr    Validate and merge PR"
echo "    uv run git-promote     Manual environment promotion"
echo ""
info "Or add to PATH:"
echo "    export PATH=\"\$PATH:$SCRIPT_DIR/.venv/bin\""
echo ""
