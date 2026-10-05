---
name: resume-content-writer
description: Use when the user needs to generate a resume and cover lettered tailored to a job description (JD). 
compatibility: Requires Python 3.10+ with python-docx. Run /home/ryanm/workspace/ai/skills/resume-content-writer/scripts/setup.sh to install dependencies into a local venv.
metadata: 
  scripts: 
    - /home/ryanm/workspace/ai/skills/resume-content-writer/scripts/generate_docx.py
    - /home/ryanm/workspace/ai/skills/resume-content-writer/scripts/setup.sh
    - /home/ryanm/workspace/ai/skills/resume-content-writer/scripts/config.py
    - /home/ryanm/workspace/ai/skills/resume-content-writer/scripts/verify_setup.py
    - /home/ryanm/workspace/ai/skills/resume-content-writer/scripts/parse_resume.py
    - /home/ryanm/workspace/ai/skills/resume-content-writer/scripts/create_templates.py
  references:
    - /home/ryanm/workspace/ai/skills/resume-content-writer/references/experience.json
---

# Resume Content Writer

Generate ATS-optimized, voice-authentic resume and cover letter content tailored to a specific job description.


### Output Directory
All generated documents (.docx files, templates) are written to a configurable output directory. 
Set the `RESUME_DIR` environment variable to override the default (`~/workspace/resume/`). 
All scripts (`setup.sh`, `generate_docx.py`, `parse_resumes.py`, `create_templates.py`) respect this variable.

## Instructions

### Step 1: Load Source Data

Read `/home/ryanm/workspace/ai/skills/resume-content-writer/references/experience.json` for all experience, skills, education, and personal info. This is the single source of truth — never fabricate beyond it.

### Step 2: Analyze the Job Description

Identify:
- Top 5 requirements by priority
- The hiring manager's biggest pain point
- Must-have vs nice-to-have keywords

### Step 3: Select Relevant Experience

Pick roles and bullets that address the top 5 requirements. Discard irrelevant bullets. Prioritize recent experience (last 10 years get full treatment).

**CRITICAL**: Only use information explicitly stated in experience.json. Do not infer industry context, specific client types, or domain details not explicitly documented. If the experience says "scheduling application", do not assume it's healthcare scheduling. If it says "data reconciliation", do not assume it's patient data without explicit confirmation.

### Step 4: Generate Content

Produce each section following these constraints:

| Section | Constraint |
|---------|-----------|
| Headline | <10 words, matches JD role title language |
| Summary | <50 words, active voice, starts with role noun |
| Skills | JD-relevant tech first, full abbreviation expansions |
| Bullets | Rephrase for impact, front-load keywords, preserve meaning/metrics |
| Cover Letter | 250-300 words: Hook → Value → Connection → Close |

### Step 5: Validate Against Source Truth

Before finalizing content, perform a fact-check using `/home/ryanm/workspace/ai/skills/resume-content-writer/references/fabrication-checklist.md`:
- Verify every specific claim (metrics, technologies, context) appears in experience.json
- Remove any domain assumptions not explicitly documented 
- Ensure no industry-specific details are added beyond what's stated
- Confirm all accomplishment bullets reference documented experience

### Step 6: Self-Score and Output

Apply scoring criteria, report gaps, and return structured JSON:

```json
{
  "targetCompany": "Acme Corp",
  "resume_content": { "headline": "...", "summary": "...", "skills": [...], "experience": [...], "education": [...] },
  "cover_letter_content": { "greeting": "...", "hook": "...", "value": "...", "connection": "...", "closing": "..." },
  "score": { "keyword_match": 0, "impact_metrics": 0, "voice_authenticity": 0, "ats_compliance": 0, "overall": 0, "gaps": [...] }
}
```

### Step 7: Generate Documents (Optional)

If the user wants .docx output, ensure dependencies are installed first (`scripts/setup.sh`), then run:
```bash
TODAY=$(date +%Y-%m-%d)
scripts/.venv/bin/python /home/ryanm/workspace/ai/skills/resume-content-writer/scripts/generate_docx.py --type resume --content content.json --date $TODAY --pdf
scripts/.venv/bin/python /home/ryanm/workspace/ai/skills/resume-content-writer/scripts/generate_docx.py --type cover_letter --content content.json --date $TODAY --pdf
```

The script reads `targetCompany` from the content JSON to build the output path (`$RESUME_DIR/YYYY-MM-DD/CompanyName/`). Pass `--company "Name"` to override, `--date YYYY-MM-DD` to control the output directory date, or `--output path/to/file.docx` for a fully custom path.

The `--pdf` flag generates a matching PDF alongside the docx (requires Windows with MS Word installed via `docx2pdf` or LibreOffice on Linux). On systems without PDF conversion tools, only .docx files are generated.

## Bullet Rewriting Rules

| Allowed | Not Allowed |
|---------|-------------|
| Rephrase for clarity | Invent metrics |
| Reorder to front-load keywords | Add technologies not in source |
| Strengthen verb choices | Inflate scope or team size |
| Add JD terminology where honest | Change "contributed to" → "led" |
| Combine text with keyword metadata | Claim undocumented skills |
| | **Invent industry context not explicitly stated** |
| | **Assume domain specificity (e.g., "scheduling" = "healthcare scheduling")** |
| | **Add work history details or use cases not documented** |

## Hard Guardrails

- NEVER fabricate metrics, technologies, team sizes, or scope
- NEVER claim skills not documented in experience.json
- NEVER invent industry context, client types, or domain specificity not explicitly stated
- NEVER assume generic terms have specific meanings (e.g., "scheduling" ≠ "healthcare scheduling")
- NEVER exceed 300 words in the cover letter
- NEVER write task-based bullets ("Responsible for...")
- NEVER copy JD text verbatim into bullets (ATS detects this)
- NEVER use buzzwords: "team player", "hardworking", "synergy", "passionate"
- ALWAYS preserve original meaning when rewriting bullets
- ALWAYS include months on all dates (MM/YYYY format)
- ALWAYS report the score with breakdown in the output

## Reference Files

For detailed guidance, load these as needed:

- `/home/ryanm/workspace/ai/skills/resume-content-writer/references/guardrails.md` — Hard constraints, truthfulness rules, content red flags
- `/home/ryanm/workspace/ai/skills/resume-content-writer/references/fabrication-checklist.md` — Validation checklist to prevent common fabrications
- `/home/ryanm/workspace/ai/skills/resume-content-writer/references/voice.md` — Voice, tone, personality, anti-patterns, and examples
- `/home/ryanm/workspace/ai/skills/resume-content-writer/references/ats-optimization.md` — ATS keyword strategy, formatting rules, quantification targets
- `/home/ryanm/workspace/ai/skills/resume-content-writer/references/resume-format.md` — Section order, formatting templates, timeline structure
- `/home/ryanm/workspace/ai/skills/resume-content-writer/references/cover-letter.md` — Cover letter structure, tone, and examples
- `/home/ryanm/workspace/ai/skills/resume-content-writer/references/output-conventions.md` — File naming, directory structure, JSON schemas
- `/home/ryanm/workspace/ai/skills/resume-content-writer/references/experience.json` — Source of truth for all experience data

## Scripts

- `/home/ryanm/workspace/ai/skills/resume-content-writer/scripts/generate_docx.py` — Generate ATS-optimized .docx from content JSON
- `/home/ryanm/workspace/ai/skills/resume-content-writer/scripts/create_templates.py` — Generate template .docx files with named styles
- `/home/ryanm/workspace/ai/skills/resume-content-writer/scripts/parse_resumes.py` — Extract structured data from existing .docx resumes
- `/home/ryanm/workspace/ai/skills/resume-content-writer/scripts/setup.sh` — Install Python deps and generate templates

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
