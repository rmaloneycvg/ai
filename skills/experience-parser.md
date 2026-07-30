---
name: experience-parser
description: Use when extracting structured experience data from existing resume .docx files into experience.json. Reads all resume documents, deduplicates entries across tailored versions, and produces a validated JSON file following the experience schema. Run once to bootstrap, periodically to add new roles.
---

# Experience Parser

## Role & Tone

Act as a meticulous data extraction specialist. Be precise about what was found in the source documents vs. what might be inferred. Always present findings for user review before committing. Flag any ambiguities (e.g., unclear dates, vague bullets without metrics).

## Environment Scope

**write+execute** — Runs `parse_resumes.py` to extract text from .docx files, then writes structured data to `experience.json`. Only modifies `experience.json` and files under `scripts/`.

## Workflow

1. **Check Existing State** — Read `~/workspace/ai/config/resume/experience.json`. If it already contains populated data, ask user whether to merge new findings or overwrite. If entries already exist for the same company + role + date range being parsed, report "already parsed" for those entries and skip them unless user requests re-extraction.
2. **Install Dependencies** — Ensure `python-docx` is installed: `uv add python-docx`
3. **Run Parser** — Execute `python3 ~/workspace/ai/scripts/resume/parse_resumes.py` to extract raw text from all resume .docx files (skips cover letters and PDFs).
4. **Structure Data** — Organize extracted text into the schema format:
   - Identify sections by heading styles or text patterns (SUMMARY, EXPERIENCE, SKILLS, EDUCATION)
   - Parse experience entries: company name, job title, date range, bullet points
   - Extract skills and group by category
   - Separate 2016+ roles (full treatment) from pre-2016 roles (condensed)
5. **Deduplicate** — Same company + same title = one entry. Merge unique bullets from different tailored versions.
6. **Enrich Bullets** — For each bullet:
   - Extract quantified metrics to the `metrics` field
   - Identify technology/method keywords
   - Assign a category (architecture, scale, leadership, business-impact, force-multiplier, technical-execution)
7. **Present for Review** — Show the user:
   - Total roles found and deduplicated count
   - Skills extracted (grouped)
   - Any entries with missing dates or vague bullets (flagged for attention)
   - Full structured output for approval
8. **Save** — Write validated data to `~/workspace/ai/config/resume/experience.json`

### Failure Recovery (max 3 retries)

- If .docx parsing fails: check file permissions, try alternative extraction method
- If schema validation fails: identify which fields are malformed, fix and re-validate
- If deduplication is ambiguous: ask user to clarify (same company, different divisions?)

### Rollback

If user rejects the extracted data: do not write to experience.json. Offer to re-run with specific files excluded or to manually adjust individual entries.

## Guardrails

- NEVER fabricate experience entries — extract only what's explicitly written in the documents
- NEVER merge entries from genuinely different roles at the same company (e.g., promoted from Engineer to Senior)
- NEVER write to experience.json without user approval
- NEVER include cover letter content as experience data
- NEVER modify the original .docx resume files
- NEVER include skills or technologies not explicitly mentioned in at least one resume

## References

- `~/workspace/ai/config/resume/experience.schema.json` — defines the target data structure
- `~/workspace/ai/scripts/resume/parse_resumes.py` — extraction script
