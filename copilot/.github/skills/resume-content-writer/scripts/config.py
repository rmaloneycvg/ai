"""Shared configuration defaults for resume-content-writer scripts."""

import os
from pathlib import Path

# Central output directory — override via RESUME_DIR env var or --resume-dir CLI arg.
DEFAULT_RESUME_DIR = Path(os.environ.get("RESUME_DIR", Path.home() / "workspace" / "resume"))

# Derived paths
DEFAULT_TEMPLATE_DIR = DEFAULT_RESUME_DIR / "templates"
