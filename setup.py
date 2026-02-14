#!/usr/bin/env python3
"""
iTaK Interactive Setup - Configure memory and infrastructure.

Asks the user about their Neo4j setup and helps configure it.
Run this after cloning the repo and before first run.

Usage:
    python setup.py
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


# ─── Constants ────────────────────────────────────────────
BOX_WIDTH = 55  # Width of header box content area

# ─── Colour helpers ────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _ok(msg: str) -> str:
    return f"  {GREEN}[✓]{RESET} {msg}"


def _warn(msg: str) -> str:
    return f"  {YELLOW}[!]{RESET} {msg}"


def _info(msg: str) -> str:
    return f"  {CYAN}[i]{RESET} {msg}"


def _header(msg: str) -> str:
    # Truncate message if too long, ensuring it fits within the box
    display_msg = msg[:BOX_WIDTH] if len(msg) > BOX_WIDTH else msg
    padding = max(0, BOX_WIDTH - len(display_msg))
    return f"\n{BOLD}{CYAN}╔═══════════════════════════════════════════════════════════╗{RESET}\n{BOLD}{CYAN}║  {display_msg}{' ' * padding}║{RESET}\n{BOLD}{CYAN}╚═══════════════════════════════════════════════════════════╝{RESET}"


def prompt_yes_no(question: str, default: bool = False) -> bool:
    """Ask a yes/no question and return True/False."""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{question} [{default_str}]: ").strip().lower()
        if not response:
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print(_warn("Please answer 'y' or 'n'"))


def prompt_string(question: str, default: str = "") -> str:
    """Ask for a string value."""
    if default:
        response = input(f"{question} [{default}]: ").strip()
        return response if response else default
    else:
        while True:
            response = input(f"{question}: ").strip()
            if response:
                return response
            print(_warn("This field is required"))


def check_docker() -> bool:
    """Check if Docker is available."""
    return shutil.which("docker") is not None


def setup_config_files():
    """Copy example config files if they don't exist."""
    print(_header("Step 1: Configuration Files"))
    
    # config.json
    if not Path("config.json").exists():
        if Path("config.json.example").exists():
            shutil.copy("config.json.example", "config.json")
            print(_ok("Created config.json from config.json.example"))
        else:
            print(_warn("config.json.example not found - skipping"))
    else:
        print(_info("config.json already exists"))
    
    # .env
    if not Path(".env").exists():
        if Path(".env.example").exists():
            shutil.copy(".env.example", ".env")
            print(_ok("Created .env from .env.example"))
        else:
            print(_warn(".env.example not found - skipping"))
    else:
        print(_info(".env already exists"))


def setup_neo4j():
    """Configure Neo4j setup."""
    print(_header("Step 2: Neo4j Knowledge Graph (Layer 3 Memory)"))
    
    print(_info("Neo4j provides relationship-aware memory for iTaK."))
    print(_info("It stores entities, relationships, and temporal context."))
    print()
    
    use_neo4j = prompt_yes_no("Do you want to use Neo4j for knowledge graph memory?", default=False)
    
    if not use_neo4j:
        print(_info("Skipping Neo4j setup. iTaK will use SQLite memory only."))
        return None
    
    print()
    has_own_neo4j = prompt_yes_no("Do you already have a Neo4j instance running?", default=False)
    
    neo4j_config = {}
    
    if has_own_neo4j:
        # User has their own Neo4j
        print()
        print(_info("Please provide your Neo4j connection details:"))
        neo4j_uri = prompt_string("Neo4j URI", "bolt://localhost:7687")
        neo4j_user = prompt_string("Neo4j username", "neo4j")
        neo4j_password = prompt_string("Neo4j password")
        
        neo4j_config = {
            "uri": neo4j_uri,
            "user": neo4j_user,
            "password": neo4j_password,
            "method": "existing"
        }
        
        print(_ok(f"Will use existing Neo4j at {neo4j_uri}"))
    else:
        # User needs Neo4j installed
        print()
        if check_docker():
            print(_info("Docker is available on your system."))
            use_docker = prompt_yes_no("Install Neo4j using Docker Compose?", default=True)
            
            if use_docker:
                neo4j_password = prompt_string("Set a password for Neo4j", "changeme")
                
                neo4j_config = {
                    "uri": "bolt://localhost:7687",
                    "user": "neo4j",
                    "password": neo4j_password,
                    "method": "docker"
                }
                
                print()
                print(_ok("Neo4j will be installed via Docker Compose"))
                print(_info("Run 'docker compose up -d neo4j' to start Neo4j"))
            else:
                print()
                print(_warn("You'll need to install Neo4j manually."))
                print(_info("Visit: https://neo4j.com/download/"))
                print(_info("After installation, re-run this setup script."))
                return None
        else:
            print(_warn("Docker is not available on your system."))
            print(_info("To use Docker for Neo4j, install Docker first:"))
            print(_info("  - https://docs.docker.com/get-docker/"))
            print()
            manual_install = prompt_yes_no("Do you want to install Neo4j manually?", default=False)
            
            if manual_install:
                print()
                print(_info("Installation instructions:"))
                print(_info("  1. Visit: https://neo4j.com/download/"))
                print(_info("  2. Download and install Neo4j Community Edition"))
                print(_info("  3. Start Neo4j and set a password"))
                print(_info("  4. Re-run this setup script to configure connection"))
                return None
            else:
                print(_info("Skipping Neo4j setup."))
                return None
    
    return neo4j_config


def update_env_file(neo4j_config):
    """Update .env file with Neo4j configuration."""
    if not neo4j_config:
        return
    
    env_path = Path(".env")
    if not env_path.exists():
        print(_warn(".env file not found - skipping update"))
        return
    
    # Read existing .env and detect line ending style
    env_content = env_path.read_text(encoding="utf-8")
    # Detect line ending style (preserve original)
    if "\r\n" in env_content:
        line_sep = "\r\n"
    else:
        line_sep = "\n"
    
    env_lines = env_content.splitlines()
    
    # Update Neo4j variables
    neo4j_vars = {
        "NEO4J_URI": neo4j_config["uri"],
        "NEO4J_PASSWORD": neo4j_config["password"]
    }
    
    updated_lines = []
    updated_vars = set()
    
    for line in env_lines:
        stripped = line.strip()
        if stripped.startswith("NEO4J_URI="):
            updated_lines.append(f"NEO4J_URI={neo4j_vars['NEO4J_URI']}")
            updated_vars.add("NEO4J_URI")
        elif stripped.startswith("NEO4J_PASSWORD="):
            updated_lines.append(f"NEO4J_PASSWORD={neo4j_vars['NEO4J_PASSWORD']}")
            updated_vars.add("NEO4J_PASSWORD")
        else:
            updated_lines.append(line)
    
    # Add missing variables
    for var, value in neo4j_vars.items():
        if var not in updated_vars:
            updated_lines.append(f"{var}={value}")
    
    # Write back with original line ending style
    env_path.write_text(line_sep.join(updated_lines), encoding="utf-8")
    print(_ok("Updated .env with Neo4j configuration"))


def update_config_file(neo4j_config):
    """Update config.json with Neo4j configuration."""
    if not neo4j_config:
        return
    
    config_path = Path("config.json")
    if not config_path.exists():
        print(_warn("config.json not found - skipping update"))
        return
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Update neo4j section
        config["neo4j"] = {
            "uri": "${NEO4J_URI}",
            "user": neo4j_config.get("user", "neo4j"),
            "password": "${NEO4J_PASSWORD}"
        }
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        
        print(_ok("Updated config.json with Neo4j configuration"))
    except Exception as e:
        print(_warn(f"Failed to update config.json: {e}"))


def setup_weaviate():
    """Configure Weaviate setup (optional)."""
    print(_header("Step 3: Weaviate Semantic Search (Layer 4 Memory)"))
    
    print(_info("Weaviate provides semantic vector search for iTaK."))
    print(_info("It's optional and can be added later."))
    print()
    
    use_weaviate = prompt_yes_no("Do you want to configure Weaviate?", default=False)
    
    if not use_weaviate:
        print(_info("Skipping Weaviate setup."))
        return
    
    print()
    print(_info("Weaviate can be run via Docker Compose (recommended)."))
    print(_info("Run 'docker compose up -d weaviate' to start Weaviate."))


def show_next_steps(neo4j_config):
    """Show what to do next."""
    print(_header("Setup Complete!"))
    
    print()
    print(_ok("Configuration files are ready."))
    print()
    
    # Next steps
    print(f"{BOLD}Next steps:{RESET}")
    print()
    print("1. Add your LLM API key to .env:")
    print(f"   {CYAN}GOOGLE_API_KEY=your_key_here{RESET}")
    print()
    
    if neo4j_config and neo4j_config.get("method") == "docker":
        print("2. Start Neo4j with Docker:")
        print(f"   {CYAN}docker compose up -d neo4j{RESET}")
        print()
        print("3. Run diagnostics to verify everything:")
        print(f"   {CYAN}python main.py --doctor{RESET}")
        print()
        print("4. Start iTaK:")
        print(f"   {CYAN}python main.py{RESET}")
    elif neo4j_config and neo4j_config.get("method") == "existing":
        print("2. Run diagnostics to verify Neo4j connection:")
        print(f"   {CYAN}python main.py --doctor{RESET}")
        print()
        print("3. Start iTaK:")
        print(f"   {CYAN}python main.py{RESET}")
    else:
        print("2. Run diagnostics to verify setup:")
        print(f"   {CYAN}python main.py --doctor{RESET}")
        print()
        print("3. Start iTaK:")
        print(f"   {CYAN}python main.py{RESET}")
    
    print()
    print(_info("For help, see docs/getting-started.md"))


def main():
    """Run interactive setup."""
    print()
    print(f"{BOLD}{CYAN}╔═══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║                                                           ║{RESET}")
    print(f"{BOLD}{CYAN}║                   iTaK Interactive Setup                  ║{RESET}")
    print(f"{BOLD}{CYAN}║                                                           ║{RESET}")
    print(f"{BOLD}{CYAN}╚═══════════════════════════════════════════════════════════╝{RESET}")
    print()
    
    # Step 1: Config files
    setup_config_files()
    
    # Step 2: Neo4j
    neo4j_config = setup_neo4j()
    if neo4j_config:
        update_env_file(neo4j_config)
        update_config_file(neo4j_config)
    
    # Step 3: Weaviate (optional)
    setup_weaviate()
    
    # Show next steps
    show_next_steps(neo4j_config)
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(_warn("Setup cancelled by user"))
        sys.exit(1)
    except Exception as e:
        print()
        print(f"{RED}Error: {e}{RESET}")
        sys.exit(1)
