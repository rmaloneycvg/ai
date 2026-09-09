---
name: resume-content-writer
description: Use when the user needs tailored resume bullets, executive summaries, cover letters, or full resume content generated for a specific job description. Reads experience data from references/experience.json, analyzes the JD, and produces structured JSON output with resume_content, cover_letter_content, and a self-score.
compatibility: Requires Python 3.10+ with python-docx. Run scripts/setup.sh to install dependencies into a local venv.
metadata: 
  scripts: 
    - scripts/generate_docx.py
  references:
    - references/experience.json
---

# Resume Content Writer

Generate ATS-optimized, voice-authentic resume and cover letter content tailored to a specific job description.

### Environment Setup
All relative paths in this document (e.g., `references/`, `scripts/`) resolve relative to the directory containing this SKILL.md file. 
Do not resolve paths relative to the current working directory of the invoking project.

### Output Directory
All generated documents (.docx files, templates) are written to a configurable output directory. 
Set the `RESUME_DIR` environment variable to override the default (`~/workspace/resume/`). 
All scripts (`setup.sh`, `generate_docx.py`, `parse_resumes.py`, `create_templates.py`) respect this variable.

## Instructions

### Step 1: Load Source Data

Read `references/experience.json` for all experience, skills, education, and personal info. This is the single source of truth — never fabricate beyond it.

### Step 2: Analyze the Job Description

Identify:
- Top 5 requirements by priority
- The hiring manager's biggest pain point
- Must-have vs nice-to-have keywords

### Step 3: Select Relevant Experience

Pick roles and bullets that address the top 5 requirements. Discard irrelevant bullets. Prioritize recent experience (last 10 years get full treatment).

### Step 4: Generate Content

Produce each section following these constraints:

| Section | Constraint |
|---------|-----------|
| Headline | <10 words, matches JD role title language |
| Summary | <50 words, active voice, starts with role noun |
| Skills | JD-relevant tech first, full abbreviation expansions |
| Bullets | Rephrase for impact, front-load keywords, preserve meaning/metrics |
| Cover Letter | 250-300 words: Hook → Value → Connection → Close |

### Step 5: Self-Score and Output

Apply scoring criteria, report gaps, and return structured JSON:

```json
{
  "targetCompany": "Acme Corp",
  "resume_content": { "headline": "...", "summary": "...", "skills": [...], "experience": [...], "education": [...] },
  "cover_letter_content": { "greeting": "...", "hook": "...", "value": "...", "connection": "...", "closing": "..." },
  "score": { "keyword_match": 0, "impact_metrics": 0, "voice_authenticity": 0, "ats_compliance": 0, "overall": 0, "gaps": [...] }
}
```

### Step 6: Generate Documents (Optional)

If the user wants .docx output, ensure dependencies are installed first (`scripts/setup.sh`), then run:
```bash
scripts/.venv/bin/python scripts/generate_docx.py --type resume --content content.json --date 2025-01-27 --pdf
scripts/.venv/bin/python scripts/generate_docx.py --type cover_letter --content content.json --date 2025-01-27 --pdf
```

The script reads `targetCompany` from the content JSON to build the output path (`$RESUME_DIR/YYYY-MM-DD/CompanyName/`). Pass `--company "Name"` to override, `--date YYYY-MM-DD` to control the output directory date, or `--output path/to/file.docx` for a fully custom path.

The `--pdf` flag generates a matching PDF alongside the docx (requires Windows with MS Word installed via `docx2pdf`). Omit `--pdf` on Linux/macOS.

## Bullet Rewriting Rules

| Allowed | Not Allowed |
|---------|-------------|
| Rephrase for clarity | Invent metrics |
| Reorder to front-load keywords | Add technologies not in source |
| Strengthen verb choices | Inflate scope or team size |
| Add JD terminology where honest | Change "contributed to" → "led" |
| Combine text with keyword metadata | Claim undocumented skills |

## Hard Guardrails

- NEVER fabricate metrics, technologies, team sizes, or scope
- NEVER claim skills not documented in experience.json
- NEVER exceed 300 words in the cover letter
- NEVER write task-based bullets ("Responsible for...")
- NEVER copy JD text verbatim into bullets (ATS detects this)
- NEVER use buzzwords: "team player", "hardworking", "synergy", "passionate"
- ALWAYS preserve original meaning when rewriting bullets
- ALWAYS include months on all dates (MM/YYYY format)
- ALWAYS report the score with breakdown in the output

## Reference Files

For detailed guidance, load these as needed:

- `references/guardrails.md` — Hard constraints, truthfulness rules, content red flags
- `references/voice.md` — Voice, tone, personality, anti-patterns, and examples
- `references/ats-optimization.md` — ATS keyword strategy, formatting rules, quantification targets
- `references/resume-format.md` — Section order, formatting templates, timeline structure
- `references/cover-letter.md` — Cover letter structure, tone, and examples
- `references/output-conventions.md` — File naming, directory structure, JSON schemas
- `references/experience.json` — Source of truth for all experience data

## Scripts

- `scripts/generate_docx.py` — Generate ATS-optimized .docx from content JSON
- `scripts/create_templates.py` — Generate template .docx files with named styles
- `scripts/parse_resumes.py` — Extract structured data from existing .docx resumes
- `scripts/setup.sh` — Install Python deps and generate templates

## Example Input

User provides a job description (pasted text or URL) and optionally:
- Target focus (full-stack, frontend, backend, leadership)
- Specific constraints ("emphasize healthcare experience", "keep to 1 page")

## Example Output

The skill returns structured JSON containing tailored resume content, a cover letter, and a self-assessment score with identified gaps. If requested, it also produces .docx files in `$RESUME_DIR/YYYY-MM-DD/[COMPANY NAME]/` (defaults to `~/workspace/resume/YYYY-MM-DD/[COMPANY NAME]/`).

## Edge Cases

- **JD requires a skill not in experience.json**: Report as a gap in score, do not claim it
- **Multiple valid role matches**: Prefer the most recent role; combine bullets from multiple roles only if both are relevant
- **JD is vague or generic**: Ask the user for clarification rather than guessing priorities
- **Years of experience mismatch**: Use 12+ as the floor regardless of JD requirements; never advertise more than JD asks for with a "+" suffix
