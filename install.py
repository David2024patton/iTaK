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
import json
import secrets
import tarfile
import datetime
from pathlib import Path
from typing import Tuple

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
    
    requirements_file = Path("install/requirements/requirements.txt")
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

    if env_file.exists():
        if ensure_env_ports(env_file):
            print_success("Ensured random host ports in .env")
        else:
            print_warning("Could not ensure random host ports in .env")
    
    # Copy install/config/config.json.example to config.json if it doesn't exist
    config_example = Path("install/config/config.json.example")
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

    if config_file.exists():
        if ensure_webui_auth_token(config_file):
            print_success("Ensured unique WebUI auth token in config.json")
        else:
            print_warning("Could not ensure WebUI auth token in config.json")
    
    return success


def ensure_webui_auth_token(config_path: Path) -> bool:
    """Generate and persist a unique WebUI auth token when missing/blank."""
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return False

    webui = data.get("webui")
    if not isinstance(webui, dict):
        webui = {}
        data["webui"] = webui

    current = str(webui.get("auth_token", "")).strip()
    if current:
        return True

    webui["auth_token"] = secrets.token_hex(24)
    try:
        config_path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")
        return True
    except Exception:
        return False


def ensure_env_ports(env_path: Path) -> bool:
    """Ensure .env has random 5-digit host ports when missing/blank."""
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return False

    keys = [
        "WEBUI_PORT",
        "NEO4J_HTTP_PORT",
        "NEO4J_BOLT_PORT",
        "WEAVIATE_PORT",
        "SEARXNG_PORT",
    ]

    existing = {}
    for line in lines:
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        existing[key.strip()] = value.strip()

    randomize = existing.get("ITAK_RANDOM_PORTS", "").strip().lower() in {"1", "true", "yes"}

    used = set()
    for key in keys:
        value = existing.get(key, "").strip()
        if value.isdigit():
            used.add(int(value))

    def random_port() -> int:
        for _ in range(1000):
            port = secrets.randbelow(55535) + 10000
            if port not in used:
                used.add(port)
                return port
        return secrets.randbelow(55535) + 10000

    updated = []
    for line in lines:
        if "=" not in line or line.lstrip().startswith("#"):
            updated.append(line)
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key == "ITAK_RANDOM_PORTS" and randomize:
            value = "false"
        if key in keys and (randomize or not value or value == "0"):
            value = str(random_port())
        updated.append(f"{key}={value}")

    try:
        env_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
        return True
    except Exception:
        return False


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
    print("   Edit .env and add at least one LLM API key:")
    print(f"   {Colors.CYAN}GEMINI_API_KEY=your_key_here{Colors.RESET}")
    print("   or")
    print(f"   {Colors.CYAN}OPENAI_API_KEY=your_key_here{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW}2.{Colors.RESET} Run iTaK:")
    print(f"   {Colors.GREEN}python -m app.main{Colors.RESET}  # CLI mode")
    print(f"   {Colors.GREEN}python -m app.main --webui{Colors.RESET}  # With web dashboard")
    print(f"   {Colors.GREEN}python -m app.main --adapter discord --webui{Colors.RESET}  # Discord bot\n")
    
    if not minimal:
        print(f"{Colors.YELLOW}3.{Colors.RESET} Optional - Full Stack (Docker required):")
        print(f"   {Colors.GREEN}docker compose up -d{Colors.RESET}  # Starts Neo4j, Weaviate, SearXNG\n")
    
    print(f"{Colors.BOLD}Documentation:{Colors.RESET}")
    print(f"   {Colors.CYAN}docs/getting-started.md{Colors.RESET}  - Quick start guide")
    print(f"   {Colors.CYAN}docs/architecture.md{Colors.RESET}     - System architecture")
    print(f"   {Colors.CYAN}docs/config.md{Colors.RESET}          - Configuration reference\n")


def _collect_path_stats(root: Path) -> dict:
    """Collect basic file/size stats for migration reporting."""
    if not root.exists():
        return {"exists": False, "files": 0, "bytes": 0}

    files = 0
    total_bytes = 0
    for path in root.rglob("*"):
        if path.is_file():
            files += 1
            try:
                total_bytes += path.stat().st_size
            except Exception:
                pass

    return {"exists": True, "files": files, "bytes": total_bytes}


def migration_status(source: Path, target: Path) -> dict:
    """Return migration status report for source and target paths."""
    return {
        "source": str(source),
        "target": str(target),
        "source_stats": _collect_path_stats(source),
        "target_stats": _collect_path_stats(target),
    }


def migrate_user_data(source: Path, target: Path, backup_dir: Path) -> tuple[bool, dict]:
    """Migrate user/runtime data with backup + verification guidance.

    Migration is copy-based for safety (non-destructive source retention).
    """
    report = {
        "source": str(source),
        "target": str(target),
        "backup": "",
        "copied": [],
        "skipped": [],
        "verify": {},
        "rollback": "",
    }

    if not source.exists() or not source.is_dir():
        return False, {**report, "error": f"Source path not found: {source}"}

    target.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    backup_file = backup_dir / f"user-data-backup-{timestamp}.tar.gz"

    if any(target.iterdir()):
        with tarfile.open(backup_file, "w:gz") as tar:
            tar.add(target, arcname=target.name)
        report["backup"] = str(backup_file)
        report["rollback"] = f"tar -xzf {backup_file} -C {target.parent}"

    for item in sorted(source.iterdir(), key=lambda p: p.name):
        destination = target / item.name
        if destination.exists():
            report["skipped"].append(item.name)
            continue

        if item.is_dir():
            shutil.copytree(item, destination)
        else:
            shutil.copy2(item, destination)
        report["copied"].append(item.name)

    report["verify"] = migration_status(source, target)
    return True, report


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

    parser.add_argument(
        "--migrate-user-data",
        action="store_true",
        help="Migrate user/runtime data from --migration-source to --migration-target with backup + report",
    )

    parser.add_argument(
        "--migration-status",
        action="store_true",
        help="Show source/target migration status report and exit",
    )

    parser.add_argument(
        "--migration-source",
        type=str,
        default="data",
        help="Source directory for user data migration (default: data)",
    )

    parser.add_argument(
        "--migration-target",
        type=str,
        default="runtime",
        help="Target directory for user data migration (default: runtime)",
    )

    parser.add_argument(
        "--migration-backup-dir",
        type=str,
        default="data/migration_backups",
        help="Directory for migration backups (default: data/migration_backups)",
    )
    
    args = parser.parse_args()

    source = Path(args.migration_source)
    target = Path(args.migration_target)
    backup_dir = Path(args.migration_backup_dir)

    if args.migration_status:
        status = migration_status(source, target)
        print(json.dumps(status, indent=2))
        return 0

    if args.migrate_user_data:
        ok, report = migrate_user_data(source, target, backup_dir)
        print(json.dumps(report, indent=2))
        return 0 if ok else 1
    
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
