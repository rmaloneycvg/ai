"""Unit tests for create_templates.py."""

import pytest
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE

from create_templates import create_resume_template, create_cover_letter_template


# ─── Resume Template ──────────────────────────────────────────────────────────


class TestCreateResumeTemplate:
    """Tests for resume template generation."""

    def test_creates_file(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        assert output.exists()
        assert output.stat().st_size > 0

    def test_is_valid_docx(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        # Should open without error
        doc = Document(str(output))
        assert len(doc.paragraphs) > 0

    def test_has_contact_name_style(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Contact Name" in style_names

    def test_has_contact_info_style(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Contact Info" in style_names

    def test_has_section_header_style(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Section Header" in style_names

    def test_has_role_title_style(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Role Title" in style_names

    def test_has_role_meta_style(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Role Meta" in style_names

    def test_has_resume_bullet_style(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Resume Bullet" in style_names

    def test_has_summary_text_style(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Summary Text" in style_names

    def test_has_skill_category_style(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Skill Category" in style_names

    def test_has_education_entry_style(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Education Entry" in style_names

    def test_has_additional_role_style(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Additional Role" in style_names

    def test_uses_calibri_font(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        style = doc.styles["Contact Name"]
        assert style.font.name == "Calibri"

    def test_contact_name_is_bold(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        style = doc.styles["Contact Name"]
        assert style.font.bold is True

    def test_contains_placeholder_text(self, tmp_dir):
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        all_text = " ".join(p.text for p in doc.paragraphs)
        assert "{name}" in all_text
        assert "{email}" in all_text
        assert "SUMMARY" in all_text
        assert "EXPERIENCE" in all_text
        assert "EDUCATION" in all_text

    def test_section_order(self, tmp_dir):
        """Sections appear in the expected order."""
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        section_headers = [
            p.text for p in doc.paragraphs
            if p.style and p.style.name == "Section Header"
        ]
        expected_order = ["SUMMARY", "SKILLS", "EXPERIENCE", "PREVIOUS EXPERIENCE", "EDUCATION"]
        assert section_headers == expected_order

    def test_margins_set(self, tmp_dir):
        """Page margins should be set (not default)."""
        output = tmp_dir / "resume_template.docx"
        create_resume_template(output)
        doc = Document(str(output))
        from docx.shared import Cm
        section = doc.sections[0]
        # Allow small EMU rounding tolerance (±200 EMU ~ 0.005mm)
        assert abs(section.left_margin - Cm(2.0)) < 300
        assert abs(section.right_margin - Cm(2.0)) < 300
        assert abs(section.top_margin - Cm(1.5)) < 300
        assert abs(section.bottom_margin - Cm(1.5)) < 300


# ─── Cover Letter Template ────────────────────────────────────────────────────


class TestCreateCoverLetterTemplate:
    """Tests for cover letter template generation."""

    def test_creates_file(self, tmp_dir):
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        assert output.exists()
        assert output.stat().st_size > 0

    def test_is_valid_docx(self, tmp_dir):
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        doc = Document(str(output))
        assert len(doc.paragraphs) > 0

    def test_has_sender_name_style(self, tmp_dir):
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Sender Name" in style_names

    def test_has_sender_contact_style(self, tmp_dir):
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Sender Contact" in style_names

    def test_has_letter_date_style(self, tmp_dir):
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Letter Date" in style_names

    def test_has_greeting_style(self, tmp_dir):
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Greeting" in style_names

    def test_has_letter_body_style(self, tmp_dir):
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Letter Body" in style_names

    def test_has_closing_style(self, tmp_dir):
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Closing" in style_names

    def test_has_signature_style(self, tmp_dir):
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        doc = Document(str(output))
        style_names = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]
        assert "Signature" in style_names

    def test_uses_calibri_font(self, tmp_dir):
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        doc = Document(str(output))
        style = doc.styles["Letter Body"]
        assert style.font.name == "Calibri"

    def test_contains_placeholder_text(self, tmp_dir):
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        doc = Document(str(output))
        all_text = " ".join(p.text for p in doc.paragraphs)
        assert "{name}" in all_text
        assert "{greeting}" in all_text
        assert "{hook_paragraph}" in all_text
        assert "{value_paragraph}" in all_text
        assert "Best regards," in all_text

    def test_wider_margins_than_resume(self, tmp_dir):
        """Cover letter should have wider margins (2.5cm) than resume (1.5-2cm)."""
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        doc = Document(str(output))
        from docx.shared import Cm
        section = doc.sections[0]
        # Allow small EMU rounding tolerance (±200 EMU ~ 0.005mm)
        assert abs(section.left_margin - Cm(2.5)) < 300
        assert abs(section.right_margin - Cm(2.5)) < 300
        assert abs(section.top_margin - Cm(2.5)) < 300
        assert abs(section.bottom_margin - Cm(2.5)) < 300

    def test_body_line_spacing(self, tmp_dir):
        """Letter body style should have 1.15 line spacing."""
        output = tmp_dir / "cover_letter_template.docx"
        create_cover_letter_template(output)
        doc = Document(str(output))
        style = doc.styles["Letter Body"]
        assert style.paragraph_format.line_spacing == 1.15
