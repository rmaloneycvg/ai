# Resume Content Writer

An AI-powered skill for generating ATS-optimized, voice-authentic resumes and cover letters tailored to specific job descriptions.

## Features

- **ATS-Optimized Content**: Generates content that passes applicant tracking systems
- **Voice-Authentic Writing**: Maintains Ryan Maloney's authentic professional voice
- **Job-Specific Tailoring**: Analyzes job descriptions and selects relevant experience  
- **Multi-Format Output**: Produces both DOCX and PDF versions
- **Dynamic Date Handling**: Automatically uses current date for folders and cover letters
- **Multi-Platform PDF Generation**: Supports Windows docx2pdf and WSL + PowerShell fallbacks

## Quick Start

### Using the Agent
```bash
kiro chat resume-builder
# Then paste a job description or provide a URL
```

### Manual Generation
```bash
cd ~/workspace/ai/skills/resume-content-writer
scripts/.venv/bin/python scripts/generate_docx.py --type resume --content path/to/content.json --date $(date +%Y-%m-%d) --pdf
```

## Setup & Installation

### 1. Install Dependencies
```bash
cd ~/workspace/ai/skills/resume-content-writer
./scripts/setup.sh
```

### 2. Verify Setup
```bash
scripts/.venv/bin/python scripts/verify_setup.py
```

### 3. PDF Generation Requirements

**Windows:**
- Microsoft Word installed
- `pip install docx2pdf` in the virtual environment

**WSL:**
- Windows Microsoft Word accessible from WSL
- PowerShell.exe available (`powershell.exe -Command "Write-Host 'test'"`)
- wslpath available (`wslpath -w /tmp`)

**Linux/macOS:**
- DOCX generation only (no PDF without additional setup)
- Consider LibreOffice headless mode for PDF generation

## File Structure

```
resume-content-writer/
├── SKILL.md                    # Main skill instructions
├── README.md                   # This file
├── CHANGELOG.md                # Version history and updates
├── scripts/
│   ├── setup.sh               # Dependency installation
│   ├── generate_docx.py       # Document generation script
│   ├── verify_setup.py        # Setup verification
│   └── .venv/                 # Python virtual environment
├── references/
│   ├── experience.json        # Source of truth for all experience data
│   ├── voice.md               # Voice and tone guidelines
│   ├── guardrails.md          # Hard constraints and rules
│   ├── ats-optimization.md    # ATS keyword strategy
│   ├── resume-format.md       # Section structure and formatting
│   ├── cover-letter.md        # Cover letter structure
│   └── output-conventions.md  # File naming and directory structure
└── templates/                 # Generated DOCX templates
```

## Output Structure

Documents are generated in `~/workspace/resume/YYYY-MM-DD/CompanyName/`:

```
~/workspace/resume/2026-09-29/Alchemer/
├── Resume_Alchemer.docx
├── Resume_Alchemer.pdf  
├── Cover_Letter_Alchemer.docx
├── Cover_Letter_Alchemer.pdf
└── [content JSON files]
```

## Configuration

### Environment Variables
- `RESUME_DIR`: Override default output directory (default: `~/workspace/resume`)

### Agent Configuration
The `resume-builder` agent in `~/workspace/ai/agents/resume-builder.json` provides:
- Model: claude-sonnet-4
- Permissions for shell commands, file I/O, and web fetching
- Integration with the resume-content-writer skill

## Content Guidelines

### Resume
- **Headline**: <10 words, matches job description language
- **Summary**: <50 words, active voice, role-focused
- **Experience**: Impact-driven bullets with quantified metrics
- **Skills**: Job-relevant technologies first, full abbreviation expansions
- **Length**: 1 page target, 2 pages max for 10+ years experience

### Cover Letter  
- **Length**: 250-300 words maximum
- **Structure**: Hook → Value → Connection → Close
- **Tone**: Conversational professional, authentic voice
- **Focus**: Why them + why you, not a prose resume

## Advanced Usage

### Custom Content Generation
```python
from pathlib import Path
import json

# Load and customize content
content = {
    "targetCompany": "Acme Corp",
    "personalInfo": {...},
    "headline": "...",
    # ... other content
}

# Generate documents
subprocess.run([
    "scripts/.venv/bin/python", "scripts/generate_docx.py",
    "--type", "resume", 
    "--content", "content.json",
    "--date", "2026-09-29",
    "--pdf"
])
```

### Batch Generation
```bash
# Generate for multiple companies
for company in Acme TechCorp StartupXYZ; do
    # Customize content for each company
    scripts/.venv/bin/python scripts/generate_docx.py \
        --type resume \
        --content "${company}_content.json" \
        --date $(date +%Y-%m-%d) \
        --pdf
done
```

## Troubleshooting

### PDF Generation Issues

**docx2pdf fails on WSL:**
- Ensure Windows Word is installed and accessible
- Script automatically falls back to PowerShell + Word COM interface

**PowerShell errors:**
- Verify `powershell.exe` is in PATH from WSL
- Check Windows Word installation and COM interface availability

**Path conversion errors:**
- Ensure `wslpath` is available and working
- Test with: `wslpath -w /home/user/test`

### Content Issues

**Missing experience data:**
- Verify `references/experience.json` exists and has required sections
- Run `scripts/verify_setup.py` for validation

**ATS optimization concerns:**
- Review `references/ats-optimization.md` for current best practices
- Ensure job description keywords are naturally integrated
- Validate with online ATS checkers

## Development

### Adding New Features
1. Update `SKILL.md` with new instructions
2. Modify `scripts/generate_docx.py` if needed
3. Update agent configuration in `~/workspace/ai/agents/resume-builder.json`
4. Test with `scripts/verify_setup.py`
5. Document in `CHANGELOG.md`

### Testing Changes
```bash
# Verify setup
scripts/.venv/bin/python scripts/verify_setup.py

# Test generation with sample content  
scripts/.venv/bin/python scripts/generate_docx.py --type resume --content test_content.json --date $(date +%Y-%m-%d)

# Test via agent
kiro chat resume-builder
```

## Version History

- **v1.3.0** (2026-09-29): Dynamic date handling, enhanced PDF generation, WSL support
- **v1.2.0** (2026-07-29): Paths config, enhanced experience data structure  
- **v1.1.0**: Initial release with ATS optimization and voice guidelines

## Support

For issues or questions:
1. Check `CHANGELOG.md` for recent updates
2. Run `scripts/verify_setup.py` for environment validation
3. Review reference files in `references/` for content guidelines
4. Test with the verification script and sample content