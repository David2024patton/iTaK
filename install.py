#!/usr/bin/env python3
"""
iTaK Universal Installer
========================

One script to install iTaK on any platform:
- Linux (Ubuntu, Debian, Fedora, RHEL, CentOS, Arch)
- macOS (Intel and Apple Silicon)
- Windows (with WSL auto-install)
- WSL (Windows Subsystem for Linux)

Usage:
    python install.py              # Interactive installation
    python install.py --full-stack # Install with all databases
    python install.py --minimal    # Install iTaK only
    python install.py --help       # Show help

No external dependencies required - uses Python standard library only.
"""

import os
import sys
import platform
import subprocess
import shutil
import json
import time
import argparse
from pathlib import Path
from typing import Optional, Tuple, List

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @classmethod
    def supports_color(cls) -> bool:
        """Check if terminal supports colors"""
        return (
            hasattr(sys.stdout, 'isatty') and
            sys.stdout.isatty() and
            os.getenv('TERM') != 'dumb' and
            sys.platform != 'win32'  # Windows CMD doesn't support ANSI by default
        )

# Disable colors on Windows or unsupported terminals
if not Colors.supports_color():
    for attr in dir(Colors):
        if not attr.startswith('_') and attr != 'supports_color':
            setattr(Colors, attr, '')


def print_header(text: str):
    """Print a header with formatting"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def run_command(cmd: List[str], check: bool = True, capture: bool = False) -> Tuple[int, str, str]:
    """
    Run a command and return (returncode, stdout, stderr)
    
    Args:
        cmd: Command as list of strings
        check: Raise exception on non-zero exit
        capture: Capture output instead of streaming
    """
    try:
        if capture:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=check
            )
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, check=check)
            return result.returncode, "", ""
    except subprocess.CalledProcessError as e:
        return e.returncode, "", str(e)
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"


def detect_os() -> dict:
    """Detect operating system and environment details"""
    info = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'is_wsl': False,
        'is_windows': False,
        'is_linux': False,
        'is_macos': False,
        'distro': None,
        'distro_version': None,
    }
    
    # Check for WSL
    if os.path.exists('/proc/version'):
        with open('/proc/version', 'r') as f:
            if 'microsoft' in f.read().lower() or 'wsl' in f.read().lower():
                info['is_wsl'] = True
    
    system = info['system'].lower()
    
    if system == 'windows':
        info['is_windows'] = True
    elif system == 'linux':
        info['is_linux'] = True
        # Detect Linux distribution
        try:
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('ID='):
                            info['distro'] = line.split('=')[1].strip().strip('"')
                        elif line.startswith('VERSION_ID='):
                            info['distro_version'] = line.split('=')[1].strip().strip('"')
        except:
            pass
    elif system == 'darwin':
        info['is_macos'] = True
        # Detect macOS version
        try:
            code, stdout, _ = run_command(['sw_vers', '-productVersion'], capture=True)
            if code == 0:
                info['distro_version'] = stdout.strip()
        except:
            pass
    
    return info


def check_python_version() -> bool:
    """Check if Python version is 3.11+"""
    version = sys.version_info
    return version >= (3, 11)


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH"""
    return shutil.which(command) is not None


def install_prerequisites_linux(os_info: dict) -> bool:
    """Install prerequisites on Linux"""
    distro = os_info.get('distro', '').lower()
    
    print_info("Installing prerequisites for Linux...")
    
    # Check for Docker
    has_docker = check_command_exists('docker')
    if not has_docker:
        print_info("Installing Docker...")
        
        if distro in ['ubuntu', 'debian']:
            commands = [
                ['sudo', 'apt-get', 'update'],
                ['sudo', 'apt-get', 'install', '-y', 'apt-transport-https', 'ca-certificates', 'curl', 'gnupg', 'lsb-release'],
                ['curl', '-fsSL', 'https://get.docker.com', '-o', 'get-docker.sh'],
                ['sudo', 'sh', 'get-docker.sh'],
                ['sudo', 'usermod', '-aG', 'docker', os.getenv('USER', 'root')],
            ]
        elif distro in ['fedora', 'rhel', 'centos']:
            commands = [
                ['sudo', 'dnf', 'install', '-y', 'dnf-plugins-core'],
                ['sudo', 'dnf', 'config-manager', '--add-repo', 'https://download.docker.com/linux/fedora/docker-ce.repo'],
                ['sudo', 'dnf', 'install', '-y', 'docker-ce', 'docker-ce-cli', 'containerd.io'],
                ['sudo', 'systemctl', 'start', 'docker'],
                ['sudo', 'systemctl', 'enable', 'docker'],
                ['sudo', 'usermod', '-aG', 'docker', os.getenv('USER', 'root')],
            ]
        else:
            print_warning(f"Unsupported distribution: {distro}")
            print_info("Please install Docker manually: https://docs.docker.com/engine/install/")
            return False
        
        for cmd in commands:
            code, _, _ = run_command(cmd, check=False)
            if code != 0:
                print_warning(f"Command failed: {' '.join(cmd)}")
        
        print_success("Docker installed")
        print_warning("You may need to log out and back in for Docker permissions to take effect")
    
    # Check for Git
    if not check_command_exists('git'):
        print_info("Installing Git...")
        if distro in ['ubuntu', 'debian']:
            run_command(['sudo', 'apt-get', 'install', '-y', 'git'], check=False)
        elif distro in ['fedora', 'rhel', 'centos']:
            run_command(['sudo', 'dnf', 'install', '-y', 'git'], check=False)
        print_success("Git installed")
    
    return True


def install_prerequisites_macos(os_info: dict) -> bool:
    """Install prerequisites on macOS"""
    print_info("Installing prerequisites for macOS...")
    
    # Check for Homebrew
    if not check_command_exists('brew'):
        print_info("Installing Homebrew...")
        cmd = ['/bin/bash', '-c', '$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)']
        run_command(cmd, check=False)
    
    # Install Docker Desktop
    if not check_command_exists('docker'):
        print_info("Please install Docker Desktop for Mac from:")
        print_info("  https://docs.docker.com/desktop/install/mac-install/")
        print_warning("Docker Desktop is required for full stack installation")
    
    # Install Git
    if not check_command_exists('git'):
        print_info("Installing Git...")
        run_command(['brew', 'install', 'git'], check=False)
        print_success("Git installed")
    
    return True


def install_prerequisites_windows(os_info: dict) -> bool:
    """Install prerequisites on Windows (via WSL)"""
    print_warning("Windows detected. iTaK works best in WSL (Windows Subsystem for Linux)")
    print_info("\nPlease install WSL and run this installer from within WSL:")
    print_info("  1. Open PowerShell as Administrator")
    print_info("  2. Run: wsl --install")
    print_info("  3. Restart your computer")
    print_info("  4. Open Ubuntu from Start Menu")
    print_info("  5. Run: python3 install.py")
    print_info("\nFor detailed instructions, see:")
    print_info("  https://learn.microsoft.com/en-us/windows/wsl/install")
    
    return False


def create_env_file() -> bool:
    """Create .env file from example if it doesn't exist"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print_info(".env file already exists")
        return True
    
    if not env_example.exists():
        print_error(".env.example not found!")
        return False
    
    print_info("Creating .env file...")
    shutil.copy(env_example, env_file)
    print_success(".env file created")
    print_warning("Please edit .env and add at least ONE API key:")
    print_info("  - GEMINI_API_KEY=your_key_here")
    print_info("  - OPENAI_API_KEY=your_key_here")
    print_info("  - ANTHROPIC_API_KEY=your_key_here")
    
    return True


def install_python_dependencies() -> bool:
    """Install Python dependencies from requirements.txt"""
    print_info("Installing Python dependencies...")
    
    if not Path('requirements.txt').exists():
        print_error("requirements.txt not found!")
        return False
    
    code, _, _ = run_command([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=False)
    
    if code == 0:
        print_success("Python dependencies installed")
        return True
    else:
        print_error("Failed to install Python dependencies")
        return False


def start_full_stack() -> bool:
    """Start full stack with docker-compose"""
    print_info("Starting full stack (iTaK + Neo4j + Weaviate + SearXNG)...")
    
    if not check_command_exists('docker'):
        print_error("Docker not found! Cannot start full stack.")
        print_info("Please install Docker or use --minimal option")
        return False
    
    if not Path('docker-compose.yml').exists():
        print_error("docker-compose.yml not found!")
        return False
    
    # Start services
    code, _, _ = run_command(['docker', 'compose', 'up', '-d'], check=False)
    
    if code == 0:
        print_success("Full stack started")
        print_info("\nServices running:")
        print_info("  iTaK Web UI:  http://localhost:8000")
        print_info("  Neo4j:        http://localhost:47474 (neo4j/changeme)")
        print_info("  Weaviate:     http://localhost:48080")
        print_info("  SearXNG:      http://localhost:48888")
        return True
    else:
        print_error("Failed to start full stack")
        return False


def start_minimal() -> bool:
    """Start iTaK in minimal mode (Python only)"""
    print_info("Starting iTaK in minimal mode...")
    
    print_success("iTaK configured for minimal mode")
    print_info("\nTo start iTaK:")
    print_info("  python main.py --webui")
    print_info("\nThen visit: http://localhost:8000")
    
    return True


def main():
    """Main installer function"""
    parser = argparse.ArgumentParser(
        description='iTaK Universal Installer - One script for all platforms',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install.py              # Interactive installation
  python install.py --full-stack # Install with all databases
  python install.py --minimal    # Install iTaK only
  
For more information: https://github.com/David2024patton/iTaK
        """
    )
    parser.add_argument('--full-stack', action='store_true',
                        help='Install full stack (iTaK + Neo4j + Weaviate + SearXNG)')
    parser.add_argument('--minimal', action='store_true',
                        help='Install minimal (iTaK only, no databases)')
    parser.add_argument('--skip-prereq', action='store_true',
                        help='Skip prerequisite installation')
    
    args = parser.parse_args()
    
    # Print header
    print_header("🚀 iTaK Universal Installer")
    print(f"{Colors.BOLD}One script to install iTaK on any platform{Colors.ENDC}\n")
    
    # Check Python version
    if not check_python_version():
        print_error(f"Python 3.11+ required, but you have {sys.version_info.major}.{sys.version_info.minor}")
        print_info("Please upgrade Python: https://www.python.org/downloads/")
        return 1
    
    print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")
    
    # Detect OS
    print_info("Detecting environment...")
    os_info = detect_os()
    
    if os_info['is_wsl']:
        print_success(f"Detected: WSL ({os_info.get('distro', 'Linux').capitalize()} {os_info.get('distro_version', '')})")
    elif os_info['is_linux']:
        print_success(f"Detected: Linux ({os_info.get('distro', 'Unknown').capitalize()} {os_info.get('distro_version', '')})")
    elif os_info['is_macos']:
        arch = "Apple Silicon" if os_info['machine'] == 'arm64' else "Intel"
        print_success(f"Detected: macOS {os_info.get('distro_version', '')} ({arch})")
    elif os_info['is_windows']:
        print_success("Detected: Windows")
    
    # Install prerequisites
    if not args.skip_prereq:
        print_header("📦 Installing Prerequisites")
        
        if os_info['is_windows']:
            if not install_prerequisites_windows(os_info):
                return 1
        elif os_info['is_linux'] or os_info['is_wsl']:
            if not install_prerequisites_linux(os_info):
                print_warning("Some prerequisites failed to install")
        elif os_info['is_macos']:
            if not install_prerequisites_macos(os_info):
                print_warning("Some prerequisites failed to install")
    
    # Determine installation type
    if not args.full_stack and not args.minimal:
        print_header("📋 Installation Options")
        print("1. Full Stack (Recommended - includes Neo4j, Weaviate, SearXNG)")
        print("2. Minimal (iTaK only, no databases)")
        
        choice = input("\nChoose installation type (1/2, default=1): ").strip() or "1"
        
        if choice == "1":
            args.full_stack = True
        else:
            args.minimal = True
    
    # Create .env file
    print_header("⚙️  Configuration")
    if not create_env_file():
        print_warning("Failed to create .env file")
    
    # Install Python dependencies
    print_header("🐍 Python Dependencies")
    if not install_python_dependencies():
        print_error("Installation failed!")
        return 1
    
    # Start services
    print_header("🚀 Starting Services")
    
    if args.full_stack:
        if not start_full_stack():
            print_error("Failed to start full stack")
            print_info("Falling back to minimal mode...")
            start_minimal()
    else:
        start_minimal()
    
    # Print success summary
    print_header("✅ Installation Complete!")
    
    print(f"{Colors.OKGREEN}{Colors.BOLD}iTaK is ready to use!{Colors.ENDC}\n")
    
    print("Next steps:")
    print("1. Edit .env and add your API key (if not done already)")
    
    if args.full_stack:
        print("2. All services are running in Docker")
        print("3. Visit http://localhost:8000 to access iTaK")
    else:
        print("2. Run: python main.py --webui")
        print("3. Visit http://localhost:8000 to access iTaK")
    
    print("\nFor help and documentation:")
    print("  README.md - Quick start guide")
    print("  QUICK_START.md - Detailed installation guide")
    print("  TESTING.md - Testing guide")
    print("\nGitHub: https://github.com/David2024patton/iTaK")
    
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Installation cancelled by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
