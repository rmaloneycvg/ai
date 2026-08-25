"""Shared fixtures for resume-content-writer tests."""

import json
import pytest
from pathlib import Path

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a temporary directory for test outputs."""
    return tmp_path


@pytest.fixture
def sample_resume_content():
    """Minimal valid resume content JSON for generate_docx."""
    return {
        "personalInfo": {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "(555) 123-4567",
            "location": "Denver, CO",
            "linkedin": "linkedin.com/in/janedoe",
            "github": "github.com/janedoe",
        },
        "headline": "Senior Full-Stack Engineer",
        "summary": "Full Stack Engineer with 10+ years delivering scalable web applications across React and Node.js.",
        "skills": [
            {"name": "Languages", "skills": ["TypeScript", "Python", "C#"]},
            {"name": "Frameworks", "skills": ["React", "Node.js", ".NET"]},
        ],
        "experience": [
            {
                "company": "Acme Corp",
                "location": "Remote",
                "title": "Senior Engineer",
                "startDate": "08/2022",
                "endDate": "Present",
                "bullets": [
                    "Built a real-time data pipeline processing 1M events/day, reducing latency by 40%",
                    "Led migration from monolith to microservices, cutting deploy time from 2 hours to 15 minutes",
                ],
            },
            {
                "company": "Startup Inc",
                "location": "Denver, CO",
                "title": "Software Engineer",
                "startDate": "03/2019",
                "endDate": "07/2022",
                "bullets": [
                    "Developed React dashboard used by 500+ daily active users",
                ],
            },
        ],
        "education": [
            {
                "institution": "University of Colorado",
                "degree": "B.S.",
                "field": "Computer Science",
                "graduationDate": "2018",
            }
        ],
        "projects": [
            {
                "name": "OpenSource CLI",
                "description": "A developer productivity tool",
                "url": "github.com/janedoe/cli",
            }
        ],
        "certifications": [
            {"name": "AWS Solutions Architect", "issuer": "Amazon", "date": "2024"}
        ],
    }


@pytest.fixture
def sample_cover_letter_content():
    """Minimal valid cover letter content JSON for generate_docx."""
    return {
        "personalInfo": {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "(555) 123-4567",
            "location": "Denver, CO",
        },
        "date": "August 24, 2026",
        "greeting": "Dear Engineering Hiring Manager,",
        "hook": "When I saw that Acme Corp is scaling its platform to handle global markets, I knew this was the role for me.",
        "value": "In my most recent role, I built a data pipeline that processes over 1M events daily, cutting latency by 40% and saving the team hours of manual work each week.",
        "connection": "What excites me about Acme is the chance to solve real scaling problems alongside a team that cares about craft.",
        "closing": "I would love to discuss how my experience maps to your current challenges.",
    }


@pytest.fixture
def sample_content_json(tmp_dir, sample_resume_content):
    """Write sample resume content to a JSON file and return its path."""
    path = tmp_dir / "content.json"
    path.write_text(json.dumps(sample_resume_content, indent=2))
    return path


@pytest.fixture
def sample_cover_letter_json(tmp_dir, sample_cover_letter_content):
    """Write sample cover letter content to a JSON file and return its path."""
    path = tmp_dir / "cover_letter_content.json"
    path.write_text(json.dumps(sample_cover_letter_content, indent=2))
    return path


@pytest.fixture
def sample_docx(tmp_dir):
    """Create a minimal resume-like .docx for parse_resumes tests."""
    filepath = tmp_dir / "test_resume.docx"
    doc = Document()

    # Name
    p = doc.add_paragraph("Jane Doe")
    for run in p.runs:
        run.bold = True
        run.font.size = Pt(18)

    # Contact
    doc.add_paragraph("jane@example.com | (555) 123-4567 | Denver, CO")

    # Summary section
    doc.add_paragraph("PROFESSIONAL SUMMARY")
    doc.add_paragraph("Experienced full-stack engineer with 10+ years building scalable web apps.")

    # Skills section
    doc.add_paragraph("TECHNICAL SKILLS")
    doc.add_paragraph("Languages: TypeScript, Python, C#")
    doc.add_paragraph("Frameworks: React, Node.js, .NET")

    # Experience section
    doc.add_paragraph("EXPERIENCE")
    p = doc.add_paragraph("Acme Corp — Senior Engineer | August 2022 – Present")
    for run in p.runs:
        run.bold = True

    # Bullets (use List Bullet style if available, otherwise prefix with bullet char)
    doc.add_paragraph("• Built real-time data pipeline processing 1M events/day")
    doc.add_paragraph("• Led migration from monolith to microservices")

    # Education
    doc.add_paragraph("EDUCATION")
    doc.add_paragraph("B.S. Computer Science, University of Colorado — 2018")

    doc.save(str(filepath))
    return filepath


@pytest.fixture
def sample_docx_dir(tmp_dir, sample_docx):
    """Create a directory with a properly named resume .docx file."""
    resume_dir = tmp_dir / "resumes"
    resume_dir.mkdir()

    # Copy the sample docx with a resume-style filename
    import shutil
    dest = resume_dir / "Jane_Doe_resume.docx"
    shutil.copy2(str(sample_docx), str(dest))

    # Also add a cover letter file that should be skipped
    cl_path = resume_dir / "Jane_Doe_cover_letter.docx"
    doc = Document()
    doc.add_paragraph("This is a cover letter and should be skipped.")
    doc.save(str(cl_path))

    return resume_dir
