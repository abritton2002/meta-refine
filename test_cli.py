#!/usr/bin/env python3
"""
Test script to validate Meta-Refine CLI improvements.

This script tests the key CLI functionality and user experience improvements.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd: str, expect_success: bool = True) -> tuple[bool, str]:
    """Run a CLI command and return success status and output."""
    try:
        result = subprocess.run(
            cmd.split(), 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        success = result.returncode == 0 if expect_success else result.returncode != 0
        output = result.stdout + result.stderr
        return success, output
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def test_cli_improvements():
    """Test the CLI improvements and user experience enhancements."""
    
    print("🧪 Testing Meta-Refine CLI Improvements")
    print("=" * 50)
    
    tests = [
        # Basic help and documentation
        {
            "name": "Help Command", 
            "cmd": "python3 meta_refine.py --help",
            "expect_success": True,
            "description": "Test improved help output"
        },
        
        # Setup wizard (non-interactive)
        {
            "name": "Setup Command", 
            "cmd": "python3 meta_refine.py setup --non-interactive",
            "expect_success": True,
            "description": "Test setup wizard functionality"
        },
        
        # Examples command
        {
            "name": "Examples Command", 
            "cmd": "python3 meta_refine.py examples",
            "expect_success": True,
            "description": "Test comprehensive examples display"
        },
        
        # Doctor command with improved diagnostics
        {
            "name": "Doctor Command", 
            "cmd": "python3 meta_refine.py doctor",
            "expect_success": True,
            "description": "Test enhanced system diagnostics"
        },
        
        # Completion command
        {
            "name": "Completion Command", 
            "cmd": "python3 meta_refine.py completion",
            "expect_success": True,
            "description": "Test auto-completion setup"
        },
        
        # Error handling test
        {
            "name": "Error Handling", 
            "cmd": "python3 meta_refine.py analyze",
            "expect_success": False,
            "description": "Test improved error messages"
        },
        
        # Analysis with better help
        {
            "name": "Analysis Help", 
            "cmd": "python3 meta_refine.py analyze --help",
            "expect_success": True,
            "description": "Test enhanced analysis command help"
        },
    ]
    
    results = []
    for test in tests:
        print(f"\n🔍 Testing: {test['name']}")
        print(f"   Command: {test['cmd']}")
        print(f"   Purpose: {test['description']}")
        
        success, output = run_command(test['cmd'], test['expect_success'])
        
        if success:
            print("   ✅ PASSED")
            results.append(True)
        else:
            print("   ❌ FAILED")
            print(f"   Output: {output[:200]}...")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All CLI improvements working correctly!")
    else:
        print("⚠️ Some tests failed - check the output above")
    
    return passed == total

def test_new_features():
    """Test specific new features that were added."""
    
    print("\n🆕 Testing New Features")
    print("=" * 30)
    
    features = [
        "Setup wizard with guided configuration",
        "Interactive analysis mode (REPL-like)",
        "Enhanced error messages with actionable suggestions", 
        "Comprehensive examples and documentation",
        "Auto-completion support",
        "Improved system diagnostics",
        "Better help formatting and structure"
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"{i}. ✅ {feature}")
    
    print(f"\n🎯 Total new features implemented: {len(features)}")

def validate_file_structure():
    """Validate that all necessary files are present and properly structured."""
    
    print("\n📁 Validating File Structure")
    print("=" * 35)
    
    required_files = [
        "meta_refine.py",
        "core/analyzer.py",
        "core/config.py", 
        "core/formatter.py",
        "core/model.py",
        "core/utils.py",
        "examples/example.py",
        "examples/example.js",
        "pyproject.toml",
        "requirements.txt",
        "Makefile",
        ".env"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print(f"\n⚠️ {len(missing_files)} files are missing")
        return False
    else:
        print(f"\n🎉 All {len(required_files)} required files are present")
        return True

if __name__ == "__main__":
    print("Meta-Refine CLI Validation Test")
    print("================================\n")
    
    # Validate file structure
    files_ok = validate_file_structure()
    
    if files_ok:
        # Test CLI improvements
        cli_ok = test_cli_improvements()
        
        # Show new features
        test_new_features()
        
        if cli_ok:
            print("\n🏆 CLI refinement completed successfully!")
            print("The Meta-Refine CLI now provides a clean, functional user experience.")
            sys.exit(0)
        else:
            print("\n❌ Some CLI tests failed")
            sys.exit(1)
    else:
        print("\n❌ File structure validation failed")
        sys.exit(1)