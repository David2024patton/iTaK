#!/usr/bin/env python3
"""
iTaK Universal Installer
Cross-platform installation script for Linux, macOS, Windows, and WSL.
No external dependencies - uses only Python standard library.
"""

import sys
import os
import platform
import subprocess
import shutil
import argparse
from pathlib import Path
from typing import Tuple, Optional

# Version
VERSION = "1.0.0"

# Minimum requirements
MIN_PYTHON_VERSION = (3, 11)


class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


def print_header(text: str) -> None:
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def detect_os() -> Tuple[str, str]:
    """
    Detect operating system and return (os_type, os_name).
    
    Returns:
        Tuple of (os_type, os_name) where os_type is one of:
        'linux', 'macos', 'windows', 'wsl'
    """
    system = platform.system().lower()
    
    # Check for WSL (Windows Subsystem for Linux)
    if system == "linux" and os.path.exists("/proc/version"):
        with open("/proc/version", "r") as f:
            if "microsoft" in f.read().lower():
                return ("wsl", "Windows Subsystem for Linux")
    
    if system == "linux":
        # Try to detect Linux distribution
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            os_name = line.split("=")[1].strip().strip('"')
                            return ("linux", os_name)
            return ("linux", "Linux")
        except Exception:
            return ("linux", "Linux")
    elif system == "darwin":
        return ("macos", f"macOS {platform.mac_ver()[0]}")
    elif system == "windows":
        return ("windows", f"Windows {platform.release()}")
    else:
        return ("unknown", system)


def check_python_version() -> bool:
    """Check if Python version meets minimum requirements"""
    current = sys.version_info
    required = MIN_PYTHON_VERSION
    
    if current >= required:
        print_success(f"Python {current.major}.{current.minor}.{current.micro} detected")
        return True
    else:
        print_error(f"Python {required[0]}.{required[1]}+ required, but {current.major}.{current.minor}.{current.micro} found")
        return False


def check_command(command: str) -> bool:
    """Check if a command is available in PATH"""
    return shutil.which(command) is not None


def check_prerequisites() -> dict:
    """Check all prerequisites and return status dict"""
    print_header("Checking Prerequisites")
    
    results = {}
    
    # Python
    results["python"] = check_python_version()
    
    # pip
    if check_command("pip") or check_command("pip3"):
        print_success("pip is installed")
        results["pip"] = True
    else:
        print_error("pip not found")
        results["pip"] = False
    
    # Git
    if check_command("git"):
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                print_success(f"Git is installed: {version}")
                results["git"] = True
            else:
                print_warning("Git found but version check failed")
                results["git"] = True
        except Exception:
            print_warning("Git found but version check failed")
            results["git"] = True
    else:
        print_warning("Git not found (optional for installation)")
        results["git"] = False
    
    # Docker (optional)
    if check_command("docker"):
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                print_success(f"Docker is installed: {version}")
                results["docker"] = True
            else:
                print_warning("Docker found but not working properly")
                results["docker"] = False
        except Exception:
            print_warning("Docker found but not accessible")
            results["docker"] = False
    else:
        print_info("Docker not found (optional, needed for full-stack mode)")
        results["docker"] = False
    
    return results


def install_dependencies(minimal: bool = False) -> bool:
    """Install Python dependencies"""
    print_header("Installing Dependencies")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print_error(f"{requirements_file} not found")
        return False
    
    print_info(f"Installing packages from {requirements_file}...")
    
    # Determine pip command
    pip_cmd = "pip3" if check_command("pip3") else "pip"
    
    # Timeout in seconds
    install_timeout = 600  # 10 minutes
    
    try:
        # Install requirements
        cmd = [pip_cmd, "install", "-r", str(requirements_file)]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=install_timeout
        )
        
        if result.returncode == 0:
            print_success("Dependencies installed successfully")
            
            # Install Playwright browsers if not minimal
            if not minimal:
                print_info("Installing Playwright browsers...")
                try:
                    subprocess.run(
                        ["playwright", "install", "chromium"],
                        capture_output=True,
                        timeout=300
                    )
                    print_success("Playwright browsers installed")
                except Exception as e:
                    print_warning(f"Playwright browser installation skipped: {e}")
            
            return True
        else:
            print_error("Dependency installation failed")
            print(f"Error: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print_error(f"Installation timeout ({install_timeout // 60} minutes)")
        return False
    except Exception as e:
        print_error(f"Installation error: {e}")
        return False


def setup_configuration() -> bool:
    """Set up configuration files"""
    print_header("Setting Up Configuration")
    
    success = True
    
    # Copy .env.example to .env if it doesn't exist
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_example.exists():
        if not env_file.exists():
            try:
                shutil.copy(env_example, env_file)
                print_success(f"Created {env_file} from {env_example}")
                print_warning(f"Please edit {env_file} and add your API keys")
            except Exception as e:
                print_error(f"Failed to copy {env_example}: {e}")
                success = False
        else:
            print_info(f"{env_file} already exists, skipping")
    else:
        print_warning(f"{env_example} not found")
    
    # Copy config.json.example to config.json if it doesn't exist
    config_example = Path("config.json.example")
    config_file = Path("config.json")
    
    if config_example.exists():
        if not config_file.exists():
            try:
                shutil.copy(config_example, config_file)
                print_success(f"Created {config_file} from {config_example}")
            except Exception as e:
                print_error(f"Failed to copy {config_example}: {e}")
                success = False
        else:
            print_info(f"{config_file} already exists, skipping")
    else:
        print_warning(f"{config_example} not found")
    
    return success


def create_data_directories() -> bool:
    """Create necessary data directories"""
    print_header("Creating Data Directories")
    
    directories = [
        "data",
        "data/db",
        "data/logs",
        "data/media",
    ]
    
    success = True
    for directory in directories:
        dir_path = Path(directory)
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print_success(f"Created directory: {directory}")
        except Exception as e:
            print_error(f"Failed to create {directory}: {e}")
            success = False
    
    return success


def display_next_steps(minimal: bool = False) -> None:
    """Display next steps for the user"""
    print_header("Installation Complete!")
    
    print(f"{Colors.BOLD}Next Steps:{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW}1.{Colors.RESET} Configure your API keys:")
    print(f"   Edit .env and add at least one LLM API key:")
    print(f"   {Colors.CYAN}GEMINI_API_KEY=your_key_here{Colors.RESET}")
    print(f"   or")
    print(f"   {Colors.CYAN}OPENAI_API_KEY=your_key_here{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW}2.{Colors.RESET} Run iTaK:")
    print(f"   {Colors.GREEN}python main.py{Colors.RESET}  # CLI mode")
    print(f"   {Colors.GREEN}python main.py --webui{Colors.RESET}  # With web dashboard")
    print(f"   {Colors.GREEN}python main.py --adapter discord --webui{Colors.RESET}  # Discord bot\n")
    
    if not minimal:
        print(f"{Colors.YELLOW}3.{Colors.RESET} Optional - Full Stack (Docker required):")
        print(f"   {Colors.GREEN}docker compose up -d{Colors.RESET}  # Starts Neo4j, Weaviate, SearXNG\n")
    
    print(f"{Colors.BOLD}Documentation:{Colors.RESET}")
    print(f"   {Colors.CYAN}docs/getting-started.md{Colors.RESET}  - Quick start guide")
    print(f"   {Colors.CYAN}docs/architecture.md{Colors.RESET}     - System architecture")
    print(f"   {Colors.CYAN}docs/config.md{Colors.RESET}          - Configuration reference\n")


def main() -> int:
    """Main installation function"""
    parser = argparse.ArgumentParser(
        description="iTaK Universal Installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install.py                 # Full installation
  python install.py --minimal       # Minimal installation (skip optional components)
  python install.py --help          # Show this help message
        """
    )
    
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Minimal installation (skip Playwright browsers and Docker components)"
    )
    
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip dependency installation (only setup config files)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"iTaK Installer v{VERSION}"
    )
    
    args = parser.parse_args()
    
    # Print welcome banner
    print_header(f"iTaK Universal Installer v{VERSION}")
    
    # Detect OS
    os_type, os_name = detect_os()
    print_info(f"Detected OS: {os_name} ({os_type})")
    
    # Check prerequisites
    prereqs = check_prerequisites()
    
    # Check critical prerequisites
    if not prereqs["python"]:
        print_error(f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ is required")
        return 1
    
    if not prereqs["pip"]:
        print_error("pip is required for installation")
        return 1
    
    # Install dependencies
    if not args.skip_deps:
        if not install_dependencies(minimal=args.minimal):
            print_error("Dependency installation failed")
            return 1
    else:
        print_info("Skipping dependency installation (--skip-deps)")
    
    # Setup configuration
    if not setup_configuration():
        print_warning("Configuration setup had some issues")
    
    # Create data directories
    if not create_data_directories():
        print_warning("Some data directories could not be created")
    
    # Display next steps
    display_next_steps(minimal=args.minimal)
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Installation cancelled by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
