#!/usr/bin/env python3
"""
Verification script for resume-content-writer skill setup.
Checks dependencies, paths, and PDF generation capabilities.
"""

import sys
import os
import json
import subprocess
from pathlib import Path

def check_python_deps():
    """Check Python dependencies."""
    print("🔍 Checking Python dependencies...")
    
    try:
        from docx import Document
        print("  ✅ python-docx installed")
    except ImportError:
        print("  ❌ python-docx missing - run: pip install python-docx")
        return False
        
    try:
        from docx2pdf import convert
        print("  ✅ docx2pdf installed")
        has_docx2pdf = True
    except ImportError:
        print("  ⚠️  docx2pdf not installed - PDF generation may use PowerShell fallback")
        has_docx2pdf = False
    
    return True, has_docx2pdf

def check_paths():
    """Check required paths and files."""
    print("\n📁 Checking file structure...")
    
    skill_dir = Path(__file__).parent.parent
    required_files = [
        "SKILL.md",
        "references/experience.json", 
        "references/voice.md",
        "references/guardrails.md",
        "references/ats-optimization.md",
        "references/resume-format.md",
        "references/cover-letter.md",
        "references/output-conventions.md",
        "scripts/generate_docx.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = skill_dir / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def check_experience_data():
    """Validate experience.json structure."""
    print("\n📊 Checking experience data...")
    
    skill_dir = Path(__file__).parent.parent
    exp_file = skill_dir / "references/experience.json"
    
    try:
        with open(exp_file) as f:
            data = json.load(f)
            
        required_keys = ["personalInfo", "skills", "experience"]
        for key in required_keys:
            if key in data:
                print(f"  ✅ {key} section found")
            else:
                print(f"  ❌ {key} section missing")
                return False
                
        exp_count = len(data.get("experience", []))
        print(f"  ✅ {exp_count} experience entries")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error reading experience.json: {e}")
        return False

def check_pdf_capabilities():
    """Check PDF generation capabilities."""
    print("\n🖨️  Checking PDF generation capabilities...")
    
    # Check if on Windows or WSL
    try:
        result = subprocess.run(["uname", "-r"], capture_output=True, text=True)
        if "microsoft" in result.stdout.lower() or "wsl" in result.stdout.lower():
            print("  🐧 WSL environment detected")
            is_wsl = True
        else:
            print("  🐧 Linux environment detected")
            is_wsl = False
    except:
        print("  🪟 Windows environment detected")
        is_wsl = False
    
    # Check PowerShell availability 
    if is_wsl:
        try:
            result = subprocess.run(["powershell.exe", "-Command", "Write-Host 'PowerShell available'"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ PowerShell.exe accessible from WSL")
            else:
                print("  ⚠️  PowerShell.exe not accessible from WSL")
        except:
            print("  ❌ PowerShell.exe not found")
    
    # Check if wslpath is available
    if is_wsl:
        try:
            result = subprocess.run(["wslpath", "-w", "/tmp"], capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ wslpath available for path conversion")
            else:
                print("  ⚠️  wslpath not available")
        except:
            print("  ❌ wslpath not found")
    
    return True

def check_output_directory():
    """Check output directory setup."""
    print("\n📂 Checking output directory setup...")
    
    resume_dir = Path.home() / "workspace/resume"
    if resume_dir.exists():
        print(f"  ✅ Resume directory exists: {resume_dir}")
    else:
        print(f"  ⚠️  Resume directory doesn't exist (will be created): {resume_dir}")
    
    # Check current date folder would be created correctly
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    today_dir = resume_dir / today
    print(f"  📅 Today's folder would be: {today_dir}")
    
    return True

def main():
    """Run all verification checks."""
    print("🚀 Resume Content Writer - Setup Verification\n")
    
    checks = [
        ("Python Dependencies", check_python_deps),
        ("File Structure", check_paths), 
        ("Experience Data", check_experience_data),
        ("PDF Capabilities", check_pdf_capabilities),
        ("Output Directory", check_output_directory)
    ]
    
    all_passed = True
    for name, check_func in checks:
        try:
            result = check_func()
            if isinstance(result, tuple):
                passed = result[0]
            else:
                passed = result
                
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"  ❌ Error in {name}: {e}")
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All checks passed! Resume Content Writer is ready to use.")
        print("\nTo generate a resume, use:")
        print("  kiro chat resume-builder")
        print("  # Then provide a job description")
    else:
        print("⚠️  Some checks failed. Review the issues above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())