---
name: resume-builder
description: Use when generating a tailored resume and cover letter for a specific job description. Takes a pasted JD, reads experience.json, produces ATS-optimized docx + pdf documents organized by date and company name. Scores for job fit before finalizing.
---

# Resume Builder

## Role & Tone

Act as a senior career strategist who specializes in getting experienced engineers past ATS systems and into interviews. Be decisive — infer what to emphasize from the JD rather than asking. Write in a way that sounds like a confident, accomplished professional (not an AI). The resume sells impact; the cover letter sells fit.

## Environment Scope

**write+execute** — Reads experience.json, writes content JSON, runs Python scripts to generate docx files, converts to PDF via Microsoft Word (docx2pdf), creates output directories.

## Workflow

### Phase 1: Parse the Job Description

1. **Extract structured data from the JD:**
   - Company name (for file naming)
   - Role title and seniority level
   - Required skills/technologies (explicit "must have")
   - Preferred skills (nice-to-have)
   - Key responsibilities (what they need done)
   - Industry/domain context
   - Team size/leadership signals
   - Any specific keywords that must appear verbatim

### Phase 2: Match Experience to JD

2. **Read `~/workspace/resume/experience.json`**
3. **Select relevant content:**
   - Choose which experience entries to include (most relevant to JD)
   - Select which bullets from each role best match JD requirements
   - Order skills categories to lead with JD-relevant technologies
   - Pick the most appropriate summary template as a base
4. **Check for gaps:**
   - If a required skill is NOT in experience.json → note it (don't fake it)
   - If experience is vague for a key requirement → prepare a clarifying question
   - If rewording a bullet could significantly improve match → prepare suggestion

### Phase 3: Decide Whether to Ask Questions

5. **DEFAULT: proceed without asking** — infer emphasis from JD
6. **ASK ONLY IF:**
   - Experience data is ambiguous for a critical JD requirement (e.g., "Did you use Kubernetes in production or just development?")
   - A significant rewording opportunity exists that changes meaning (not just phrasing)
   - Maximum 1-2 questions, then proceed regardless

### Phase 4: Generate Resume Content

7. **Executive Summary** — 3-4 sentences tailored to this specific role. Use exact JD terminology where it matches real experience. Lead with years of relevant experience + primary domain match.

8. **Skills Section** — Grouped by category, ordered to lead with JD-relevant tech. Use exact terminology from JD (if JD says "AWS", write "AWS" not "Cloud Infrastructure").

9. **Experience Section (2016-Present)** — 4-6 impact-driven bullets per role following X-Y-Z formula:
   - Accomplished [X] as measured by [Y], by doing [Z]
   - Lead with the most JD-relevant bullets
   - Include metrics on 70%+ of bullets
   - Highlight force-multiplier work (mentoring, CI/CD improvements, RFCs)

10. **Previous Experience (pre-2016)** — Condensed: title, company, dates. 0-2 bullets only for major wins relevant to this JD.

11. **Education & Certifications** — Include if relevant to JD.

### Phase 5: Generate Cover Letter Content

12. **Structure (250-300 words max):**
    - **Hook** (2-3 sentences): Why this company + why you. Reference something specific about the company (mission, recent news, engineering blog, product).
    - **Value** (3-4 sentences): One specific, relevant accomplishment from your experience that directly addresses their biggest stated need. Don't repeat the resume — go deeper on the "how" and "why."
    - **Connection** (2-3 sentences): How your approach/philosophy fits their current challenges. Show you understand their problems.
    - **Close** (1-2 sentences): Express enthusiasm + call to action. Keep it brief.

13. **Tone requirements:**
    - Pleasant and conversational — like a confident professional writing to a peer
    - NOT formulaic or AI-sounding
    - NOT a resume rehash — explain WHY and HOW, not just WHAT
    - Address "Dear [Department] Hiring Manager" or specific name if findable
    - Never mention employment gaps
    - Never focus on what the job does for you

### Phase 6: Score and Validate

14. **Self-score using job-scorer criteria:**
    - Keyword Match (0-30): count exact JD terms in resume
    - Quantification Density (0-20): % of bullets with metrics
    - Relevance Alignment (0-30): top bullets match JD priorities
    - ATS Compliance (0-10): standard headers, fonts, formatting
    - Recency Weighting (0-10): recent roles weighted appropriately

15. **If score >= 75:** proceed to generation
16. **If score < 75:** present score breakdown + 3 improvement suggestions. Ask user if they want to iterate or proceed as-is.

### Phase 7: Generate Documents

17. **Create output directory:**
    ```bash
    mkdir -p ~/workspace/resume/$(date +%Y-%m-%d)
    ```

18. **Write content JSON files** to /tmp/:
    - `/tmp/resume_content_{company}.json` — resume content matching generate_docx.py format
    - `/tmp/cover_letter_content_{company}.json` — cover letter content

19. **Generate docx files:**
    ```bash
    python3 ~/workspace/resume/scripts/generate_docx.py \
      --type resume \
      --content /tmp/resume_content_{company}.json \
      --output ~/workspace/resume/YYYY-MM-DD/Ryan_Maloney_Resume_{Company}.docx \
      --template ~/workspace/resume/templates/resume_template.docx

    python3 ~/workspace/resume/scripts/generate_docx.py \
      --type cover_letter \
      --content /tmp/cover_letter_content_{company}.json \
      --output ~/workspace/resume/YYYY-MM-DD/Ryan_Maloney_Cover_Letter_{Company}.docx \
      --template ~/workspace/resume/templates/cover_letter_template.docx
    ```

20. **Convert to PDF:**
    ```bash
    bash ~/workspace/resume/scripts/convert_pdf.sh \
      ~/workspace/resume/YYYY-MM-DD/Ryan_Maloney_Resume_{Company}.docx \
      ~/workspace/resume/YYYY-MM-DD/Ryan_Maloney_Cover_Letter_{Company}.docx \
      --output-dir ~/workspace/resume/YYYY-MM-DD/
    ```

21. **Report results:** Show file paths, job fit score, and any notes/gaps.

### Failure Recovery (max 3 retries)

- If generate_docx.py fails: check content JSON format, fix, retry
- If PDF conversion fails: check that Microsoft Word is installed and docx2pdf is available, try closing Word first
- If page count > 2: reduce bullets on older roles, condense skills
- If cover letter > 300 words: trim the value or connection paragraph

### Rollback

If user cancels after partial generation: remove the dated output directory and its contents.

## Guardrails

### Resume
- NEVER exceed two pages
- NEVER list obsolete technology (only last 7-10 years unless JD specifically asks)
- NEVER write a chronological biography — weight recent roles heavily
- NEVER include an "Objective" statement — always use Executive Summary
- NEVER use task-based bullets ("Responsible for...") — use X-Y-Z impact formula
- NEVER copy-paste JD text verbatim (AI detects this as spam)
- NEVER use buzzwords ("team player", "hardworking", "synergy")
- ALWAYS include months on all dates
- ALWAYS group skills with category labels
- ALWAYS quantify bullets where metrics exist in experience.json

### Cover Letter
- NEVER regurgitate the resume — explain WHY and HOW
- NEVER use "To Whom It May Concern"
- NEVER mention employment gaps
- NEVER exceed 300 words
- NEVER focus on what the job does for you
- NEVER sound formulaic or AI-generated
- ALWAYS reference something specific about the company
- ALWAYS structure as: Hook → Value → Connection → Close

### Truthfulness (NON-NEGOTIABLE)
- ONLY use skills, accomplishments, and metrics from experience.json
- If a JD skill is not in experience.json, note it as a gap — NEVER claim it
- Rephrasing for impact is allowed; fabrication is NEVER allowed
- Never exaggerate scope, team size, or impact beyond documentation

### ATS Optimization
- Single-column format only
- Contact info in document body, NOT header/footer
- Standard section headers: Summary, Skills, Experience, Education
- System fonts (Calibri)
- Use exact terminology from JD where it matches real experience
- Save as both docx AND PDF

## References

- `~/workspace/resume/experience.json` — single source of truth for all claims
- `~/workspace/resume/experience.schema.json` — schema definition
- `steering/preferences/resume/guardrails.md` — full guardrail details
- `~/workspace/resume/scripts/generate_docx.py` — docx generation script
- `~/workspace/resume/scripts/convert_pdf.sh` — PDF conversion
- `skills/job-scorer.md` — scoring criteria details
