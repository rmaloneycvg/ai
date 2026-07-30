# Resume & Cover Letter Guardrails

## Why This Exists

This document consolidates all hard constraints, best practices, and optimization rules for generating tailored resumes and cover letters. The resume-builder agent loads this as context and follows it prescriptively. Breaking these rules risks ATS rejection, ageism bias triggers, or misrepresenting experience.

---

## Resume Guardrails (Hard Constraints)

### Formatting Red Flags (Immediate ATS Rejections)

| Rule | Reason |
|------|--------|
| Single-column layout ONLY | ATS parsers scramble multi-column, tables, and text boxes |
| No headers/footers for contact info | Many parsers skip document headers entirely — write all content in the body |
| No Photoshop, graphic design tools, or online resume builders | Use only Word/Google Docs body text |
| Standard section titles ONLY (see Section Order below) | Creative names break ATS parsing |
| Standard fonts ONLY: Calibri, Arial, Garamond, Lato | New/custom fonts may convert letters into unreadable special characters |
| Font size NEVER below 10pt | Must be readable for humans in later hiring stages |
| Use pipe `\|` or tabs as dividers between inline info | No slashes, dashes, or custom separators |
| Save as both .docx AND .pdf | PDF preserves layout (generated via MS Word docx2pdf); docx ensures parseability |
| Include months on ALL dates (MM/YYYY format) | ATS flags missing dates as suspicious; uses placement to estimate experience duration |
| Reduce margins instead of using headers/footers | 0.5 inch (1.27cm) margins to maximize body content space |

### Section Order (Mandatory)

Generate sections in this exact order:

1. **Name** — Largest text, top of page, centered
2. **Professional Summary** — Use a HEADLINE as the section title (not "Professional Summary"). Under 10 words. E.g. "Sr. Full-Stack Software Engineer with 15+ Years Building Scalable Systems"
3. **Contact Information** — Name, phone, location (City, State), email (personal Gmail, never work), LinkedIn URL, GitHub URL. Pipe-separated.
4. **Skills** — Format: `[Category]: [skill | skill | skill]`. Categories: Languages, Frameworks, Databases, Cloud & DevOps, etc.
5. **Work Experience** — Reverse chronological. Format: `[Company], [Location] | [Job Title] | [MM/YYYY – MM/YYYY]`
6. **Education** — (Move before Work Experience only if still in school or <3 years experience)
7. **Projects** — Optional
8. **Certifications / Awards** — Optional

### Resume Headline (Summary Section Title)

Instead of writing "Professional Summary" as the section title, use a headline with fewer than 10 words. Examples:
- "Software Engineer (Full Stack)"
- "Senior Front End Engineer"
- "Software Engineering Lead"

The summary body below the headline must be <50 words, active voice, action words, starting with the noun describing the job role.

### Work Experience Formatting

Each role MUST follow this exact structure:
```
[Company], [Location] | [Job Title] | [MM/YYYY – MM/YYYY]
```

Example: `Facebook, Singapore | Front End Engineering Lead | 08/2018 – Present`

Bullets follow: `[Accomplishment summary]: [Action] that resulted in [quantifiable outcome]`

### Content Red Flags (AI Score Penalties)

| Rule | Reason |
|------|--------|
| Never copy-paste JD text verbatim | Modern AI detects this and flags as spam |
| Never use buzzwords ("team player", "hardworking", "synergy") | Takes space, adds zero score weight |
| Never list duties instead of results | "Responsible for..." tells AI what you were supposed to do, not what you achieved |
| Never hide or omit dates | AI views missing dates as intentional omission |

### Structural Constraints

| Rule | Reason |
|------|--------|
| **Maximum 2 pages** | Recruiters spend 6-10 seconds on initial scan. Page 3+ won't be read |
| **No obsolete technology** | Unless JD specifically asks. Listing outdated tech brands you as a legacy developer |
| **No chronological biography** | Don't give equal weight to junior 2005 roles and senior 2023 roles |
| **No "Objective" statement** | Outdated. Companies care about what you do for them, not what you want |
| **No task-based bullets** | "Responsible for writing APIs" is a job description, not an accomplishment |

---

## Resume Best Practices

### The 10-Year Rule (Timeline Structure)

| Era | Treatment |
|-----|-----------|
| **2016–Present** | Full treatment: 4-6 bullets per role. Focus on architecture, scale, leadership, business impact |
| **2006–2015** | Condensed: company, title, dates + 1-2 bullets for major wins. OR group under "Previous Engineering Experience" |
| **Pre-2006** | Omit or single line if highly relevant to target role |

### Years of Experience (Match the JD)

In the executive summary, only state the number of years the JD asks for with a "+" after it. Never advertise more years than required. If the JD says "6+ years", write "6+ years" in the summary, not "20+ years". The goal is to match their requirement, not signal overqualification. The full work history is visible in the experience section for anyone who wants to count.

**Floor: 12 years minimum.** If the JD asks for fewer than 12 years, use "12+" instead. Never go below 12+ regardless of what the JD requests.

### Executive Summary (Replaces Objective)

3-4 sentences that establish identity and set the narrative:

**Structure:**
1. Title/seniority + years of relevant experience + primary domain
2. Specialization + quantified top accomplishment
3. Secondary strength (leadership, mentoring, architecture)
4. What you bring to the target role specifically

**Bad:** "Hardworking software engineer looking for a new opportunity."

**Good:** "Staff Backend Engineer with 20+ years of experience architecting high-throughput distributed systems. Specializes in migrating legacy monolithic applications to microservices (AWS, Go, Node.js), reducing infrastructure costs by up to 30%. Proven track record of mentoring engineering teams and bridging the gap between product requirements and technical execution."

### Skills Section (Grouped with Category Labels)

Structure: `[Skill category]: [List skills separated by |]`

```
Languages: Python | Node.js | TypeScript | C# | JavaScript | SQL | HTML/CSS
Frameworks & Libraries: .NET | React | Angular | Vue.js | GraphQL | Apollo | Express.js
Cloud & DevOps: Amazon Web Services (AWS) | Microsoft Azure | Google Cloud Platform (GCP) | Docker | Terraform | GitHub Actions
Databases: SQL Server | PostgreSQL | Firebase | MySQL | Redis | MongoDB
Observability & Testing: Grafana | Prometheus | Jaeger | OpenTelemetry | Playwright | Jest | pytest
```

- Only include technologies used in the last 7-10 years
- Use exact terminology from JD where it matches real experience
- Order within each category by relevance to target role
- Include full expansions of common abbreviations: Amazon Web Services (AWS), Google Cloud Platform (GCP), Microsoft Azure
- ATS assigns experience duration based on keyword placement relative to job dates — put critical skills in recent role bullets too

### Impact-Driven Bullets (X-Y-Z Formula)

Every bullet should follow: **Accomplished [X] as measured by [Y], by doing [Z]**

**Weak:** "Migrated the database to the cloud."

**Strong:** "Architected the zero-downtime migration of a 5TB legacy relational database to AWS Aurora, improving read-query performance by 40% and saving $120k annually in on-premise hosting costs."

**Target:** 70%+ of bullets should contain quantified metrics (dollar values, percentages, volumes, time durations).

### Force Multiplier Work

Senior engineers don't just write code — they make developers around them better. Highlight:
- CI/CD pipeline improvements that cut deployment times
- Mentoring junior/mid engineers
- Leading RFCs for system design
- Introducing testing practices that reduced bugs
- Documentation or developer experience improvements

---

## ATS Optimization (2026 Playbook)

### Keyword Strategy

1. **Use exact terminology from JD** — if JD says "AWS", write "AWS" not "Cloud Infrastructure"
2. **Include full expansions AND abbreviations** — "Amazon Web Services (AWS)" captures both keyword variants
3. **Natural integration** — weave keywords into accomplishment bullets, not just the skills section
4. **Category grouping** — "Data Analysis: Python | SQL | Tableau" scores higher than a random comma list
5. **Don't keyword-stuff** — AI detects unnatural density and flags as spam
6. **Frequency matters** — Some ATS score skill strength by keyword frequency. Important skills should appear in Skills AND Work Experience sections
7. **Placement matters** — ATS estimates experience duration for a skill based on which role it appears under. A skill in a 3-year role = 3 years of assumed experience
8. **Imitate JD language closely** — Use the exact phrasing from the job description where it honestly applies
9. **Include the full version of abbreviations** — "Amazon Web Services" not just "AWS", "Google Cloud Platform" not just "GCP"

### Keyword Optimization Process

For each job application:
1. Analyze the JD for must-have and good-to-have skills
2. Ensure must-have keywords appear in BOTH the Skills section and at least one Work Experience bullet
3. Map good-to-have keywords into relevant experience bullets where truthful
4. Optimize frequency: critical skills should appear 2-3 times naturally across the document
5. Never add keywords that don't reflect real, documented experience

### Quantification Priority

AI screeners using NLP actively prioritize resumes containing:
- Dollar values ($120k savings, $2M revenue)
- Percentages (40% improvement, 99.9% uptime)
- Volumes (5TB database, 10M daily requests, 40+ tickets/day)
- Time (reduced from 2 hours to 15 minutes)

"Resolved 40+ tickets/day with 98% satisfaction" will always outrank "Handled customer support tickets."

### What ATS Actually Checks

1. Keyword presence (exact matches against JD)
2. Keyword context (are they in accomplishment sentences or just listed?)
3. Date continuity (gaps flagged, missing months flagged)
4. Section structure (can it find Summary, Experience, Skills, Education?)
5. Recency (more weight to recent roles)

---

## Cover Letter Guardrails (Hard Constraints)

| Rule | Reason |
|------|--------|
| **Do NOT regurgitate resume** | Resume shows WHAT; cover letter explains WHY and HOW your approach aligns |
| **Do NOT use "To Whom It May Concern"** | Use "Dear [Department] Hiring Manager" or find the actual name |
| **Do NOT mention employment gaps** | Start directly with value proposition |
| **Do NOT exceed 250-300 words** | Half a page max. Executive communication is brief |
| **Do NOT focus on what the job does for you** | "Great next step in my career" is irrelevant to employer |
| **Do NOT sound AI-generated** | Write conversationally, like a confident professional to a peer |

## Cover Letter Best Practices

### Structure (4 Paragraphs)

**1. Hook (2-3 sentences) — "Why Them + Why You"**

Identify the role + immediately connect your expertise to their company's mission or challenges. Reference their engineering blog, recent news, or product.

> "When I saw that [Company] is scaling its payment processing infrastructure to handle global markets, I knew I had to apply for the Staff Engineer role. Having spent the last seven years architecting distributed, high-availability microservices in the fintech space, I specialize in exactly the type of bottleneck resolution your team is currently tackling."

**2. Value (3-4 sentences) — Your Best Relevant Accomplishment**

Go deeper on ONE accomplishment that directly addresses their biggest need. Don't repeat the resume bullet — explain the context, your approach, and why it worked.

**3. Connection (2-3 sentences) — How You Fit Their Challenges**

Show you understand their specific problems. Connect your working style or philosophy to what they need right now.

**4. Close (1-2 sentences) — Call to Action**

Brief, confident. Express enthusiasm for discussing specifics.

### Tone

- Conversational and confident — not formal/stiff, not casual/sloppy
- Like a senior engineer writing to an engineering leader they respect
- Show personality without being unprofessional
- Avoid clichés, filler, and corporate-speak
- Vary sentence length — mix short punchy sentences with longer explanatory ones

---

## Truthfulness Constraint (NON-NEGOTIABLE)

| Rule | Detail |
|------|--------|
| Source of truth | `experience.json` is the ONLY source for claims |
| Skills | If it's not in experience.json skills section, don't claim it |
| Accomplishments | If it's not documented as a bullet, don't invent it |
| Metrics | Use only metrics explicitly recorded. Never round up or extrapolate |
| Scope | Don't upgrade "contributed to" → "led" or "team of 3" → "team of 10" |
| Rephrasing | Allowed — rewording for impact without changing meaning is fine |
| Fabrication | NEVER allowed under any circumstances |

---

## Voice & Personality

All resume and cover letter content should sound like Ryan — not about Ryan. The documents are written in his voice.

**Who Ryan is:**
- An empathetic listener who genuinely cares about the people using what he builds
- Committed and tenacious about hard problems. Doesn't shy away from complexity, jumps in with both feet and figures things out
- Team-first — celebrates shared wins, loves mentoring, thrives in collaboration
- Direct and warm, never corporate or detached
- Finds real joy in making the developers around him more productive

**Resume bullet voice:**
- Compressed stories Ryan would tell enthusiastically in conversation
- Emphasize human impact — who benefited, what was unblocked, what the team accomplished together
- Confident without boasting — the work speaks, framed with genuine energy
- Active, vivid verbs: "built", "solved", "untangled", "connected" — not "leveraged", "facilitated", "spearheaded"

**Cover letter voice:**
- Sounds like Ryan writing to someone he'd enjoy working with
- Show genuine curiosity about the company's challenges and mission
- Express real excitement — "What drew me to this role..." not "I am writing to express my interest..."
- Warmth and personality in sentence rhythm — short punchy mixed with longer explanatory
- Empathy for end users (patients, families, customers) — Ryan cares about who benefits

**Anti-patterns (NEVER):**
- ❌ "Leveraged synergies to drive stakeholder alignment"
- ❌ "Results-driven professional with a passion for excellence"
- ❌ "I am writing to express my interest in the position"
- ❌ "Spearheaded a cross-functional initiative to optimize workflows"
- ❌ Em-dashes (—) or double-hyphens (--) mid-sentence. Use commas, "and", or split into two sentences.
- ❌ Semicolons (;) as sentence joiners. Rewrite as two sentences or use a comma.

**Examples (YES):**
- ✅ "Built the integration layer that finally let our healthcare teams stop manually reconciling data between three systems"
- ✅ "What drew me to this role is the chance to solve the same kind of messy, real-world data problems I've spent the last four years untangling"
- ✅ "The best part of that project was watching three junior engineers ship their first production integration using the library I'd built for exactly that purpose"

### Handling Skill Gaps

When the JD requires something not in experience.json:
- Note it internally as a gap
- Do NOT claim the skill on the resume
- In the cover letter, you may express interest in learning if relevant
- Report gaps to the user in the scoring output

---

## File Naming Convention

Output directory is configured via `paths.resumeDir` in `config/resume/experience.json` (default: `~/workspace/resume`).

```
{resumeDir}/YYYY-MM-DD/
├── Resume_{CompanyName}.docx
├── Resume_{CompanyName}.pdf
├── Cover_Letter_{CompanyName}.docx
├── Cover_Letter_{CompanyName}.pdf
├── resume_content_{companyname}.json       (intermediate content, kept for reproducibility)
└── cover_letter_content_{companyname}.json  (intermediate content, kept for reproducibility)
```

- CompanyName: PascalCase, no spaces (e.g., "BlueOrigin", "YesEnergy", "OrthoFi") — used in human-facing filenames
- companyname: lowercase (e.g., "blueorigin", "frontera") — used in content JSON filenames
- Date: ISO format from generation date
- Always produce all 4 document files (docx + pdf for both resume and cover letter)
- Keep content JSON files alongside outputs for traceability and re-generation
