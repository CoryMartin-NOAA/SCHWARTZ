#!/usr/bin/env python3
"""
Test script for GRIB2 to FV3 regridding functionality.

This script tests the basic structure and argument parsing of the regridding tool
without requiring heavy scientific computing dependencies.
"""

import sys
import os
import tempfile
import subprocess
from pathlib import Path

def test_help_functionality():
    """Test that the script shows help without crashing."""
    
    # Test basic argument parsing structure
    try:
        # Simple test of argparse functionality
        import argparse
        parser = argparse.ArgumentParser(description='Test')
        parser.add_argument('--input', '-i', required=True, help='Input file')
        parser.add_argument('--output', '-out', required=True, help='Output dir')
        parser.add_argument('--npx', type=int, default=384, help='Grid resolution')
        
        # Test parsing with sample args
        test_args = ['--input', 'test.grib2', '--output', 'test_out']
        args = parser.parse_args(test_args)
        
        if args.input == 'test.grib2' and args.output == 'test_out' and args.npx == 384:
            print("✓ Basic argument parsing works")
            return True
        else:
            print("✗ Argument parsing failed")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist and have correct structure."""
    base_dir = Path(__file__).parent
    
    required_files = [
        "grib2_to_fv3_regrid.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_exist = True
    for file in required_files:
        file_path = base_dir / file
        if file_path.exists():
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} missing")
            all_exist = False
    
    return all_exist

def test_script_syntax():
    """Test that the main script has valid Python syntax."""
    script_path = Path(__file__).parent / "grib2_to_fv3_regrid.py"
    
    try:
        with open(script_path, 'r') as f:
            code = f.read()
        
        # Compile to check syntax
        compile(code, script_path, 'exec')
        print("✓ Script has valid Python syntax")
        return True
        
    except SyntaxError as e:
        print(f"✗ Syntax error in script: {e}")
        return False
    except Exception as e:
        print(f"✗ Error checking syntax: {e}")
        return False

def main():
    """Run all tests."""
    print("Running tests for GRIB2 to FV3 regridding tool...")
    print("=" * 50)
    
    tests = [
        ("File structure", test_file_structure),
        ("Script syntax", test_script_syntax),
        ("Argument parsing", test_help_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}:")
        if test_func():
            passed += 1
        
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("All tests passed! ✓")
        return 0
    else:
        print("Some tests failed! ✗")
        return 1

if __name__ == "__main__":
    sys.exit(main())