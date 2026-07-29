#!/usr/bin/env bash
# setup.sh — Initialize resume config files for a new user.
#
# Creates experience.json (from existing file or scaffold) and installs
# Python dependencies needed by the resume scripts.
#
# Usage: ./scripts/resume/setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_DIR="$REPO_ROOT/config/resume"
LEGACY_PATH="$HOME/workspace/resume/experience.json"

echo "=== Resume Tooling Setup ==="
echo ""

# --- 1. experience.json ---
if [ -f "$CONFIG_DIR/experience.json" ]; then
    echo "✓ experience.json already exists at $CONFIG_DIR/experience.json"
elif [ -f "$LEGACY_PATH" ]; then
    echo "Found existing experience.json at $LEGACY_PATH"
    read -rp "Copy it to $CONFIG_DIR/experience.json? [Y/n] " answer
    answer="${answer:-Y}"
    if [[ "$answer" =~ ^[Yy] ]]; then
        cp "$LEGACY_PATH" "$CONFIG_DIR/experience.json"
        # Inject paths config if missing from legacy file
        if ! grep -q '"paths"' "$CONFIG_DIR/experience.json"; then
            sed -i '1a\  "paths": { "resumeDir": "~/workspace/resume" },' "$CONFIG_DIR/experience.json"
            echo "  Added paths.resumeDir config to copied file"
        fi
        echo "✓ Copied experience.json from $LEGACY_PATH"
    else
        echo "Skipped. Creating scaffold instead..."
        cat > "$CONFIG_DIR/experience.json" << 'SCAFFOLD'
{
  "paths": {
    "resumeDir": "~/workspace/resume"
  },
  "metadata": {
    "version": "1.0.0",
    "lastUpdated": "2024-01-01",
    "notes": "Scaffold — populate with your experience data using the experience-parser agent"
  },
  "personalInfo": {
    "name": "Your Name",
    "email": "your.email@example.com",
    "phone": "(555) 555-5555",
    "location": "City, State",
    "linkedin": "https://linkedin.com/in/yourprofile",
    "github": "https://github.com/yourusername"
  },
  "summaryTemplates": [],
  "skills": {
    "categories": []
  },
  "experience": [],
  "additionalExperience": [],
  "education": [],
  "certifications": []
}
SCAFFOLD
        echo "✓ Created scaffold experience.json"
    fi
else
    echo "No existing experience.json found. Creating scaffold..."
    cat > "$CONFIG_DIR/experience.json" << 'SCAFFOLD'
{
  "paths": {
    "resumeDir": "~/workspace/resume"
  },
  "metadata": {
    "version": "1.0.0",
    "lastUpdated": "2024-01-01",
    "notes": "Scaffold — populate with your experience data using the experience-parser agent"
  },
  "personalInfo": {
    "name": "Your Name",
    "email": "your.email@example.com",
    "phone": "(555) 555-5555",
    "location": "City, State",
    "linkedin": "https://linkedin.com/in/yourprofile",
    "github": "https://github.com/yourusername"
  },
  "summaryTemplates": [],
  "skills": {
    "categories": []
  },
  "experience": [],
  "additionalExperience": [],
  "education": [],
  "certifications": []
}
SCAFFOLD
    echo "✓ Created scaffold experience.json"
fi

echo ""

# --- 2. Python dependencies ---
echo "Installing Python dependencies..."
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "  Created venv at $VENV_DIR"
fi
"$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
echo "✓ Python dependencies installed"

echo ""

# --- 3. Generate templates ---
echo "Generating docx templates..."
mkdir -p "$CONFIG_DIR/templates"
"$VENV_DIR/bin/python" "$SCRIPT_DIR/create_templates.py" --output-dir "$CONFIG_DIR/templates"
echo "✓ Templates generated"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. If you used the scaffold, run the experience-parser agent to populate experience.json"
echo "  2. Use 'kiro --agent resume-builder' and paste a job description to generate a resume"
