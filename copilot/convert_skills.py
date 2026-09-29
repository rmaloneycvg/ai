#!/usr/bin/env python3
"""Convert Kiro skills to Copilot Agent Skills.

For each SKILL.md under ~/workspace/ai/skills (including nested ui/*), copy the
skill directory into copilot/.github/skills/<name>/ where <name> is the skill's
frontmatter `name` (which must be lowercase-hyphen and will match the new dir).

Transforms:
  - Normalize the output directory name to the frontmatter `name` so Copilot's
    "name must match parent dir" rule holds. (ui/code-simplification -> code-simplification)
  - Set `context: fork` on read-heavy skills: diagnose, harvest-debt, flywheel.
  - Rewrite Kiro path prefixes in the body to Copilot-neutral equivalents:
        .kiro/      -> .copilot/       (workspace working dirs: issues/, delivery/)
        ~/.kiro/    -> ~/.copilot/     (user-level infra references)
    Rewrites are recorded and printed; infra references with no true Copilot
    equivalent are additionally logged for MIGRATION-NOTES.
  - Copy resource files, excluding junk (node_modules, .venv, __pycache__,
    .pytest_cache, *.pyc/*.pyo, dist, build, .cache, .next).

Skills with an empty/invalid SKILL.md (no name/description) are SKIPPED and
reported so they can be flagged in MIGRATION-NOTES.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import yaml

SRC = Path.home() / "workspace" / "ai" / "skills"
DST = Path(__file__).resolve().parent / ".github" / "skills"
FRONTMATTER_RE = re.compile(r"^\s*---\n(.*?)\n---\n?", re.DOTALL)

FORK_SKILLS = {"diagnose", "harvest-debt", "flywheel"}

EXCLUDE_DIR_PARTS = {
    "node_modules", ".venv", "__pycache__", ".pytest_cache",
    "dist", "build", ".cache", ".next", ".git",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}

# Kiro-infrastructure references that have NO clean Copilot equivalent — logged
# for MIGRATION-NOTES even after prefix rewrite.
INFRA_MARKERS = [
    "/sessions/",           # Kiro session store / transcript format
    "permissions.yaml",     # Kiro permission engine
    "/agents/",             # Kiro agent-profile layout (*.md under ~/.kiro/agents)
    "/steering/",           # Kiro steering layout (now Copilot instructions)
]


def is_excluded(path: Path) -> bool:
    if any(part in EXCLUDE_DIR_PARTS for part in path.parts):
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return False


def rewrite_kiro_paths(text: str) -> tuple[str, int]:
    n = 0
    def repl(m):
        nonlocal n
        n += 1
        return m.group(0).replace(".kiro", ".copilot")
    # Match ~/.kiro/... and .kiro/... occurrences
    out = re.sub(r"~?/?\.kiro\b", repl, text)
    return out, n


def parse(md: Path):
    text = md.read_text()
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, None, text
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, None, text
    if not isinstance(fm, dict):
        return None, None, text
    body = text[m.end():]
    return fm, m.group(1), body


def emit_frontmatter(fm: dict) -> str:
    lines = ["---"]
    # deterministic key order
    for key in ("name", "description", "context", "user-invocable", "disable-model-invocation", "argument-hint"):
        if key in fm and fm[key] is not None:
            lines.append(f"{key}: {yaml_scalar(fm[key])}")
    # preserve any other keys we didn't explicitly order
    for key, val in fm.items():
        if key not in ("name", "description", "context", "user-invocable", "disable-model-invocation", "argument-hint") and val is not None:
            lines.append(f"{key}: {yaml_scalar(val)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def yaml_scalar(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v)
    if s == "":
        return "''"
    if re.search(r"[:#\[\]{}&*!|>'\"%@`,]", s) or s[0] in "-?" or s != s.strip():
        return "'" + s.replace("'", "''") + "'"
    return s


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    skipped: list[str] = []
    infra_hits: dict[str, list[str]] = {}
    rewrite_counts: dict[str, int] = {}
    converted = 0

    md_files = sorted(
        p for p in SRC.rglob("SKILL.md")
        if not is_excluded(p.relative_to(SRC))
    )

    for md in md_files:
        rel = md.relative_to(SRC)
        fm, _, body = parse(md)
        if not fm or not fm.get("name") or not fm.get("description"):
            skipped.append(str(rel))
            continue
        name = str(fm["name"]).strip()
        src_dir = md.parent

        # context: fork for heavy skills
        if name in FORK_SKILLS:
            fm["context"] = "fork"

        # rewrite body paths
        new_body, nrw = rewrite_kiro_paths(body)
        if nrw:
            rewrite_counts[name] = nrw
        # record infra markers (check original body before rewrite)
        hits = [mk for mk in INFRA_MARKERS if mk in body and (".kiro" in body)]
        # more precise: only flag infra markers that co-occur with a kiro path
        precise = []
        for line in body.splitlines():
            if ".kiro" in line:
                for mk in INFRA_MARKERS:
                    if mk in line:
                        precise.append(mk)
        if precise:
            infra_hits[name] = sorted(set(precise))

        # also rewrite the description if it carried a kiro path
        if "description" in fm and isinstance(fm["description"], str):
            fm["description"], _ = rewrite_kiro_paths(fm["description"])

        out_dir = DST / name
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)

        # write SKILL.md
        (out_dir / "SKILL.md").write_text(emit_frontmatter(fm) + new_body)

        # copy resource files (everything except SKILL.md and excluded junk)
        for res in sorted(src_dir.rglob("*")):
            if res.is_dir():
                continue
            relres = res.relative_to(src_dir)
            if relres.name == "SKILL.md" and relres.parent == Path("."):
                continue
            if is_excluded(relres):
                continue
            # Skip nested SKILL.md (handled as their own skill)
            if res.name == "SKILL.md":
                continue
            target = out_dir / relres
            target.parent.mkdir(parents=True, exist_ok=True)
            # rewrite kiro paths inside text resources too (.md/.json/.txt)
            if res.suffix in (".md", ".json", ".txt", ".yaml", ".yml"):
                try:
                    content, _ = rewrite_kiro_paths(res.read_text())
                    target.write_text(content)
                    continue
                except UnicodeDecodeError:
                    pass
            shutil.copy2(res, target)

        converted += 1
        print(f"  {rel} -> skills/{name}/SKILL.md" + ("  [context: fork]" if fm.get("context") == "fork" else ""))

    print(f"\nConverted {converted} skills.")
    if rewrite_counts:
        print("Kiro-path rewrites (.kiro -> .copilot):")
        for k, v in sorted(rewrite_counts.items()):
            print(f"  {k}: {v} occurrence(s)")
    if infra_hits:
        print("Kiro-infrastructure references to FLAG in MIGRATION-NOTES:")
        for k, v in sorted(infra_hits.items()):
            print(f"  {k}: {', '.join(v)}")
    if skipped:
        print("SKIPPED (invalid/empty SKILL.md — flag in MIGRATION-NOTES):")
        for s in skipped:
            print(f"  {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
