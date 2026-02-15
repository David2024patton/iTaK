#!/usr/bin/env python3
"""
iTaK universal installer (single script, cross-platform).
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent


def detect_platform() -> tuple[str, bool]:
    system = platform.system().lower()
    release = platform.release().lower()
    is_wsl = system == "linux" and ("microsoft" in release or "wsl" in release)
    if system == "darwin":
        return "macos", False
    if system == "windows":
        return "windows", False
    return "linux", is_wsl


def has_command(name: str) -> bool:
    return shutil.which(name) is not None


def run_command(command: list[str], *, check: bool = True) -> bool:
    print(f"→ {' '.join(command)}")
    try:
        subprocess.run(command, check=check)
        return True
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"  Failed: {exc}")
        return False


def install_prerequisite(prerequisite: str, os_name: str) -> bool:
    installers: dict[tuple[str, str], list[str]] = {
        ("linux", "git"): ["sudo", "apt-get", "install", "-y", "git"],
        ("linux", "docker"): ["sudo", "apt-get", "install", "-y", "docker.io"],
        ("macos", "git"): ["brew", "install", "git"],
        ("macos", "docker"): ["brew", "install", "--cask", "docker"],
        ("windows", "git"): ["winget", "install", "--id", "Git.Git", "-e"],
        ("windows", "docker"): ["winget", "install", "--id", "Docker.DockerDesktop", "-e"],
    }
    command = installers.get((os_name, prerequisite))
    if not command:
        print(f"⚠ No automated installer configured for {prerequisite} on {os_name}.")
        return False
    return run_command(command)


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = " [Y/n]: " if default else " [y/N]: "
    answer = input(prompt + suffix).strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes"}


def ensure_bootstrap_files() -> None:
    env_target = REPO_ROOT / ".env"
    config_target = REPO_ROOT / "config.json"
    if not env_target.exists():
        shutil.copy(REPO_ROOT / ".env.example", env_target)
        print("✓ Created .env from .env.example")
    if not config_target.exists():
        shutil.copy(REPO_ROOT / "config.json.example", config_target)
        print("✓ Created config.json from config.json.example")


def docker_services_to_start(use_own_databases: bool, use_own_searxng: bool) -> list[str]:
    services: list[str] = []
    if not use_own_databases:
        services.extend(["neo4j", "weaviate"])
    if not use_own_searxng:
        services.append("searxng")
    return services


def main() -> int:
    os_name, is_wsl = detect_platform()
    print("=== iTaK Universal Installer ===")
    print(f"Detected OS: {os_name}{' (WSL)' if is_wsl else ''}")

    ensure_bootstrap_files()

    prerequisites = ["git", "docker"]
    missing = [name for name in prerequisites if not has_command(name)]
    if missing:
        print(f"Missing prerequisites: {', '.join(missing)}")
        for prerequisite in missing:
            if ask_yes_no(f"Install missing prerequisite '{prerequisite}' now?", default=True):
                install_prerequisite(prerequisite, os_name)
    else:
        print("✓ Prerequisites detected (git, docker)")

    use_own_databases = ask_yes_no("Do you have your own databases (Neo4j/Weaviate)?", default=False)
    use_own_searxng = ask_yes_no("Do you have your own SearXNG server?", default=False)
    services = docker_services_to_start(use_own_databases, use_own_searxng)

    if services:
        if not has_command("docker"):
            print("⚠ Docker is required to auto-install Neo4j/Weaviate/SearXNG.")
        else:
            print(f"Starting Docker services: {', '.join(services)}")
            run_command(["docker", "compose", "up", "-d", *services], check=False)
    else:
        print("✓ Using your existing databases and SearXNG server.")

    print("Installing Python dependencies...")
    run_command([sys.executable, "-m", "pip", "install", "-r", str(REPO_ROOT / "requirements.txt")], check=False)

    print("\nInstaller complete.")
    print("Next steps:")
    print("1) Add your API key(s) to .env")
    print("2) Run: python main.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
