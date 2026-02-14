#!/usr/bin/env python3
"""
iTaK Setup Script - Cross-platform Onboarding
==================================================
Automatically installs all dependencies and sets up the iTaK environment
on Mac, Linux, Windows, and WSL.

Usage:
    python setup.py
    python3 setup.py
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


# ─── Color Codes ───────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(msg: str):
    """Print a section header."""
    print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}{msg:^60}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}\n")


def print_ok(msg: str):
    """Print a success message."""
    print(f"  {GREEN}✓{RESET} {msg}")


def print_info(msg: str):
    """Print an info message."""
    print(f"  {CYAN}ℹ{RESET} {msg}")


def print_warn(msg: str):
    """Print a warning message."""
    print(f"  {YELLOW}⚠{RESET} {msg}")


def print_error(msg: str):
    """Print an error message."""
    print(f"  {RED}✗{RESET} {msg}")


def run_command(cmd: list, description: str = "", check: bool = True) -> tuple[bool, str]:
    """
    Run a shell command and return success status and output.
    
    Args:
        cmd: Command as a list of strings
        description: Human-readable description for logging
        check: If True, raise on error
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        if description:
            print_info(f"{description}...")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=check,
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Failed: {e.stderr}")
        return False, e.stderr
    except FileNotFoundError:
        if check:
            print_error(f"Command not found: {cmd[0]}")
        return False, f"Command not found: {cmd[0]}"


def detect_os() -> dict:
    """
    Detect the operating system and return details.
    
    Returns:
        Dict with 'os', 'is_wsl', 'package_manager' keys
    """
    system = platform.system()
    is_wsl = False
    package_manager = None
    
    # Check for WSL
    if system == "Linux":
        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    is_wsl = True
        except FileNotFoundError:
            pass
    
    # Determine package manager
    if system == "Darwin":
        package_manager = "brew" if shutil.which("brew") else None
        os_name = "macOS"
    elif system == "Linux":
        if is_wsl:
            os_name = "WSL (Windows Subsystem for Linux)"
        else:
            os_name = "Linux"
        
        # Detect Linux package manager
        if shutil.which("apt"):
            package_manager = "apt"
        elif shutil.which("yum"):
            package_manager = "yum"
        elif shutil.which("dnf"):
            package_manager = "dnf"
        elif shutil.which("pacman"):
            package_manager = "pacman"
    elif system == "Windows":
        os_name = "Windows"
        package_manager = "choco" if shutil.which("choco") else None
    else:
        os_name = system
    
    return {
        "os": os_name,
        "system": system,
        "is_wsl": is_wsl,
        "package_manager": package_manager,
    }


def check_python_version() -> bool:
    """Check if Python version is 3.11+."""
    version = sys.version_info
    if version >= (3, 11):
        print_ok(f"Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        print_error(f"Python 3.11+ required, found {version.major}.{version.minor}.{version.micro}")
        return False


def check_pip() -> bool:
    """Check if pip is available."""
    success, _ = run_command([sys.executable, "-m", "pip", "--version"], check=False)
    if success:
        print_ok("pip is available")
        return True
    else:
        print_error("pip not found")
        return False


def install_system_dependencies(os_info: dict) -> bool:
    """
    Install system-level dependencies based on OS.
    
    Args:
        os_info: OS information from detect_os()
    
    Returns:
        True if successful or skipped, False if failed
    """
    system = os_info["system"]
    pkg_mgr = os_info["package_manager"]
    
    print_info("Checking system dependencies...")
    
    # Git check
    if shutil.which("git"):
        print_ok("Git is installed")
    else:
        print_warn("Git not found - recommended for version control")
        if pkg_mgr:
            if pkg_mgr == "brew":
                print_info("You can install git with: brew install git")
            elif pkg_mgr in ["apt"]:
                print_info("You can install git with: sudo apt install git")
            elif pkg_mgr in ["yum", "dnf"]:
                print_info(f"You can install git with: sudo {pkg_mgr} install git")
            elif pkg_mgr == "pacman":
                print_info("You can install git with: sudo pacman -S git")
            elif pkg_mgr == "choco":
                print_info("You can install git with: choco install git")
    
    # Docker check (optional)
    if shutil.which("docker"):
        print_ok("Docker is installed")
    else:
        print_warn("Docker not found - sandbox mode will be unavailable")
        print_info("Visit https://docs.docker.com/get-docker/ to install Docker")
    
    return True


def create_virtual_environment() -> bool:
    """Create a virtual environment if not already in one."""
    # Check if we're in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    
    if in_venv:
        print_ok("Already in a virtual environment")
        return True
    
    venv_path = Path("venv")
    if venv_path.exists():
        print_ok("Virtual environment already exists at ./venv")
        print_info("Activate it with:")
        if platform.system() == "Windows":
            print_info("  venv\\Scripts\\activate")
        else:
            print_info("  source venv/bin/activate")
        return True
    
    print_info("Creating virtual environment...")
    success, _ = run_command([sys.executable, "-m", "venv", "venv"], check=False)
    
    if success:
        print_ok("Virtual environment created at ./venv")
        print_info("Activate it with:")
        if platform.system() == "Windows":
            print_info("  venv\\Scripts\\activate")
        else:
            print_info("  source venv/bin/activate")
        print_warn("Please activate the virtual environment and re-run setup.py")
        return False  # Require activation
    else:
        print_error("Failed to create virtual environment")
        return False


def install_python_packages() -> bool:
    """Install Python packages from requirements.txt."""
    req_file = Path("requirements.txt")
    
    if not req_file.exists():
        print_error("requirements.txt not found!")
        return False
    
    print_info("Installing Python packages from requirements.txt...")
    print_info("This may take a few minutes...")
    
    success, output = run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"],
        check=False
    )
    
    if success:
        print_ok("All Python packages installed successfully")
        return True
    else:
        print_error("Failed to install some packages")
        print_error(output)
        return False


def install_playwright() -> bool:
    """Install Playwright browsers."""
    print_info("Installing Playwright browsers (required for browser automation)...")
    print_info("This may take a few minutes and download ~300MB...")
    
    # First check if playwright is installed
    try:
        import playwright
        print_ok("Playwright package is installed")
    except ImportError:
        print_error("Playwright package not found - should have been installed with requirements.txt")
        return False
    
    # Install chromium browser
    success, output = run_command(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=False
    )
    
    if success:
        print_ok("Playwright Chromium browser installed")
        return True
    else:
        print_warn("Failed to install Playwright browsers")
        print_info("You can install manually with: python -m playwright install chromium")
        return True  # Non-critical, return True to continue


def setup_config_files() -> bool:
    """Copy example config files if they don't exist."""
    print_info("Setting up configuration files...")
    
    configs = [
        (".env.example", ".env"),
        ("config.json.example", "config.json"),
    ]
    
    all_ok = True
    for example, target in configs:
        example_path = Path(example)
        target_path = Path(target)
        
        if target_path.exists():
            print_ok(f"{target} already exists")
        elif example_path.exists():
            try:
                shutil.copy(example_path, target_path)
                print_ok(f"Created {target} from {example}")
                print_warn(f"Please edit {target} and add your API keys!")
            except Exception as e:
                print_error(f"Failed to copy {example} to {target}: {e}")
                all_ok = False
        else:
            print_error(f"{example} not found - cannot create {target}")
            all_ok = False
    
    return all_ok


def create_directories() -> bool:
    """Create necessary data directories."""
    print_info("Creating data directories...")
    
    directories = ["data", "logs"]
    
    for dirname in directories:
        dirpath = Path(dirname)
        try:
            dirpath.mkdir(parents=True, exist_ok=True)
            if dirpath.exists():
                print_ok(f"Directory {dirname}/ ready")
            else:
                print_error(f"Failed to create {dirname}/")
                return False
        except Exception as e:
            print_error(f"Failed to create {dirname}/: {e}")
            return False
    
    return True


def run_doctor() -> bool:
    """Run the iTaK doctor diagnostic."""
    print_info("Running iTaK diagnostic...")
    
    success, _ = run_command(
        [sys.executable, "-m", "core.doctor"],
        check=False
    )
    
    return success


def print_next_steps():
    """Print instructions for what to do next."""
    print_header("🎉 Setup Complete!")
    
    print(f"{BOLD}Next Steps:{RESET}\n")
    
    print(f"1. {BOLD}Configure API Keys{RESET}")
    print(f"   Edit .env and add at least one LLM API key:")
    print(f"   {CYAN}   - OPENAI_API_KEY=sk-...{RESET}")
    print(f"   {CYAN}   - ANTHROPIC_API_KEY=sk-ant-...{RESET}")
    print(f"   {CYAN}   - GEMINI_API_KEY=AIza...{RESET}")
    print(f"   {CYAN}   - Or use local Ollama (no key needed){RESET}\n")
    
    print(f"2. {BOLD}Review Configuration{RESET}")
    print(f"   Edit config.json to customize:")
    print(f"   {CYAN}   - Model preferences{RESET}")
    print(f"   {CYAN}   - Memory backends{RESET}")
    print(f"   {CYAN}   - Adapter settings{RESET}\n")
    
    print(f"3. {BOLD}Run Diagnostic{RESET}")
    print(f"   {CYAN}python main.py --doctor{RESET}\n")
    
    print(f"4. {BOLD}Start iTaK{RESET}")
    print(f"   {CYAN}python main.py                 # CLI mode{RESET}")
    print(f"   {CYAN}python main.py --webui         # With dashboard{RESET}")
    print(f"   {CYAN}python main.py --adapter discord --webui  # Discord bot{RESET}\n")
    
    print(f"{BOLD}Documentation:{RESET}")
    print(f"   {CYAN}README.md               # Project overview{RESET}")
    print(f"   {CYAN}docs/getting-started.md # Detailed setup guide{RESET}")
    print(f"   {CYAN}docs/configuration.md   # Config reference{RESET}\n")
    
    print(f"{GREEN}Happy AI agent building! 🧠{RESET}\n")


def main():
    """Main setup routine."""
    print_header("iTaK Setup - Cross-Platform Onboarding")
    
    # Detect OS
    os_info = detect_os()
    print_ok(f"Detected OS: {os_info['os']}")
    if os_info["package_manager"]:
        print_ok(f"Package manager: {os_info['package_manager']}")
    
    # Check Python version
    if not check_python_version():
        print_error("\n❌ Python 3.11+ is required. Please upgrade Python and try again.")
        print_info("Visit https://www.python.org/downloads/")
        sys.exit(1)
    
    # Check pip
    if not check_pip():
        print_error("\n❌ pip is required. Please install pip and try again.")
        sys.exit(1)
    
    # Check system dependencies
    install_system_dependencies(os_info)
    
    # Virtual environment (recommended but not required)
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        print_warn("\n⚠️  Not running in a virtual environment")
        print_info("It's recommended to use a virtual environment")
        print_info("Creating one now...")
        if not create_virtual_environment():
            print_warn("\nSetup paused. Please activate venv and re-run:")
            print_info(f"  {CYAN}source venv/bin/activate{RESET}  (Mac/Linux)")
            print_info(f"  {CYAN}venv\\Scripts\\activate{RESET}     (Windows)")
            print_info(f"  {CYAN}python setup.py{RESET}")
            sys.exit(0)
    
    # Install Python packages
    print_header("Installing Python Dependencies")
    if not install_python_packages():
        print_error("\n❌ Failed to install Python packages")
        sys.exit(1)
    
    # Install Playwright
    print_header("Installing Playwright Browsers")
    install_playwright()  # Non-critical, continue even if fails
    
    # Setup config files
    print_header("Setting Up Configuration")
    if not setup_config_files():
        print_warn("\n⚠️  Some configuration files could not be created")
    
    # Create directories
    if not create_directories():
        print_error("\n❌ Failed to create required directories")
        sys.exit(1)
    
    # Print next steps
    print_next_steps()
    
    # Optionally run doctor (only in interactive mode)
    if sys.stdin.isatty():
        print(f"\n{BOLD}Would you like to run the diagnostic now? (y/n):{RESET} ", end="")
        try:
            response = input().strip().lower()
            if response in ["y", "yes"]:
                print()
                run_doctor()
        except (KeyboardInterrupt, EOFError):
            print("\n")
    
    print(f"\n{GREEN}✓ Setup complete!{RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Setup interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{RED}Setup failed with error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
