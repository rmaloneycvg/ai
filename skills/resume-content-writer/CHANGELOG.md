# Resume Content Writer - Changelog

## Version 1.3.0 - 2026-09-29

### ✅ Fixed: Date Handling
- **Dynamic date generation**: Updated SKILL.md Step 6 to use `$(date +%Y-%m-%d)` instead of hardcoded dates
- **Cover letter dates**: Now automatically use today's date formatted as "Month DD, YYYY"
- **Folder structure**: Output directories now use actual current date instead of hardcoded 2025-01-27

### ✅ Enhanced: PDF Generation
- **Multi-platform support**: Enhanced `generate_docx.py` to support multiple PDF conversion methods
- **Windows docx2pdf**: Primary method for native Windows environments
- **WSL + Windows Word**: Fallback method using PowerShell COM interface for WSL environments
- **Automatic fallback**: Script tries docx2pdf first, falls back to PowerShell + Word COM if needed
- **Error handling**: Comprehensive error handling with informative warnings

### ✅ Updated: Agent Configuration  
- **resume-builder.json**: Updated prompt to include dynamic date handling and PDF generation
- **Permissions**: Added PowerShell.exe and date command permissions
- **Documentation**: Clarified WSL + Windows Word PDF generation requirements

### ✅ Improved: Script Robustness
- **Path conversion**: Proper WSL path to Windows path conversion using wslpath
- **PowerShell scripts**: Auto-generated PowerShell scripts for PDF conversion when needed  
- **Cleanup handling**: Better Word COM object cleanup to prevent process hanging
- **Progress indicators**: Clear success/failure messaging for PDF generation

### 📁 Files Updated
- `~/workspace/ai/skills/resume-content-writer/SKILL.md` - Dynamic date instructions
- `~/workspace/ai/skills/resume-content-writer/scripts/generate_docx.py` - Enhanced PDF generation
- `~/workspace/ai/agents/resume-builder.json` - Updated prompt and permissions
- `~/workspace/ai/skills/resume-content-writer/CHANGELOG.md` - This file

### 🧪 Testing Completed
- ✅ Alchemer resume/cover letter generation with PDF output
- ✅ Judi Health resume/cover letter generation with PDF output  
- ✅ Dynamic date folder creation (2026-09-29)
- ✅ Windows docx2pdf integration
- ✅ WSL + PowerShell + Windows Word fallback
- ✅ Proper path conversion and error handling

### 🎯 Compatibility
- **Windows**: Full support with docx2pdf + MS Word
- **WSL**: Full support with PowerShell + Windows Word fallback
- **Linux**: DOCX generation only (no PDF without additional setup)
- **macOS**: DOCX generation only (no PDF without additional setup)

### 🔧 Dependencies
- `python-docx` (required)
- `docx2pdf` (optional, Windows + MS Word)
- PowerShell + Windows Word (WSL fallback)
- `wslpath` (WSL environments)

### 📋 Known Limitations
- PDF generation requires Windows environment or WSL with Windows Word access
- PowerShell COM interface may show minor cleanup warnings (non-blocking)
- Cover letter word count warnings for content >300 words (informational only)

## Previous Versions

### Version 1.2.0 - 2026-07-29
- Added paths config for agent tooling
- Enhanced experience data structure
- Improved ATS optimization guidelines

### Version 1.1.0 - Initial Release
- Base resume content generation
- ATS optimization features  
- Voice and style guidelines
- Reference file structure