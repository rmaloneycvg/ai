"""Unit tests for parse_resumes.py."""

import pytest
from pathlib import Path

from parse_resumes import (
    is_resume_file,
    extract_paragraphs,
    identify_sections,
    parse_experience_section,
    parse_skills_section,
    extract_resume_data,
)


# ─── is_resume_file ───────────────────────────────────────────────────────────


class TestIsResumeFile:
    """Tests for the resume file filter function."""

    def test_accepts_resume_docx(self, tmp_dir):
        f = tmp_dir / "Jane_Doe_resume.docx"
        f.touch()
        assert is_resume_file(f) is True

    def test_accepts_resume_in_name(self, tmp_dir):
        f = tmp_dir / "my_resume_2026.docx"
        f.touch()
        assert is_resume_file(f) is True

    def test_rejects_cover_letter(self, tmp_dir):
        f = tmp_dir / "Jane_cover_letter.docx"
        f.touch()
        assert is_resume_file(f) is False

    def test_rejects_cover_letter_underscored(self, tmp_dir):
        f = tmp_dir / "cover_letter_resume_mention.docx"
        f.touch()
        assert is_resume_file(f) is False

    def test_rejects_reference_file(self, tmp_dir):
        f = tmp_dir / "reference_list.docx"
        f.touch()
        assert is_resume_file(f) is False

    def test_rejects_non_docx(self, tmp_dir):
        f = tmp_dir / "resume.pdf"
        f.touch()
        assert is_resume_file(f) is False

    def test_rejects_temp_file(self, tmp_dir):
        f = tmp_dir / "~$resume.docx"
        f.touch()
        assert is_resume_file(f) is False

    def test_rejects_unrelated_docx(self, tmp_dir):
        f = tmp_dir / "meeting_notes.docx"
        f.touch()
        assert is_resume_file(f) is False

    def test_case_insensitive(self, tmp_dir):
        f = tmp_dir / "My_RESUME_Final.docx"
        f.touch()
        assert is_resume_file(f) is True


# ─── extract_paragraphs ──────────────────────────────────────────────────────


class TestExtractParagraphs:
    """Tests for paragraph extraction from docx files."""

    def test_extracts_non_empty_paragraphs(self, sample_docx):
        paragraphs = extract_paragraphs(sample_docx)
        assert len(paragraphs) > 0
        # All returned paragraphs should have non-empty text
        for p in paragraphs:
            assert p["text"].strip() != ""

    def test_paragraph_has_required_keys(self, sample_docx):
        paragraphs = extract_paragraphs(sample_docx)
        required_keys = {"text", "style", "is_bullet", "is_bold", "font_size"}
        for p in paragraphs:
            assert required_keys.issubset(p.keys())

    def test_detects_bullet_characters(self, sample_docx):
        paragraphs = extract_paragraphs(sample_docx)
        bullets = [p for p in paragraphs if p["is_bullet"]]
        # Our sample has bullet-prefixed paragraphs
        assert len(bullets) >= 2

    def test_strips_bullet_prefix(self, sample_docx):
        paragraphs = extract_paragraphs(sample_docx)
        bullets = [p for p in paragraphs if p["is_bullet"]]
        for b in bullets:
            # Bullet character should be stripped from text
            assert not b["text"].startswith("•")
            assert not b["text"].startswith("●")
            assert not b["text"].startswith("-")

    def test_detects_bold(self, sample_docx):
        paragraphs = extract_paragraphs(sample_docx)
        bold_paras = [p for p in paragraphs if p["is_bold"]]
        # "Jane Doe" and the role header should be bold
        assert len(bold_paras) >= 1


# ─── identify_sections ────────────────────────────────────────────────────────


class TestIdentifySections:
    """Tests for section grouping logic."""

    def test_finds_experience_section(self, sample_docx):
        paragraphs = extract_paragraphs(sample_docx)
        sections = identify_sections(paragraphs)
        assert "experience" in sections
        assert len(sections["experience"]) > 0

    def test_finds_skills_section(self, sample_docx):
        paragraphs = extract_paragraphs(sample_docx)
        sections = identify_sections(paragraphs)
        assert "skills" in sections
        assert len(sections["skills"]) > 0

    def test_finds_summary_section(self, sample_docx):
        paragraphs = extract_paragraphs(sample_docx)
        sections = identify_sections(paragraphs)
        assert "summary" in sections

    def test_finds_education_section(self, sample_docx):
        paragraphs = extract_paragraphs(sample_docx)
        sections = identify_sections(paragraphs)
        assert "education" in sections

    def test_header_paragraphs_not_in_section_content(self, sample_docx):
        """Section header text like 'EXPERIENCE' should not appear as content."""
        paragraphs = extract_paragraphs(sample_docx)
        sections = identify_sections(paragraphs)
        for section_name, content in sections.items():
            for p in content:
                # The section title itself shouldn't be in the content
                assert p["text"].upper() != "EXPERIENCE"
                assert p["text"].upper() != "TECHNICAL SKILLS"
                assert p["text"].upper() != "EDUCATION"

    def test_recognizes_various_section_patterns(self):
        """Test that different phrasing of section headers is recognized."""
        test_paragraphs = [
            {"text": "Work History", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
            {"text": "Built things at a company", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
            {"text": "Core Competencies", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
            {"text": "Python, React, Node.js", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
        ]
        sections = identify_sections(test_paragraphs)
        assert "experience" in sections
        assert "skills" in sections


# ─── parse_experience_section ─────────────────────────────────────────────────


class TestParseExperienceSection:
    """Tests for experience section parsing into structured roles."""

    def test_extracts_roles_from_sample(self, sample_docx):
        paragraphs = extract_paragraphs(sample_docx)
        sections = identify_sections(paragraphs)
        roles = parse_experience_section(sections.get("experience", []))
        assert len(roles) >= 1

    def test_role_has_bullets(self, sample_docx):
        paragraphs = extract_paragraphs(sample_docx)
        sections = identify_sections(paragraphs)
        roles = parse_experience_section(sections.get("experience", []))
        # First role should have bullets
        assert len(roles[0]["bullets"]) >= 1

    def test_detects_dates_in_header(self):
        """Paragraphs with dates should start a new role."""
        test_paras = [
            {"text": "Acme Corp — Senior Engineer | August 2022 – Present", "style": "Normal", "is_bullet": False, "is_bold": True, "font_size": None},
            {"text": "Built a real-time data pipeline", "style": "Normal", "is_bullet": True, "is_bold": False, "font_size": None},
            {"text": "Led migration to microservices", "style": "Normal", "is_bullet": True, "is_bold": False, "font_size": None},
            {"text": "Startup Inc — Engineer | March 2019 – July 2022", "style": "Normal", "is_bullet": False, "is_bold": True, "font_size": None},
            {"text": "Developed React dashboard", "style": "Normal", "is_bullet": True, "is_bold": False, "font_size": None},
        ]
        roles = parse_experience_section(test_paras)
        assert len(roles) == 2
        assert len(roles[0]["bullets"]) == 2
        assert len(roles[1]["bullets"]) == 1

    def test_extracts_start_date(self):
        test_paras = [
            {"text": "Acme Corp | January 2020 – December 2023", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
            {"text": "Did some work", "style": "Normal", "is_bullet": True, "is_bold": False, "font_size": None},
        ]
        roles = parse_experience_section(test_paras)
        assert roles[0]["start_date"] == "January 2020"

    def test_detects_present_end_date(self):
        test_paras = [
            {"text": "Acme Corp | September 2022 – Present", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
            {"text": "Doing great work", "style": "Normal", "is_bullet": True, "is_bold": False, "font_size": None},
        ]
        roles = parse_experience_section(test_paras)
        assert roles[0]["end_date"] == "Present"

    def test_handles_abbreviated_months(self):
        test_paras = [
            {"text": "Company X | Sep 2020 – Aug 2022", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
            {"text": "Wrote code", "style": "Normal", "is_bullet": True, "is_bold": False, "font_size": None},
        ]
        roles = parse_experience_section(test_paras)
        assert roles[0]["start_date"] == "Sep 2020"


# ─── parse_skills_section ─────────────────────────────────────────────────────


class TestParseSkillsSection:
    """Tests for skills section parsing."""

    def test_parses_colon_delimited_categories(self):
        test_paras = [
            {"text": "Languages: TypeScript, Python, C#", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
            {"text": "Frameworks: React, Node.js, .NET", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
        ]
        categories = parse_skills_section(test_paras)
        assert len(categories) == 2
        assert categories[0]["name"] == "Languages"
        assert "TypeScript" in categories[0]["skills"]
        assert "Python" in categories[0]["skills"]
        assert categories[1]["name"] == "Frameworks"

    def test_handles_pipe_separated_skills(self):
        test_paras = [
            {"text": "Cloud: AWS | Azure | GCP", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
        ]
        categories = parse_skills_section(test_paras)
        assert len(categories) == 1
        assert "AWS" in categories[0]["skills"]
        assert "Azure" in categories[0]["skills"]
        assert "GCP" in categories[0]["skills"]

    def test_handles_semicolons(self):
        test_paras = [
            {"text": "Tools: Git; Docker; Terraform", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
        ]
        categories = parse_skills_section(test_paras)
        assert "Git" in categories[0]["skills"]
        assert "Docker" in categories[0]["skills"]

    def test_uncategorized_comma_list(self):
        test_paras = [
            {"text": "Python, JavaScript, Go, Rust, Java", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
        ]
        categories = parse_skills_section(test_paras)
        assert len(categories) == 1
        assert categories[0]["name"] == "Uncategorized"
        assert "Python" in categories[0]["skills"]

    def test_ignores_short_non_categorized_text(self):
        """A short text without a colon and fewer than 3 items should be ignored."""
        test_paras = [
            {"text": "Python, JS", "style": "Normal", "is_bullet": False, "is_bold": False, "font_size": None},
        ]
        categories = parse_skills_section(test_paras)
        assert len(categories) == 0


# ─── extract_resume_data (full extraction) ────────────────────────────────────


class TestExtractResumeData:
    """Tests for the full extraction pipeline on a single docx."""

    def test_returns_expected_keys(self, sample_docx):
        data = extract_resume_data(sample_docx)
        expected_keys = {
            "source_file",
            "header",
            "summary",
            "experience",
            "skills",
            "education",
            "certifications",
            "additional_experience",
        }
        assert expected_keys.issubset(data.keys())

    def test_source_file_is_filename(self, sample_docx):
        data = extract_resume_data(sample_docx)
        assert data["source_file"] == sample_docx.name

    def test_extracts_skills(self, sample_docx):
        data = extract_resume_data(sample_docx)
        assert len(data["skills"]) >= 1
        # Should find our "Languages" category
        category_names = [c["name"] for c in data["skills"]]
        assert "Languages" in category_names

    def test_extracts_experience(self, sample_docx):
        data = extract_resume_data(sample_docx)
        assert len(data["experience"]) >= 1

    def test_extracts_education(self, sample_docx):
        data = extract_resume_data(sample_docx)
        assert len(data["education"]) >= 1
