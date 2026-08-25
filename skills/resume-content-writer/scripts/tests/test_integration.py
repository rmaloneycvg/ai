"""Integration tests for the resume-content-writer pipeline.

Tests the end-to-end flow: parse docx → generate content → produce output docx.
Also tests CLI entry points and script interoperability.
"""

import json
import subprocess
import sys
import pytest
from pathlib import Path

from docx import Document

from parse_resumes import extract_resume_data, is_resume_file
from create_templates import create_resume_template, create_cover_letter_template
from generate_docx import generate_resume, generate_cover_letter


SCRIPTS_DIR = Path(__file__).resolve().parent.parent


# ─── Parse → Generate Pipeline ────────────────────────────────────────────────


class TestParseToGeneratePipeline:
    """End-to-end: parse a docx resume, then generate a new resume from the extracted data."""

    def test_parsed_data_feeds_generate(self, sample_docx, tmp_dir):
        """Data extracted from a docx can be transformed into generate_docx input format."""
        # Step 1: Parse
        parsed = extract_resume_data(sample_docx)

        # Step 2: Transform parsed output into generate_docx content format
        content = {
            "personalInfo": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "(555) 123-4567",
                "location": "Denver, CO",
            },
            "headline": "Senior Full-Stack Engineer",
            "summary": parsed["summary"][:50] if parsed["summary"] else "Experienced engineer.",
            "skills": parsed["skills"],
            "experience": [],
            "education": [{"institution": edu, "degree": "", "graduationDate": ""} for edu in parsed["education"]],
        }

        # Transform parsed experience into the expected format
        for role in parsed["experience"]:
            content["experience"].append({
                "company": role.get("clean_header", "Unknown"),
                "location": "",
                "title": "",
                "startDate": role.get("start_date", ""),
                "endDate": role.get("end_date", ""),
                "bullets": role.get("bullets", []),
            })

        # Step 3: Generate
        output = tmp_dir / "generated_resume.docx"
        generate_resume(content, Path("/unused"), output)

        # Verify output
        assert output.exists()
        doc = Document(str(output))
        all_text = " ".join(p.text for p in doc.paragraphs)
        assert "JANE DOE" in all_text
        assert len(doc.paragraphs) > 5

    def test_round_trip_preserves_skills(self, sample_docx, tmp_dir):
        """Skills extracted from a parsed docx appear in the generated output."""
        parsed = extract_resume_data(sample_docx)

        content = {
            "personalInfo": {"name": "Jane Doe", "email": "jane@example.com"},
            "skills": parsed["skills"],
            "experience": [],
        }

        output = tmp_dir / "skills_check.docx"
        generate_resume(content, Path("/unused"), output)

        doc = Document(str(output))
        all_text = " ".join(p.text for p in doc.paragraphs)

        # Skills from the sample docx should appear in output
        if parsed["skills"]:
            for skill in parsed["skills"][0]["skills"][:3]:
                assert skill in all_text

    def test_round_trip_preserves_bullets(self, sample_docx, tmp_dir):
        """Experience bullets from parsing appear in the generated resume."""
        parsed = extract_resume_data(sample_docx)

        experience = []
        for role in parsed["experience"]:
            experience.append({
                "company": "Test Co",
                "title": "Engineer",
                "startDate": role.get("start_date", "01/2020"),
                "endDate": role.get("end_date", "Present"),
                "bullets": role.get("bullets", []),
            })

        content = {
            "personalInfo": {"name": "Jane Doe", "email": "jane@example.com"},
            "experience": experience,
        }

        output = tmp_dir / "bullets_check.docx"
        generate_resume(content, Path("/unused"), output)

        doc = Document(str(output))
        all_text = " ".join(p.text for p in doc.paragraphs)

        # At least one bullet from the parsed data should be in the output
        if parsed["experience"] and parsed["experience"][0]["bullets"]:
            first_bullet = parsed["experience"][0]["bullets"][0]
            assert first_bullet in all_text


# ─── Template → Generate Pipeline ─────────────────────────────────────────────


class TestTemplateToGeneratePipeline:
    """Templates and generate_docx use compatible structures."""

    def test_templates_generate_in_same_directory(self, tmp_dir):
        """Templates and generated docs can coexist in the same output dir."""
        template_dir = tmp_dir / "templates"
        template_dir.mkdir()

        # Create templates
        create_resume_template(template_dir / "resume_template.docx")
        create_cover_letter_template(template_dir / "cover_letter_template.docx")

        assert (template_dir / "resume_template.docx").exists()
        assert (template_dir / "cover_letter_template.docx").exists()

    def test_generated_resume_has_more_content_than_template(self, tmp_dir, sample_resume_content):
        """A generated resume should have more substantive text than the template."""
        template_dir = tmp_dir / "templates"
        template_dir.mkdir()

        # Create template
        template_path = template_dir / "resume_template.docx"
        create_resume_template(template_path)

        # Generate resume
        output_path = tmp_dir / "resume.docx"
        generate_resume(sample_resume_content, template_path, output_path)

        template_doc = Document(str(template_path))
        output_doc = Document(str(output_path))

        template_text = " ".join(p.text for p in template_doc.paragraphs)
        output_text = " ".join(p.text for p in output_doc.paragraphs)

        # Generated doc should have more content
        assert len(output_text) > len(template_text)


# ─── CLI Entry Points ─────────────────────────────────────────────────────────


class TestCLIParseResumes:
    """Test parse_resumes.py CLI behavior."""

    def test_cli_exits_with_error_for_missing_dir(self, tmp_dir):
        """parse_resumes.py exits non-zero when directory doesn't exist."""
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "parse_resumes.py"), "--dir", str(tmp_dir / "nonexistent")],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "ERROR" in result.stdout or "ERROR" in result.stderr

    def test_cli_exits_with_error_for_no_resumes(self, tmp_dir):
        """parse_resumes.py exits non-zero when no resume files are found."""
        empty_dir = tmp_dir / "empty"
        empty_dir.mkdir()
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "parse_resumes.py"), "--dir", str(empty_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_cli_outputs_json(self, sample_docx_dir):
        """parse_resumes.py outputs valid JSON to stdout."""
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "parse_resumes.py"), "--dir", str(sample_docx_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "extraction_count" in data
        assert "extractions" in data
        assert data["extraction_count"] >= 1

    def test_cli_writes_to_output_file(self, sample_docx_dir, tmp_dir):
        """parse_resumes.py writes JSON to specified output file."""
        output_file = tmp_dir / "output.json"
        result = subprocess.run(
            [
                sys.executable, str(SCRIPTS_DIR / "parse_resumes.py"),
                "--dir", str(sample_docx_dir),
                "--output", str(output_file),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["extraction_count"] >= 1


class TestCLICreateTemplates:
    """Test create_templates.py CLI behavior."""

    def test_cli_creates_both_templates(self, tmp_dir):
        """create_templates.py creates resume and cover letter templates."""
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "create_templates.py"), "--output-dir", str(tmp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (tmp_dir / "resume_template.docx").exists()
        assert (tmp_dir / "cover_letter_template.docx").exists()

    def test_cli_creates_output_dir_if_missing(self, tmp_dir):
        """create_templates.py creates the output directory if it doesn't exist."""
        nested_dir = tmp_dir / "deep" / "nested" / "templates"
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "create_templates.py"), "--output-dir", str(nested_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert nested_dir.exists()
        assert (nested_dir / "resume_template.docx").exists()


class TestCLIGenerateDocx:
    """Test generate_docx.py CLI behavior."""

    def test_cli_generates_resume(self, sample_content_json, tmp_dir):
        """generate_docx.py produces a resume .docx from content JSON."""
        output = tmp_dir / "cli_resume.docx"
        result = subprocess.run(
            [
                sys.executable, str(SCRIPTS_DIR / "generate_docx.py"),
                "--type", "resume",
                "--content", str(sample_content_json),
                "--output", str(output),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert output.exists()
        # Verify it's a valid docx
        doc = Document(str(output))
        assert len(doc.paragraphs) > 0

    def test_cli_generates_cover_letter(self, sample_cover_letter_json, tmp_dir):
        """generate_docx.py produces a cover letter .docx from content JSON."""
        output = tmp_dir / "cli_cover_letter.docx"
        result = subprocess.run(
            [
                sys.executable, str(SCRIPTS_DIR / "generate_docx.py"),
                "--type", "cover_letter",
                "--content", str(sample_cover_letter_json),
                "--output", str(output),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert output.exists()
        doc = Document(str(output))
        all_text = " ".join(p.text for p in doc.paragraphs)
        assert "Jane Doe" in all_text

    def test_cli_errors_on_missing_content_file(self, tmp_dir):
        """generate_docx.py exits non-zero when content file doesn't exist."""
        result = subprocess.run(
            [
                sys.executable, str(SCRIPTS_DIR / "generate_docx.py"),
                "--type", "resume",
                "--content", str(tmp_dir / "nonexistent.json"),
                "--output", str(tmp_dir / "output.docx"),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_cli_errors_on_invalid_type(self, sample_content_json, tmp_dir):
        """generate_docx.py rejects invalid --type values."""
        result = subprocess.run(
            [
                sys.executable, str(SCRIPTS_DIR / "generate_docx.py"),
                "--type", "invalid",
                "--content", str(sample_content_json),
                "--output", str(tmp_dir / "output.docx"),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0


# ─── Full Pipeline (parse → transform → generate) ────────────────────────────


class TestFullPipeline:
    """End-to-end integration: CLI parse → manual transform → CLI generate."""

    def test_parse_cli_to_generate_cli(self, sample_docx_dir, tmp_dir):
        """Full pipeline: parse_resumes CLI → transform → generate_docx CLI."""
        # Step 1: Parse via CLI
        parse_result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "parse_resumes.py"), "--dir", str(sample_docx_dir)],
            capture_output=True,
            text=True,
        )
        assert parse_result.returncode == 0
        parsed_data = json.loads(parse_result.stdout)

        # Step 2: Transform to generate_docx format
        extraction = parsed_data["extractions"][0]
        content = {
            "personalInfo": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "(555) 123-4567",
                "location": "Denver, CO",
                "linkedin": "linkedin.com/in/janedoe",
            },
            "headline": "Senior Full-Stack Engineer",
            "summary": extraction["summary"][:50] if extraction["summary"] else "Experienced engineer.",
            "skills": extraction["skills"],
            "experience": [
                {
                    "company": role.get("clean_header", "Company"),
                    "title": role.get("subtitle", "Engineer"),
                    "startDate": role.get("start_date", ""),
                    "endDate": role.get("end_date", ""),
                    "bullets": role.get("bullets", []),
                }
                for role in extraction["experience"]
            ],
            "education": [
                {"institution": edu, "degree": "", "graduationDate": ""}
                for edu in extraction["education"]
            ],
        }

        content_path = tmp_dir / "pipeline_content.json"
        content_path.write_text(json.dumps(content, indent=2))

        # Step 3: Generate via CLI
        output = tmp_dir / "pipeline_resume.docx"
        gen_result = subprocess.run(
            [
                sys.executable, str(SCRIPTS_DIR / "generate_docx.py"),
                "--type", "resume",
                "--content", str(content_path),
                "--output", str(output),
            ],
            capture_output=True,
            text=True,
        )
        assert gen_result.returncode == 0
        assert output.exists()

        # Verify final output
        doc = Document(str(output))
        all_text = " ".join(p.text for p in doc.paragraphs)
        assert "JANE DOE" in all_text
        assert len(doc.paragraphs) > 5

    def test_multiple_resumes_parse_correctly(self, tmp_dir):
        """Multiple resume files in a directory all get parsed."""
        resume_dir = tmp_dir / "multi_resumes"
        resume_dir.mkdir()

        # Create two distinct resume files
        for i, name in enumerate(["resume_v1.docx", "my_resume_v2.docx"]):
            doc = Document()
            doc.add_paragraph(f"Engineer {i + 1}")
            doc.add_paragraph("EXPERIENCE")
            doc.add_paragraph(f"Company {i + 1} — Role | January 2020 – Present")
            doc.add_paragraph(f"• Achievement {i + 1}")
            doc.save(str(resume_dir / name))

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "parse_resumes.py"), "--dir", str(resume_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["extraction_count"] == 2
        assert len(data["extractions"]) == 2
