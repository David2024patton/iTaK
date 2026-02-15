"""
Tests for install.py - Universal Installer
"""

import sys
import subprocess
import os
from pathlib import Path
import pytest


def test_installer_file_exists():
    """Test that install.py exists"""
    install_py = Path(__file__).parent.parent / "install.py"
    assert install_py.exists(), "install.py should exist in repository root"


def test_installer_is_executable():
    """Test that install.py is executable"""
    install_py = Path(__file__).parent.parent / "install.py"
    if os.name != "nt":  # Skip on Windows
        assert os.access(install_py, os.X_OK), "install.py should be executable"


def test_installer_python_syntax():
    """Test that install.py has valid Python syntax"""
    install_py = Path(__file__).parent.parent / "install.py"
    
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(install_py)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"install.py has syntax errors: {result.stderr}"


def test_installer_imports():
    """Test that install.py can be imported without errors"""
    install_py = Path(__file__).parent.parent / "install.py"
    
    result = subprocess.run(
        [sys.executable, "-c", f"import sys; sys.path.insert(0, '{install_py.parent}'); import install"],
        capture_output=True,
        text=True
    )
    
    # Should import successfully (exit code 0)
    assert result.returncode == 0, f"install.py import failed: {result.stderr}"


def test_installer_help():
    """Test that install.py --help works"""
    install_py = Path(__file__).parent.parent / "install.py"
    
    result = subprocess.run(
        [sys.executable, str(install_py), "--help"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert result.returncode == 0, "install.py --help should exit with code 0"
    assert "iTaK Universal Installer" in result.stdout, "Help text should mention iTaK"
    assert "--minimal" in result.stdout, "Help should show --minimal option"
    assert "--skip-deps" in result.stdout, "Help should show --skip-deps option"


def test_installer_version():
    """Test that install.py --version works"""
    install_py = Path(__file__).parent.parent / "install.py"
    
    result = subprocess.run(
        [sys.executable, str(install_py), "--version"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert result.returncode == 0, "install.py --version should exit with code 0"
    assert "iTaK Installer" in result.stdout or "iTaK Installer" in result.stderr, \
        "Version output should mention iTaK Installer"


def test_installer_detects_os():
    """Test that install.py can detect the operating system"""
    install_py = Path(__file__).parent.parent / "install.py"
    
    # Run a test that imports and calls detect_os
    test_code = """
import sys
sys.path.insert(0, '{path}')
from install import detect_os
os_type, os_name = detect_os()
print(f"OS: {{os_type}}, Name: {{os_name}}")
assert os_type in ['linux', 'macos', 'windows', 'wsl', 'unknown'], f"Invalid OS type: {{os_type}}"
""".format(path=install_py.parent)
    
    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert result.returncode == 0, f"OS detection failed: {result.stderr}"
    assert "OS:" in result.stdout, "OS detection should output OS information"


def test_installer_checks_python_version():
    """Test that install.py checks Python version correctly"""
    install_py = Path(__file__).parent.parent / "install.py"
    
    # Test that current Python passes the check
    test_code = """
import sys
sys.path.insert(0, '{path}')
from install import check_python_version
result = check_python_version()
assert result is True, "Current Python version should pass the check"
""".format(path=install_py.parent)
    
    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # If we're running Python 3.11+, this should pass
    if sys.version_info >= (3, 11):
        assert result.returncode == 0, f"Python version check failed: {result.stderr}"


def test_installer_invalid_args():
    """Test that install.py handles invalid arguments gracefully"""
    install_py = Path(__file__).parent.parent / "install.py"
    
    result = subprocess.run(
        [sys.executable, str(install_py), "--invalid-arg-that-does-not-exist"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # Should exit with non-zero code for invalid args
    assert result.returncode != 0, "install.py should fail on invalid arguments"


def test_installer_has_required_functions():
    """Test that install.py defines all required functions"""
    install_py = Path(__file__).parent.parent / "install.py"
    
    required_functions = [
        "detect_os",
        "check_python_version",
        "check_command",
        "check_prerequisites",
        "install_dependencies",
        "setup_configuration",
        "create_data_directories",
        "display_next_steps",
        "main",
    ]
    
    for func in required_functions:
        test_code = f"""
import sys
sys.path.insert(0, '{install_py.parent}')
import install
assert hasattr(install, '{func}'), "install.py should define {func}() function"
"""
        
        result = subprocess.run(
            [sys.executable, "-c", test_code],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0, f"install.py should define {func}() function"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
