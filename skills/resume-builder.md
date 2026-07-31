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

2. **Read `~/workspace/ai/config/resume/experience.json`**
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

### Phase 4: Generate Content (Delegated to Sub-Agent)

7. **Delegate to resume-content-writer** — Invoke the `resume-content-writer` sub-agent with model override `claude-opus-4` for higher reasoning capacity. Pass:
   - Parsed JD (company, role, required skills, responsibilities, seniority signals)
   - Full experience.json content
   - Any user clarifications from Phase 3
   - Specific instructions (e.g., "emphasize integration platform ownership")

8. **Receive from sub-agent:**
   - `resume_content` — full content JSON matching generate_docx.py format
   - `cover_letter_content` — full cover letter JSON
   - `score` — self-assessment with breakdown and keyword gaps

   If the subagent tool is unavailable, perform content generation directly (single-agent fallback).

### Phase 5: Review and Validate

9. **Truthfulness review** — Cross-check the sub-agent's output against experience.json:
    - Every skill claimed must exist in the skills section
    - Every metric must be documented in a bullet's `metrics` field
    - No scope inflation (team sizes, dollar amounts, percentages)
    - If a violation is found, correct it before proceeding

10. **Cover letter review** — Verify:
    - ≤ 300 words
    - References something specific about the company
    - Doesn't rehash resume bullets verbatim
    - Tone is conversational, not formulaic

### Phase 6: Score and Gate

11. **Use the sub-agent's score** (or self-score if running single-agent):
    - Keyword Match (0-30): count exact JD terms in resume
    - Quantification Density (0-20): % of bullets with metrics
    - Relevance Alignment (0-30): top bullets match JD priorities
    - ATS Compliance (0-10): standard headers, fonts, formatting
    - Recency Weighting (0-10): recent roles weighted appropriately

12. **If score >= 75:** proceed to generation
13. **If score < 75:** present score breakdown + 3 improvement suggestions. Ask user if they want to iterate or proceed as-is. If iterating, re-invoke sub-agent with specific feedback.

### Phase 7: Generate Documents

16. **Resolve output directory:**
    Read `paths.resumeDir` from `~/workspace/ai/config/resume/experience.json` (default: `~/workspace/resume`). Expand `~` to the user's home directory. Use this as `RESUME_DIR`.

17. **Create output directory:**
    ```bash
    mkdir -p $RESUME_DIR/$(date +%Y-%m-%d)
    ```

18. **Write content JSON files** to the output directory:
    - `$RESUME_DIR/YYYY-MM-DD/resume_content_{company}.json` — resume content matching generate_docx.py format
    - `$RESUME_DIR/YYYY-MM-DD/cover_letter_content_{company}.json` — cover letter content

19. **Generate docx files:**
    ```bash
    python3 ~/workspace/ai/scripts/resume/generate_docx.py \
      --type resume \
      --content $RESUME_DIR/YYYY-MM-DD/resume_content_{company}.json \
      --output $RESUME_DIR/YYYY-MM-DD/Resume_{Company}.docx

    python3 ~/workspace/ai/scripts/resume/generate_docx.py \
      --type cover_letter \
      --content $RESUME_DIR/YYYY-MM-DD/cover_letter_content_{company}.json \
      --output $RESUME_DIR/YYYY-MM-DD/Cover_Letter_{Company}.docx
    ```

20. **Convert to PDF (WSL → PowerShell → docx2pdf):**
    Environment requires: `$WIN_TEMP` set in shell profile, Windows Python with `docx2pdf`, Microsoft Word installed.

    First kill any lingering Word process:
    ```bash
    powershell.exe -Command "Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2"
    ```

    For EACH docx file, convert using `wslpath -w` to get the Windows-accessible path:
    ```bash
    WIN_SRC=$(wslpath -w "$RESUME_DIR/YYYY-MM-DD/Resume_{Company}.docx")
    powershell.exe -Command "python -c \"from docx2pdf import convert; convert(r'${WIN_SRC}')\""
    ```

    This produces a `.pdf` alongside the `.docx` in the same directory. Repeat for the cover letter.

    If direct path conversion fails (Word cannot open `\\wsl.localhost` paths), use the temp-copy fallback:
    ```bash
    WIN_SRC=$(wslpath -w "<linux_path>.docx")
    TEMP_DOCX="${WIN_TEMP}\\<filename>.docx"
    TEMP_PDF="${WIN_TEMP}\\<filename>.pdf"
    powershell.exe -Command "
      Copy-Item '${WIN_SRC}' -Destination '${TEMP_DOCX}' -Force
      python -c \"from docx2pdf import convert; convert(r'${TEMP_DOCX}', r'${TEMP_PDF}')\"
    "
    cp "$(wslpath "${TEMP_PDF}")" "<linux_output_path>.pdf"
    powershell.exe -Command "Remove-Item '${WIN_TEMP}\\<filename>.*' -Force -ErrorAction SilentlyContinue"
    ```

    Expected output files:
    ```
    $RESUME_DIR/YYYY-MM-DD/
    ├── Resume_{Company}.docx
    ├── Resume_{Company}.pdf
    ├── Cover_Letter_{Company}.docx
    └── Cover_Letter_{Company}.pdf
    ├── resume_content_{company}.json      (intermediate, kept for reproducibility)
    └── cover_letter_content_{company}.json (intermediate, kept for reproducibility)
    ```

21. **Report results:** Show file paths, estimated page count, word count (cover letter), job fit score, and any keyword gaps.

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

- `~/workspace/ai/config/resume/experience.json` — single source of truth for all claims
- `~/workspace/ai/config/resume/experience.schema.json` — schema definition
- `steering/preferences/resume/guardrails.md` — full guardrail details
- `~/workspace/ai/scripts/resume/generate_docx.py` — docx generation script
- `~/workspace/ai/scripts/resume/generate_docx.py --help` — platform-specific PDF conversion instructions
- `skills/resume-job-scorer.md` — scoring criteria details
