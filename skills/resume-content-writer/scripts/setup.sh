#!/usr/bin/env bash
# setup.sh — Initialize resume tooling: install Python deps and generate docx templates.
#
# Templates are placed in ~/workspace/resume/templates/ (alongside resume output).
#
# Usage: ./scripts/setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RESUME_DIR="$HOME/workspace/resume"
TEMPLATE_DIR="$RESUME_DIR/templates"

echo "=== Resume Tooling Setup ==="
echo ""
echo "  Skill root:   $SKILL_ROOT"
echo "  Resume dir:   $RESUME_DIR"
echo "  Template dir:  $TEMPLATE_DIR"
echo ""

# --- 1. Python dependencies ---
echo "Installing Python dependencies..."
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "  Created venv at $VENV_DIR"
fi
"$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
echo "✓ Python dependencies installed"

echo ""

# --- 2. Ensure resume output directory exists ---
mkdir -p "$RESUME_DIR"

# --- 3. Generate templates ---
echo "Generating docx templates..."
mkdir -p "$TEMPLATE_DIR"
"$VENV_DIR/bin/python" "$SCRIPT_DIR/create_templates.py" --output-dir "$TEMPLATE_DIR"
echo "✓ Templates generated in $TEMPLATE_DIR"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Review/update references/experience.json with your latest experience"
echo "  2. Activate the resume-content-writer skill and paste a job description to generate a tailored resume"
