#!/usr/bin/env python3
"""
create_templates.py — Generate ATS-optimized docx templates for resume and cover letter.

Creates template files with named Word styles that the generation script will use
to insert content. Templates follow strict ATS rules:
- Single-column layout
- System fonts (Calibri)
- No headers/footers for contact info
- Standard section titles
- Named styles for programmatic insertion

Usage:
    python3 create_templates.py [--output-dir ~/workspace/resume/templates/]
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Inches, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
except ImportError:
    print("ERROR: python-docx is required. Install with: pip3 install python-docx")
    sys.exit(1)

from config import DEFAULT_TEMPLATE_DIR


def create_resume_template(output_path: Path):
    """Create an ATS-optimized resume template with named styles."""
    doc = Document()

    # --- Page Setup ---
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(2.0)
        # Clear headers and footers (ATS can't read them)
        section.header.is_linked_to_previous = True
        section.footer.is_linked_to_previous = True

    # --- Define Custom Styles ---

    # Contact Name style (large, bold)
    style_name = doc.styles.add_style("Contact Name", WD_STYLE_TYPE.PARAGRAPH)
    style_name.font.name = "Calibri"
    style_name.font.size = Pt(18)
    style_name.font.bold = True
    style_name.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    style_name.paragraph_format.space_after = Pt(2)
    style_name.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Contact Info style (smaller, gray)
    style_contact = doc.styles.add_style("Contact Info", WD_STYLE_TYPE.PARAGRAPH)
    style_contact.font.name = "Calibri"
    style_contact.font.size = Pt(10)
    style_contact.font.color.rgb = RGBColor(0x4A, 0x4A, 0x4A)
    style_contact.paragraph_format.space_after = Pt(6)

    # Section Header style
    style_section = doc.styles.add_style("Section Header", WD_STYLE_TYPE.PARAGRAPH)
    style_section.font.name = "Calibri"
    style_section.font.size = Pt(12)
    style_section.font.bold = True
    style_section.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    style_section.paragraph_format.space_before = Pt(12)
    style_section.paragraph_format.space_after = Pt(4)
    style_section.paragraph_format.keep_with_next = True
    # Add bottom border
    pf = style_section.paragraph_format

    # Role Title style (company + title line)
    style_role = doc.styles.add_style("Role Title", WD_STYLE_TYPE.PARAGRAPH)
    style_role.font.name = "Calibri"
    style_role.font.size = Pt(11)
    style_role.font.bold = True
    style_role.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    style_role.paragraph_format.space_before = Pt(8)
    style_role.paragraph_format.space_after = Pt(1)
    style_role.paragraph_format.keep_with_next = True

    # Role Meta style (dates, location)
    style_meta = doc.styles.add_style("Role Meta", WD_STYLE_TYPE.PARAGRAPH)
    style_meta.font.name = "Calibri"
    style_meta.font.size = Pt(10)
    style_meta.font.italic = True
    style_meta.font.color.rgb = RGBColor(0x4A, 0x4A, 0x4A)
    style_meta.paragraph_format.space_after = Pt(4)
    style_meta.paragraph_format.keep_with_next = True

    # Summary Text style
    style_summary = doc.styles.add_style("Summary Text", WD_STYLE_TYPE.PARAGRAPH)
    style_summary.font.name = "Calibri"
    style_summary.font.size = Pt(10.5)
    style_summary.font.color.rgb = RGBColor(0x2A, 0x2A, 0x2A)
    style_summary.paragraph_format.space_after = Pt(6)

    # Skill Category style
    style_skill = doc.styles.add_style("Skill Category", WD_STYLE_TYPE.PARAGRAPH)
    style_skill.font.name = "Calibri"
    style_skill.font.size = Pt(10)
    style_skill.font.color.rgb = RGBColor(0x2A, 0x2A, 0x2A)
    style_skill.paragraph_format.space_after = Pt(2)

    # Bullet Point style
    style_bullet = doc.styles.add_style("Resume Bullet", WD_STYLE_TYPE.PARAGRAPH)
    style_bullet.font.name = "Calibri"
    style_bullet.font.size = Pt(10)
    style_bullet.font.color.rgb = RGBColor(0x2A, 0x2A, 0x2A)
    style_bullet.paragraph_format.left_indent = Cm(0.5)
    style_bullet.paragraph_format.space_after = Pt(2)
    style_bullet.paragraph_format.first_line_indent = Cm(-0.3)

    # Education Entry style
    style_edu = doc.styles.add_style("Education Entry", WD_STYLE_TYPE.PARAGRAPH)
    style_edu.font.name = "Calibri"
    style_edu.font.size = Pt(10.5)
    style_edu.font.color.rgb = RGBColor(0x2A, 0x2A, 0x2A)
    style_edu.paragraph_format.space_after = Pt(4)

    # Additional Experience style (condensed)
    style_additional = doc.styles.add_style("Additional Role", WD_STYLE_TYPE.PARAGRAPH)
    style_additional.font.name = "Calibri"
    style_additional.font.size = Pt(10)
    style_additional.font.color.rgb = RGBColor(0x2A, 0x2A, 0x2A)
    style_additional.paragraph_format.space_after = Pt(2)

    # --- Add Placeholder Content (shows structure) ---

    # Contact info in body (NOT header)
    doc.add_paragraph("{name}", style="Contact Name")
    doc.add_paragraph(
        "{email} | {phone} | {location} | {linkedin}",
        style="Contact Info"
    )

    # Summary section
    doc.add_paragraph("SUMMARY", style="Section Header")
    doc.add_paragraph("{summary_text}", style="Summary Text")

    # Skills section
    doc.add_paragraph("SKILLS", style="Section Header")
    doc.add_paragraph("{category}: {skill1}, {skill2}, {skill3}", style="Skill Category")

    # Experience section
    doc.add_paragraph("EXPERIENCE", style="Section Header")
    doc.add_paragraph("{company} — {title}", style="Role Title")
    doc.add_paragraph("{start_date} – {end_date} | {location}", style="Role Meta")
    doc.add_paragraph("• {bullet_text}", style="Resume Bullet")

    # Additional Experience section
    doc.add_paragraph("PREVIOUS EXPERIENCE", style="Section Header")
    doc.add_paragraph(
        "{title} — {company} ({start_date} – {end_date})",
        style="Additional Role"
    )

    # Education section
    doc.add_paragraph("EDUCATION", style="Section Header")
    doc.add_paragraph("{degree}, {institution} — {graduation_date}", style="Education Entry")

    doc.save(str(output_path))
    print(f"✓ Resume template created: {output_path}")


def create_cover_letter_template(output_path: Path):
    """Create an ATS-optimized cover letter template with named styles."""
    doc = Document()

    # --- Page Setup ---
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
        section.header.is_linked_to_previous = True
        section.footer.is_linked_to_previous = True

    # --- Define Custom Styles ---

    # Sender Name style
    style_sender = doc.styles.add_style("Sender Name", WD_STYLE_TYPE.PARAGRAPH)
    style_sender.font.name = "Calibri"
    style_sender.font.size = Pt(14)
    style_sender.font.bold = True
    style_sender.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    style_sender.paragraph_format.space_after = Pt(2)

    # Sender Contact style
    style_sender_contact = doc.styles.add_style("Sender Contact", WD_STYLE_TYPE.PARAGRAPH)
    style_sender_contact.font.name = "Calibri"
    style_sender_contact.font.size = Pt(10)
    style_sender_contact.font.color.rgb = RGBColor(0x4A, 0x4A, 0x4A)
    style_sender_contact.paragraph_format.space_after = Pt(16)

    # Date style
    style_date = doc.styles.add_style("Letter Date", WD_STYLE_TYPE.PARAGRAPH)
    style_date.font.name = "Calibri"
    style_date.font.size = Pt(10.5)
    style_date.font.color.rgb = RGBColor(0x2A, 0x2A, 0x2A)
    style_date.paragraph_format.space_after = Pt(12)

    # Greeting style
    style_greeting = doc.styles.add_style("Greeting", WD_STYLE_TYPE.PARAGRAPH)
    style_greeting.font.name = "Calibri"
    style_greeting.font.size = Pt(10.5)
    style_greeting.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    style_greeting.paragraph_format.space_after = Pt(8)

    # Body Paragraph style
    style_body = doc.styles.add_style("Letter Body", WD_STYLE_TYPE.PARAGRAPH)
    style_body.font.name = "Calibri"
    style_body.font.size = Pt(10.5)
    style_body.font.color.rgb = RGBColor(0x2A, 0x2A, 0x2A)
    style_body.paragraph_format.space_after = Pt(8)
    style_body.paragraph_format.line_spacing = 1.15

    # Closing style
    style_closing = doc.styles.add_style("Closing", WD_STYLE_TYPE.PARAGRAPH)
    style_closing.font.name = "Calibri"
    style_closing.font.size = Pt(10.5)
    style_closing.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    style_closing.paragraph_format.space_before = Pt(12)
    style_closing.paragraph_format.space_after = Pt(4)

    # Signature style
    style_sig = doc.styles.add_style("Signature", WD_STYLE_TYPE.PARAGRAPH)
    style_sig.font.name = "Calibri"
    style_sig.font.size = Pt(10.5)
    style_sig.font.bold = True
    style_sig.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    style_sig.paragraph_format.space_after = Pt(0)

    # --- Add Placeholder Content ---

    doc.add_paragraph("{name}", style="Sender Name")
    doc.add_paragraph("{email} | {phone} | {location}", style="Sender Contact")

    doc.add_paragraph("{date}", style="Letter Date")
    doc.add_paragraph("{greeting}", style="Greeting")

    # Body paragraphs (hook, value, connection, close)
    doc.add_paragraph("{hook_paragraph}", style="Letter Body")
    doc.add_paragraph("{value_paragraph}", style="Letter Body")
    doc.add_paragraph("{connection_paragraph}", style="Letter Body")
    doc.add_paragraph("{closing_paragraph}", style="Letter Body")

    doc.add_paragraph("Best regards,", style="Closing")
    doc.add_paragraph("{name}", style="Signature")

    doc.save(str(output_path))
    print(f"✓ Cover letter template created: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate ATS-optimized docx templates"
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_TEMPLATE_DIR),
        help="Directory for template output (default: $RESUME_DIR/templates/ or ~/workspace/resume/templates/)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    create_resume_template(output_dir / "resume_template.docx")
    create_cover_letter_template(output_dir / "cover_letter_template.docx")

    print(f"\nTemplates created in: {output_dir}")
    print("Run 'python3 create_templates.py' again to regenerate if styles need updating.")


if __name__ == "__main__":
    main()
