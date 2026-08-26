#!/usr/bin/env python3
"""
parse_resumes.py — Extract structured text from resume .docx files.

Reads all resume .docx files in ~/workspace/resume/ (skips cover letters),
extracts paragraph text with style information, and outputs structured JSON
for the experience-parser agent to process.

Usage:
    python3 parse_resumes.py [--output raw_extracted.json] [--dir ~/workspace/resume/]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
except ImportError:
    print("ERROR: python-docx is required. Install with: pip3 install python-docx")
    sys.exit(1)

from config import DEFAULT_RESUME_DIR


def is_resume_file(filepath: Path) -> bool:
    """Filter to only resume .docx files (skip cover letters, references, etc.)."""
    name = filepath.name.lower()
    if not name.endswith(".docx"):
        return False
    if name.startswith("~$"):  # Skip temp files
        return False
    if "cover_letter" in name or "cover letter" in name:
        return False
    if "reference" in name:
        return False
    return "resume" in name


def extract_paragraphs(filepath: Path) -> list[dict]:
    """Extract all paragraphs from a docx with their style and formatting info."""
    doc = Document(str(filepath))
    paragraphs = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Detect if this is a bullet point
        is_bullet = False
        if para.style and para.style.name:
            style_name = para.style.name.lower()
            is_bullet = "list" in style_name or "bullet" in style_name

        # Check for bullet characters
        if text.startswith(("•", "●", "○", "▪", "-", "–", "◦")):
            is_bullet = True
            text = re.sub(r"^[•●○▪\-–◦]\s*", "", text)

        paragraphs.append({
            "text": text,
            "style": para.style.name if para.style else "Normal",
            "is_bullet": is_bullet,
            "is_bold": any(run.bold for run in para.runs if run.bold is not None),
            "font_size": next(
                (run.font.size.pt for run in para.runs if run.font.size),
                None
            ),
        })

    return paragraphs


def identify_sections(paragraphs: list[dict]) -> dict[str, list[dict]]:
    """Group paragraphs into resume sections based on heading patterns."""
    sections = {}
    current_section = "header"
    section_patterns = {
        "summary": r"^(professional\s+)?summary|^profile|^about",
        "experience": r"^(professional\s+)?experience|^work\s+history|^employment",
        "skills": r"^(technical\s+)?skills|^technologies|^core\s+competencies",
        "education": r"^education|^academic",
        "certifications": r"^certifications?|^licenses?|^credentials?",
        "additional": r"^additional|^previous|^earlier|^other",
    }

    for para in paragraphs:
        text_lower = para["text"].lower().strip()

        # Check if this paragraph is a section header
        matched_section = None
        for section_name, pattern in section_patterns.items():
            if re.match(pattern, text_lower):
                matched_section = section_name
                break

        # Also detect headers by style (Heading 1, Heading 2) or all-caps
        if not matched_section:
            if para.get("style", "").startswith("Heading"):
                # Try to match the heading text to a section
                for section_name, pattern in section_patterns.items():
                    if re.match(pattern, text_lower):
                        matched_section = section_name
                        break
            elif text_lower == text_lower.upper() and len(text_lower) < 30:
                # ALL CAPS short text is likely a section header
                for section_name, pattern in section_patterns.items():
                    if re.match(pattern, text_lower):
                        matched_section = section_name
                        break

        if matched_section:
            current_section = matched_section
            if current_section not in sections:
                sections[current_section] = []
            continue

        if current_section not in sections:
            sections[current_section] = []
        sections[current_section].append(para)

    return sections


def parse_experience_section(paragraphs: list[dict]) -> list[dict]:
    """Parse experience section into structured role entries."""
    roles = []
    current_role = None

    # Patterns for detecting role headers (Company — Title, dates)
    date_pattern = r"((?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{4})"
    present_pattern = r"(Present|Current)"

    for para in paragraphs:
        text = para["text"]

        # Check if this looks like a role header (has dates or is bold non-bullet)
        has_date = re.search(date_pattern, text) or re.search(present_pattern, text)
        is_non_bullet = not para["is_bullet"]

        if has_date and is_non_bullet:
            # This is likely a role header line — try to extract dates
            dates = re.findall(date_pattern, text)
            has_present = bool(re.search(present_pattern, text))

            # Remove dates from text to get company/title info
            clean_text = re.sub(date_pattern, "", text)
            clean_text = re.sub(present_pattern, "", clean_text)
            clean_text = re.sub(r"[|–—\-]+", "|", clean_text)
            clean_text = re.sub(r"\s+", " ", clean_text).strip(" |,")

            if current_role:
                roles.append(current_role)

            current_role = {
                "header_text": text,
                "clean_header": clean_text,
                "start_date": dates[0] if dates else None,
                "end_date": "Present" if has_present else (dates[1] if len(dates) > 1 else None),
                "bullets": [],
            }
        elif is_non_bullet and para.get("is_bold") and current_role is None:
            # Bold non-bullet without date might be company/title on separate line
            if current_role:
                roles.append(current_role)
            current_role = {
                "header_text": text,
                "clean_header": text,
                "start_date": None,
                "end_date": None,
                "bullets": [],
            }
        elif para["is_bullet"] and current_role:
            current_role["bullets"].append(text)
        elif current_role and not para["is_bullet"]:
            # Non-bullet text after a role header might be a subtitle (title on next line)
            # or continuation — add as context
            if not current_role.get("subtitle"):
                current_role["subtitle"] = text
            else:
                # Treat as a bullet if it's long enough
                if len(text) > 30:
                    current_role["bullets"].append(text)

    if current_role:
        roles.append(current_role)

    return roles


def parse_skills_section(paragraphs: list[dict]) -> list[dict]:
    """Parse skills section into categorized groups."""
    categories = []

    for para in paragraphs:
        text = para["text"]
        # Look for "Category: skill1, skill2, skill3" pattern
        if ":" in text:
            parts = text.split(":", 1)
            category_name = parts[0].strip()
            skills_text = parts[1].strip()
            skills = [s.strip() for s in re.split(r"[,|;•]", skills_text) if s.strip()]
            if skills:
                categories.append({
                    "name": category_name,
                    "skills": skills,
                })
        else:
            # Might be a comma-separated list without a category header
            skills = [s.strip() for s in re.split(r"[,|;•]", text) if s.strip()]
            if skills and len(skills) > 2:
                categories.append({
                    "name": "Uncategorized",
                    "skills": skills,
                })

    return categories


def extract_resume_data(filepath: Path) -> dict:
    """Extract all structured data from a single resume file."""
    paragraphs = extract_paragraphs(filepath)
    sections = identify_sections(paragraphs)

    result = {
        "source_file": filepath.name,
        "header": [p["text"] for p in sections.get("header", [])],
        "summary": " ".join(p["text"] for p in sections.get("summary", [])),
        "experience": parse_experience_section(sections.get("experience", [])),
        "skills": parse_skills_section(sections.get("skills", [])),
        "education": [p["text"] for p in sections.get("education", [])],
        "certifications": [p["text"] for p in sections.get("certifications", [])],
        "additional_experience": parse_experience_section(
            sections.get("additional", [])
        ),
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Extract structured data from resume .docx files"
    )
    parser.add_argument(
        "--dir",
        default=str(DEFAULT_RESUME_DIR),
        help="Directory containing resume .docx files (default: $RESUME_DIR or ~/workspace/resume/)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file path (default: print to stdout)",
    )
    args = parser.parse_args()

    resume_dir = Path(args.dir)
    if not resume_dir.exists():
        print(f"ERROR: Directory not found: {resume_dir}")
        sys.exit(1)

    # Find all resume .docx files recursively (supports YYYY-MM-DD/CompanyName/ structure)
    resume_files = sorted(
        [f for f in resume_dir.rglob("*.docx") if is_resume_file(f)],
        key=lambda f: f.stat().st_mtime,
        reverse=True,  # Most recent first
    )

    if not resume_files:
        print(f"ERROR: No resume .docx files found in {resume_dir}")
        sys.exit(1)

    print(f"Found {len(resume_files)} resume files:", file=sys.stderr)
    for f in resume_files:
        print(f"  - {f.name}", file=sys.stderr)

    # Extract data from each file
    all_extractions = []
    for filepath in resume_files:
        try:
            data = extract_resume_data(filepath)
            all_extractions.append(data)
            print(f"  ✓ Parsed: {filepath.name}", file=sys.stderr)
        except Exception as e:
            print(f"  ✗ Failed: {filepath.name} — {e}", file=sys.stderr)

    output = {
        "extraction_count": len(all_extractions),
        "source_files": [f.name for f in resume_files],
        "extractions": all_extractions,
    }

    # Output
    json_output = json.dumps(output, indent=2, ensure_ascii=False)
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json_output)
        print(f"\nOutput written to: {output_path}", file=sys.stderr)
    else:
        print(json_output)


if __name__ == "__main__":
    main()
