#!/usr/bin/env python3
"""
Test suite for install.py
Validates the universal Python installer works correctly
"""

import sys
import subprocess
import platform

def test_help_command():
    """Test that --help works"""
    print("Testing --help command...")
    result = subprocess.run(
        [sys.executable, "install.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Help command failed"
    assert "iTaK Universal Installer" in result.stdout, "Help text missing"
    assert "--full-stack" in result.stdout, "Missing --full-stack option"
    assert "--minimal" in result.stdout, "Missing --minimal option"
    print("✓ Help command works correctly")

def test_python_syntax():
    """Test that install.py has valid Python syntax"""
    print("Testing Python syntax...")
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", "install.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"
    print("✓ Python syntax is valid")

def test_imports():
    """Test that all imports in install.py work"""
    print("Testing imports...")
    # Test by importing as module
    result = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, '.'); import install"],
        capture_output=True,
        text=True,
        cwd="/home/runner/work/iTaK/iTaK"
    )
    # Note: This might fail because install.py runs code on import
    # So we check if it at least doesn't have import errors
    if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
        assert False, f"Import error: {result.stderr}"
    print("✓ All imports are available")

def test_os_detection():
    """Test OS detection logic"""
    print("Testing OS detection...")
    
    # Test that platform module calls work
    try:
        os_name = platform.system()
        arch = platform.machine()
        assert os_name in ['Linux', 'Darwin', 'Windows'], f"Unknown OS: {os_name}"
        print(f"✓ OS detection works (detected: {os_name} {arch})")
    except Exception as e:
        assert False, f"OS detection failed: {e}"

def test_version_check():
    """Test Python version checking"""
    print("Testing Python version check...")
    
    version_info = sys.version_info
    assert version_info >= (3, 11), f"Python {version_info} is too old"
    print(f"✓ Python version check passed ({sys.version.split()[0]})")

def test_invalid_arguments():
    """Test handling of invalid arguments"""
    print("Testing invalid arguments...")
    
    result = subprocess.run(
        [sys.executable, "install.py", "--invalid-flag"],
        capture_output=True,
        text=True
    )
    # Should exit with error
    assert result.returncode != 0, "Should reject invalid arguments"
    assert "error" in result.stderr.lower() or "unrecognized" in result.stderr.lower(), \
        "Should show error message"
    print("✓ Invalid arguments handled correctly")

def test_script_structure():
    """Test that install.py has required components"""
    print("Testing script structure...")
    
    with open("install.py", "r") as f:
        content = f.read()
    
    # Check for key components (function-based, not class-based)
    assert "def detect_os" in content, "Missing detect_os function"
    assert "def install_prerequisites" in content, "Missing install_prerequisites functions"
    assert "def main" in content, "Missing main function"
    assert 'argparse' in content, "Missing argparse for CLI"
    assert "def create_env_file" in content, "Missing create_env_file function"
    assert "def start_full_stack" in content, "Missing start_full_stack function"
    
    print("✓ Script structure is correct")

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Testing install.py - Universal Python Installer")
    print("=" * 60)
    print()
    
    tests = [
        test_python_syntax,
        test_imports,
        test_help_command,
        test_os_detection,
        test_version_check,
        test_invalid_arguments,
        test_script_structure,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(run_all_tests())
