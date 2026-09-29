# Output Conventions

File naming, directory structure, and output format rules.

## Output Directory

Configured via the `RESUME_DIR` environment variable (default: `~/workspace/resume`).

## Directory Structure

```
{RESUME_DIR}/YYYY-MM-DD/{CompanyName}/
├── Resume_{CompanyName}.docx
├── Resume_{CompanyName}.pdf
├── Cover_Letter_{CompanyName}.docx
├── Cover_Letter_{CompanyName}.pdf
├── resume_content_{companyname}.json
└── cover_letter_content_{companyname}.json
```

## Naming Rules

| Element | Convention | Example |
|---------|-----------|---------|
| CompanyName (folder & filenames) | PascalCase, no spaces | "BlueOrigin", "YesEnergy", "OrthoFi" |
| companyname (JSON files) | lowercase, no spaces | "blueorigin", "frontera" |
| Date folder | ISO format from generation date | "2026-08-24" |

## Required Outputs

Always produce all 6 files:
- Resume .docx + .pdf
- Cover letter .docx + .pdf
- Content JSON for both (kept for reproducibility and re-generation)

## Content JSON Format

### resume_content_{companyname}.json

```json
{
  "targetCompany": "Acme Corp",
  "personalInfo": { "name": "...", "email": "...", "phone": "...", "location": "...", "linkedin": "...", "github": "..." },
  "headline": "<10 words matching JD role language",
  "summary": "<50 words, active voice, starts with role noun",
  "skills": [
    { "name": "Category", "skills": ["Skill1", "Skill2"] }
  ],
  "experience": [
    {
      "company": "...", "location": "...", "title": "...",
      "startDate": "MM/YYYY", "endDate": "MM/YYYY or Present",
      "bullets": ["Accomplishment: Action resulting in outcome"]
    }
  ],
  "education": [{ "institution": "...", "degree": "...", "field": "...", "graduationDate": "..." }],
  "projects": [{ "name": "...", "description": "...", "url": "..." }],
  "certifications": [{ "name": "...", "issuer": "...", "date": "..." }]
}
```

### cover_letter_content_{companyname}.json

```json
{
  "targetCompany": "Acme Corp",
  "personalInfo": { "name": "...", "email": "...", "phone": "...", "location": "..." },
  "date": "Month DD, YYYY",
  "greeting": "Dear ... Hiring Manager,",
  "hook": "Why them + why you (2-3 sentences)",
  "value": "Best relevant accomplishment (3-4 sentences)",
  "connection": "How you fit their challenges (2-3 sentences)",
  "closing": "Call to action (1-2 sentences)"
}
```

## Score Output

Always include alongside content:

```json
{
  "score": {
    "keyword_match": 0-10,
    "impact_metrics": 0-10,
    "voice_authenticity": 0-10,
    "ats_compliance": 0-10,
    "overall": 0-10,
    "gaps": ["skill or requirement not covered"],
    "improvements": ["suggested enhancement"]
  }
}
```
