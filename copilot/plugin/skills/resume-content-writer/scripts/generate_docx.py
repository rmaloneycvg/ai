#!/usr/bin/env python3
"""
generate_docx.py — Generate ATS-optimized resume or cover letter docx from content JSON.

Follows strict ATS optimization guidelines:
- No headers/footers — all content in body only
- Standard fonts only (Calibri) at readable sizes (≥10pt)
- Single-column layout, no tables or graphics
- Pipe (|) separators between inline information
- Resume headline as summary section title (not generic "Professional Summary")
- Section order: Headline/Summary → Contact Info → Skills → Work Experience → Education → Projects → Optional
- Work experience format: [Company], [Location] | [Job Title] | [MM/YYYY – MM/YYYY]
- Bullet format: [Accomplishment summary]: [Action] that resulted in [quantifiable outcome]
- Full abbreviation expansions for ATS keyword matching (e.g. "Amazon Web Services (AWS)")
- Keywords from job descriptions peppered into Skills, Work Experience, and Education
- 1 page target (2 pages max for 10+ years experience)

Usage:
    python3 generate_docx.py --type resume --content content.json --output ./output/resume.docx
    python3 generate_docx.py --type cover_letter --content content.json --output ./output/cover_letter.docx
    python3 generate_docx.py --type resume --content content.json --output ./output/resume.docx --template ./templates/resume_template.docx

Content JSON format for resume:
{
    "targetCompany": "Acme Corp",
    "personalInfo": {
        "name": "...",
        "email": "...",
        "phone": "...",
        "location": "City, State",
        "linkedin": "linkedin.com/in/...",
        "github": "github.com/..."
    },
    "headline": "Sr. Full-Stack Engineer with 10+ Years Building Scalable Systems",
    "summary": "Under 50 words. Active voice, action words, starts with noun describing role...",
    "skills": [
        { "name": "Languages", "skills": ["TypeScript", "Python", "Go"] },
        { "name": "Frameworks", "skills": ["React", "Node.js", ".NET"] },
        { "name": "Databases", "skills": ["PostgreSQL", "Redis", "MongoDB"] }
    ],
    "experience": [
        {
            "company": "Acme Corp",
            "location": "Remote",
            "title": "Senior Engineer",
            "startDate": "08/2022",
            "endDate": "Present",
            "bullets": ["Accomplishment: Action resulting in quantifiable outcome", ...]
        }
    ],
    "education": [
        {
            "institution": "University",
            "degree": "B.S. Computer Science",
            "graduationDate": "2005"
        }
    ],
    "projects": [
        { "name": "Project Name", "description": "Brief description with keywords", "url": "..." }
    ],
    "certifications": [
        { "name": "AWS Solutions Architect", "issuer": "Amazon", "date": "2024" }
    ]
}

Content JSON format for cover_letter:
{
    "targetCompany": "Acme Corp",
    "personalInfo": { "name": "...", "email": "...", "phone": "...", "location": "..." },
    "date": "July 29, 2026",
    "greeting": "Dear Engineering Hiring Manager,",
    "hook": "When I saw that...",
    "value": "In my most recent role...",
    "connection": "What excites me about...",
    "closing": "I would welcome the opportunity..."
}
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn, nsdecls
    from docx.oxml import parse_xml
except ImportError:
    print("ERROR: python-docx is required. Install with: pip3 install python-docx")
    sys.exit(1)

try:
    from docx2pdf import convert as docx2pdf_convert
    HAS_DOCX2PDF = True
except ImportError:
    HAS_DOCX2PDF = False

from config import DEFAULT_RESUME_DIR, DEFAULT_TEMPLATE_DIR

# ATS formatting constants
FONT_NAME = "Lato"
FONT_SIZE_NAME = 14
FONT_SIZE_SECTION = 11
FONT_SIZE_BODY = 10
FONT_SIZE_CONTACT = 10
COLOR_HEADING = (0x00, 0x3D, 0x7A)  # Royal blue for headers/section titles
COLOR_BODY = (0x2A, 0x2A, 0x2A)
COLOR_META = (0x4A, 0x4A, 0x4A)
MARGIN_CM = 1.27  # 0.5 inch — reduced margins per ATS guide


def add_bottom_border(paragraph):
    """Add a thin bottom border as section separator (royal blue accent)."""
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = parse_xml(
        '<w:pBdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:bottom w:val="single" w:sz="6" w:space="1" w:color="003D7A"/>'
        '</w:pBdr>'
    )
    pPr.append(pBdr)


def set_spacing(paragraph, before=0, after=0):
    """Set paragraph spacing in points."""
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)


def add_run(paragraph, text, size=FONT_SIZE_BODY, bold=False, italic=False, color=COLOR_BODY):
    """Add a formatted run to a paragraph using ATS-safe font."""
    run = paragraph.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)
    return run


def setup_document():
    """Create a blank document with ATS-optimized page setup."""
    doc = Document()

    for section in doc.sections:
        section.top_margin = Cm(MARGIN_CM)
        section.bottom_margin = Cm(MARGIN_CM)
        section.left_margin = Cm(MARGIN_CM)
        section.right_margin = Cm(MARGIN_CM)
        # Clear headers and footers — ATS cannot read them
        section.header.is_linked_to_previous = True
        section.footer.is_linked_to_previous = True
        for p in section.header.paragraphs:
            p.text = ""
        for p in section.footer.paragraphs:
            p.text = ""

    # Remove default empty paragraph
    if doc.paragraphs:
        doc.paragraphs[0]._element.getparent().remove(doc.paragraphs[0]._element)

    return doc


def generate_resume(content: dict, template_path: Path, output_path: Path):
    """Generate an ATS-optimized resume docx from content JSON."""
    doc = setup_document()

    personal = content["personalInfo"]

    # ─── NAME (top of resume, largest text) ───
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_run(p, personal["name"].upper(), size=FONT_SIZE_NAME, bold=True, color=COLOR_HEADING)

    # ─── CONTACT INFORMATION (pipe-separated, centered) ───
    contact_parts = []
    if personal.get("email"):
        contact_parts.append(personal["email"])
    if personal.get("phone"):
        contact_parts.append(personal["phone"])
    if personal.get("location"):
        contact_parts.append(personal["location"])
    if personal.get("linkedin"):
        contact_parts.append(personal["linkedin"])
    if personal.get("github"):
        contact_parts.append(personal["github"])

    if contact_parts:
        p = doc.add_paragraph()
        set_spacing(p, before=2, after=2)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_run(p, " | ".join(contact_parts), size=FONT_SIZE_CONTACT, color=COLOR_META)

    # ─── PROFESSIONAL SUMMARY (headline as section title) ───
    # The headline IS the section title — not "Professional Summary"
    headline = content.get("headline", "Professional Summary")
    p = doc.add_paragraph()
    set_spacing(p, before=8, after=4)
    add_run(p, headline, size=FONT_SIZE_SECTION, bold=True, color=COLOR_HEADING)
    add_bottom_border(p)

    if content.get("summary"):
        p = doc.add_paragraph()
        set_spacing(p, before=2, after=6)
        add_run(p, content["summary"], size=FONT_SIZE_BODY, color=COLOR_BODY)

    # ─── SKILLS ───
    # Format: [Category]: [skill | skill | skill]
    if content.get("skills"):
        p = doc.add_paragraph()
        set_spacing(p, before=8, after=4)
        add_run(p, "Skills", size=FONT_SIZE_SECTION, bold=True, color=COLOR_HEADING)
        add_bottom_border(p)

        for category in content["skills"]:
            p = doc.add_paragraph()
            set_spacing(p, before=2, after=2)
            add_run(p, f"{category['name']}: ", size=FONT_SIZE_BODY, bold=True, color=COLOR_BODY)
            skills_str = " | ".join(category["skills"])
            add_run(p, skills_str, size=FONT_SIZE_BODY, color=COLOR_BODY)

    # ─── WORK EXPERIENCE ───
    # Format: [Company], [Location] | [Job Title] | [MM/YYYY – MM/YYYY]
    if content.get("experience"):
        p = doc.add_paragraph()
        set_spacing(p, before=8, after=4)
        add_run(p, "Work Experience", size=FONT_SIZE_SECTION, bold=True, color=COLOR_HEADING)
        add_bottom_border(p)

        for role in content["experience"]:
            # Role header line
            p = doc.add_paragraph()
            set_spacing(p, before=6, after=1)

            header_parts = []
            company_loc = role["company"]
            if role.get("location"):
                company_loc += f", {role['location']}"
            header_parts.append(company_loc)
            header_parts.append(role["title"])

            date_range = ""
            if role.get("startDate") and role.get("endDate"):
                date_range = f"{role['startDate']} – {role['endDate']}"
            elif role.get("startDate"):
                date_range = f"{role['startDate']} – Present"
            if date_range:
                header_parts.append(date_range)

            add_run(p, " | ".join(header_parts), size=FONT_SIZE_BODY, bold=True, color=COLOR_HEADING)

            # Bullet points
            for bullet in role.get("bullets", []):
                p = doc.add_paragraph()
                set_spacing(p, before=2, after=3)
                p.paragraph_format.left_indent = Cm(0.5)
                add_run(p, f"• {bullet}", size=FONT_SIZE_BODY, color=COLOR_BODY)

    # ─── EDUCATION ───
    if content.get("education"):
        p = doc.add_paragraph()
        set_spacing(p, before=8, after=4)
        add_run(p, "Education", size=FONT_SIZE_SECTION, bold=True, color=COLOR_HEADING)
        add_bottom_border(p)

        for edu in content["education"]:
            p = doc.add_paragraph()
            set_spacing(p, before=2, after=2)
            add_run(p, edu.get("institution", ""), size=FONT_SIZE_BODY, bold=True, color=COLOR_BODY)

            meta_parts = []
            if edu.get("degree"):
                meta_parts.append(edu["degree"])
            if edu.get("field"):
                meta_parts[-1] = f"{meta_parts[-1]} in {edu['field']}" if meta_parts else edu["field"]
            if edu.get("graduationDate"):
                meta_parts.append(edu["graduationDate"])
            if edu.get("honors"):
                meta_parts.append(edu["honors"])

            if meta_parts:
                add_run(p, " | " + " | ".join(meta_parts), size=FONT_SIZE_BODY, color=COLOR_BODY)

    # ─── PROJECTS (optional) ───
    if content.get("projects"):
        p = doc.add_paragraph()
        set_spacing(p, before=8, after=4)
        add_run(p, "Projects", size=FONT_SIZE_SECTION, bold=True, color=COLOR_HEADING)
        add_bottom_border(p)

        for project in content["projects"]:
            p = doc.add_paragraph()
            set_spacing(p, before=2, after=2)
            text = project["name"]
            if project.get("description"):
                text += f": {project['description']}"
            if project.get("url"):
                text += f" ({project['url']})"
            add_run(p, text, size=FONT_SIZE_BODY, color=COLOR_BODY)

    # ─── CERTIFICATIONS (optional) ───
    if content.get("certifications"):
        p = doc.add_paragraph()
        set_spacing(p, before=8, after=4)
        add_run(p, "Certifications", size=FONT_SIZE_SECTION, bold=True, color=COLOR_HEADING)
        add_bottom_border(p)

        for cert in content["certifications"]:
            p = doc.add_paragraph()
            set_spacing(p, before=2, after=2)
            text = cert["name"]
            if cert.get("issuer"):
                text += f" — {cert['issuer']}"
            if cert.get("date"):
                text += f" ({cert['date']})"
            add_run(p, text, size=FONT_SIZE_BODY, color=COLOR_BODY)

    # ─── SAVE ───
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"✓ Resume generated: {output_path}")

    # Page count estimation (~45 lines per page with these margins/sizes)
    line_count = sum(1 for p in doc.paragraphs if p.text.strip())
    estimated_pages = max(1, round(line_count / 45, 1))
    if estimated_pages > 2:
        print(
            f"  ⚠ WARNING: Estimated {estimated_pages} pages — exceeds 2-page limit. "
            f"Consider reducing bullets or condensing older roles.",
            file=sys.stderr,
        )
    elif estimated_pages > 1:
        print(f"  Estimated length: ~{estimated_pages} pages", file=sys.stderr)
    else:
        print(f"  Estimated length: ~1 page ✓", file=sys.stderr)


def generate_cover_letter(content: dict, template_path: Path, output_path: Path):
    """Generate a cover letter docx from content JSON."""
    doc = setup_document()

    # Wider margins for cover letter (more formal)
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    personal = content["personalInfo"]

    # Sender info
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=2)
    add_run(p, personal["name"], size=14, bold=True, color=COLOR_HEADING)

    contact_parts = [personal.get("email", ""), personal.get("phone", "")]
    if personal.get("location"):
        contact_parts.append(personal["location"])
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=16)
    add_run(p, " | ".join(part for part in contact_parts if part), size=FONT_SIZE_BODY, color=COLOR_META)

    # Date
    if content.get("date"):
        p = doc.add_paragraph()
        set_spacing(p, before=0, after=12)
        add_run(p, content["date"], size=10.5, color=COLOR_BODY)

    # Greeting
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=8)
    add_run(p, content.get("greeting", "Dear Hiring Manager,"), size=10.5, color=COLOR_HEADING)

    # Body paragraphs
    for section_key in ["hook", "value", "connection", "closing"]:
        text = content.get(section_key, "")
        if text:
            p = doc.add_paragraph()
            set_spacing(p, before=0, after=8)
            add_run(p, text, size=10.5, color=COLOR_BODY)

    # Sign-off
    p = doc.add_paragraph()
    set_spacing(p, before=12, after=4)
    add_run(p, "Best regards,", size=10.5, color=COLOR_HEADING)

    p = doc.add_paragraph()
    set_spacing(p, before=0, after=0)
    add_run(p, personal["name"], size=10.5, bold=True, color=COLOR_HEADING)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"✓ Cover letter generated: {output_path}")

    # Word count check
    word_count = sum(
        len(p.text.split())
        for p in doc.paragraphs
        if p.text.strip()
    )
    body_word_count = word_count - 10  # Subtract name, contact, sign-off
    if body_word_count > 300:
        print(
            f"  ⚠ WARNING: Cover letter is ~{body_word_count} words — exceeds 300 word limit.",
            file=sys.stderr,
        )
    elif body_word_count < 200:
        print(
            f"  ⚠ NOTE: Cover letter is ~{body_word_count} words — target 250-300.",
            file=sys.stderr,
        )
    else:
        print(f"  Word count: ~{body_word_count} (within 250-300 target) ✓", file=sys.stderr)


def to_pascal_case(name: str) -> str:
    """Convert a company name to PascalCase for directory/file naming."""
    # Remove non-alphanumeric chars (except spaces), then PascalCase each word
    cleaned = re.sub(r"[^\w\s]", "", name)
    return "".join(word.capitalize() for word in cleaned.split())


def build_output_path(company: str, doc_type: str, resume_dir: Path, date_override: str = None) -> Path:
    """Build the canonical output path: $RESUME_DIR/YYYY-MM-DD/CompanyName/filename.docx"""
    company_dir = to_pascal_case(company)
    date_str = date_override or date.today().isoformat()
    prefix = "Resume" if doc_type == "resume" else "Cover_Letter"
    filename = f"{prefix}_{company_dir}.docx"
    return resume_dir / date_str / company_dir / filename


def main():
    parser = argparse.ArgumentParser(
        description="Generate ATS-optimized resume or cover letter docx from content JSON"
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["resume", "cover_letter"],
        help="Document type to generate",
    )
    parser.add_argument(
        "--content",
        required=True,
        help="Path to content JSON file",
    )
    parser.add_argument(
        "--company",
        default=None,
        help="Target company name (used for output directory and file naming). Inferred from content JSON 'targetCompany' field if omitted.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Explicit output docx path (overrides --company-based path generation)",
    )
    parser.add_argument(
        "--template",
        default=None,
        help="Path to template docx (ignored — generates from scratch for ATS safety)",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        default=False,
        help="Also generate a PDF via docx2pdf (requires Windows with MS Word installed)",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Date for output directory (YYYY-MM-DD format). Uses today's date if not specified.",
    )
    args = parser.parse_args()

    # Load content
    content_path = Path(args.content)
    if not content_path.exists():
        print(f"ERROR: Content file not found: {content_path}")
        sys.exit(1)

    with open(content_path) as f:
        content = json.load(f)

    # Determine company name: CLI arg > content JSON > error
    company = args.company or content.get("targetCompany")
    if not company and not args.output:
        print(
            "ERROR: --company not provided and 'targetCompany' not found in content JSON. "
            "Either pass --company or add a 'targetCompany' field to the content JSON.",
        )
        sys.exit(1)

    # Determine output path: explicit --output wins, otherwise build from company
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = build_output_path(company, args.type, DEFAULT_RESUME_DIR, args.date)

    # Template path (kept for API compat but not used — we generate from scratch)
    template_path = Path(args.template) if args.template else DEFAULT_TEMPLATE_DIR / "resume_template.docx"

    # Generate
    if args.type == "resume":
        generate_resume(content, template_path, output_path)
    else:
        generate_cover_letter(content, template_path, output_path)

    # PDF conversion (Windows only via docx2pdf)
    if args.pdf:
        if not HAS_DOCX2PDF:
            print(
                "  ⚠ WARNING: --pdf requested but docx2pdf is not installed. "
                "Install with: pip install docx2pdf (Windows only, requires MS Word)",
                file=sys.stderr,
            )
        else:
            pdf_path = output_path.with_suffix(".pdf")
            try:
                docx2pdf_convert(str(output_path), str(pdf_path))
                print(f"✓ PDF generated: {pdf_path}")
            except Exception as e:
                print(f"  ✗ PDF conversion failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
