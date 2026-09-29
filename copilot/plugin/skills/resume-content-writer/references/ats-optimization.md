# ATS Optimization (2026 Playbook)

How modern Applicant Tracking Systems score resumes and how to optimize for them.

## What ATS Actually Checks

1. **Keyword presence** — exact matches against JD terms
2. **Keyword context** — are they in accomplishment sentences or just listed?
3. **Date continuity** — gaps flagged, missing months flagged
4. **Section structure** — can it find Summary, Experience, Skills, Education?
5. **Recency** — more weight to recent roles

## Formatting Rules (Immediate Rejection Risks)

| Rule | Reason |
|------|--------|
| Single-column layout ONLY | Parsers scramble multi-column, tables, and text boxes |
| No headers/footers for contact info | Many parsers skip document headers entirely |
| Standard fonts ONLY: Calibri, Arial, Garamond, Lato | Custom fonts may produce unreadable characters |
| Font size NEVER below 10pt | Must be readable for humans in later stages |
| Pipe `\|` or tabs as inline dividers | No slashes, dashes, or custom separators |
| Save as both .docx AND .pdf | PDF preserves layout; docx ensures parseability |
| Include months on ALL dates (MM/YYYY) | ATS flags missing dates as suspicious |
| 0.5 inch (1.27cm) margins | Maximize body content space without headers/footers |
| No graphics, images, or design tools | Use only Word body text |

## Keyword Strategy

1. **Use exact JD terminology** — if JD says "AWS", write "AWS" not "Cloud Infrastructure"
2. **Include full expansions AND abbreviations** — "Amazon Web Services (AWS)" captures both variants
3. **Natural integration** — weave keywords into accomplishment bullets, not just Skills
4. **Category grouping** — "Data Analysis: Python | SQL | Tableau" scores higher than a random list
5. **Don't keyword-stuff** — AI detects unnatural density and flags as spam
6. **Frequency matters** — important skills should appear in Skills AND Work Experience (2-3x naturally)
7. **Placement matters** — ATS estimates experience duration by which role a skill appears under
8. **Imitate JD language** — use exact phrasing where it honestly applies
9. **Full abbreviation expansions** — "Amazon Web Services" not just "AWS"

## Keyword Optimization Process

For each job application:

1. Analyze JD for must-have and good-to-have skills
2. Ensure must-have keywords appear in BOTH Skills and at least one Work Experience bullet
3. Map good-to-have keywords into relevant bullets where truthful
4. Optimize frequency: critical skills appear 2-3 times naturally
5. Never add keywords that don't reflect documented experience

## Quantification Priority

AI screeners using NLP actively prioritize resumes containing:

- Dollar values ($120k savings, $2M revenue)
- Percentages (40% improvement, 99.9% uptime)
- Volumes (5TB database, 10M daily requests, 40+ tickets/day)
- Time (reduced from 2 hours to 15 minutes)

"Resolved 40+ tickets/day with 98% satisfaction" will always outrank "Handled customer support tickets."

**Target:** 70%+ of bullets should contain quantified metrics.

## Impact-Driven Bullets (X-Y-Z Formula)

Every bullet should follow: **Accomplished [X] as measured by [Y], by doing [Z]**

**Weak:** "Migrated the database to the cloud."

**Strong:** "Architected the zero-downtime migration of a 5TB legacy relational database to AWS Aurora, improving read-query performance by 40% and saving $120k annually in on-premise hosting costs."
