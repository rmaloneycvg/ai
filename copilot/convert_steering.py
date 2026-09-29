#!/usr/bin/env python3
"""Convert Kiro steering files to Copilot .instructions.md files.

Transform per file:
  - Keep `name` and `description`.
  - Drop `inclusion` (Kiro-only).
  - Convert `fileMatchPattern` (a YAML list of globs) into a single `applyTo`
    string, comma-joined (Copilot's applyTo accepts a comma-separated glob list).
  - Preserve the Markdown body byte-for-byte below the new frontmatter.

Output naming: flatten subfolders into hyphen-prefixed filenames, e.g.
  steering/nextjs/overview.md      -> instructions/nextjs-overview.instructions.md
  steering/react/use-effect.md     -> instructions/react-use-effect.instructions.md
  steering/security/policies.md    -> instructions/security-policies.instructions.md
  steering/DOTNET-EntityFrameworkQueries.md
                                   -> instructions/dotnet-entityframeworkqueries.instructions.md
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

SRC = Path.home() / "workspace" / "ai" / "steering"
DST = Path(__file__).resolve().parent / ".github" / "instructions"
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)


def out_name(md: Path) -> str:
    rel = md.relative_to(SRC)
    parts = list(rel.parts)
    parts[-1] = parts[-1][: -len(".md")]
    slug = "-".join(parts).lower()
    return f"{slug}.instructions.md"


def convert(md: Path) -> tuple[str, str]:
    text = md.read_text()
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"{md}: no frontmatter")
    fm = yaml.safe_load(m.group(1))
    body = text[m.end():]

    name = fm.get("name")
    description = fm.get("description")
    patterns = fm.get("fileMatchPattern") or []
    if isinstance(patterns, str):
        patterns = [patterns]
    apply_to = ",".join(p.strip() for p in patterns if str(p).strip())

    # Build new frontmatter deterministically (no inclusion field).
    lines = ["---"]
    if name is not None:
        lines.append(f"name: {yaml_scalar(name)}")
    if description is not None:
        lines.append(f"description: {yaml_scalar(description)}")
    lines.append(f"applyTo: {yaml_scalar(apply_to)}")
    lines.append("---")
    new_fm = "\n".join(lines) + "\n"
    return out_name(md), new_fm + body


def yaml_scalar(v) -> str:
    """Emit a YAML-safe single-line scalar, quoting when needed."""
    s = str(v)
    if s == "":
        return "''"
    # Quote if it contains characters that would confuse a bare scalar.
    if re.search(r"[:#\[\]{}&*!|>'\"%@`,]", s) or s[0] in "-?" or s != s.strip():
        return "'" + s.replace("'", "''") + "'"
    return s


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    md_files = sorted(SRC.rglob("*.md"))
    count = 0
    for md in md_files:
        name, content = convert(md)
        (DST / name).write_text(content)
        count += 1
        print(f"  {md.relative_to(SRC)} -> instructions/{name}")
    print(f"Converted {count} steering files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
