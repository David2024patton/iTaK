"""
iTaK Preflight Check - Auto-check prerequisites at startup.

Validates that required dependencies, configuration, and services are
available before the agent starts. Reports issues clearly and offers
auto-install where possible.
"""

import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path


# fmt: off
REQUIRED_PACKAGES = [
    ("litellm",          "litellm>=1.50.0"),
    ("pydantic",         "pydantic>=2.0.0"),
    ("dotenv",           "python-dotenv>=1.0.0"),
    ("aiosqlite",        "aiosqlite>=0.20.0"),
    ("tiktoken",         "tiktoken>=0.7.0"),
    ("dirtyjson",        "dirtyjson>=1.0.8"),
    ("fastapi",          "fastapi>=0.115.0"),
    ("uvicorn",          "uvicorn[standard]>=0.30.0"),
    ("httpx",            "httpx>=0.27.0"),
]

OPTIONAL_PACKAGES = [
    ("neo4j",            "neo4j>=5.0.0",            "Knowledge graph (Neo4j)"),
    ("weaviate",         "weaviate-client>=4.0.0",   "Semantic search (Weaviate)"),
    ("discord",          "discord.py>=2.4.0",        "Discord adapter"),
    ("telegram",         "python-telegram-bot>=21.0", "Telegram adapter"),
    ("slack_bolt",       "slack-bolt>=1.20.0",       "Slack adapter"),
    ("playwright",       "playwright>=1.48.0",       "Browser agent"),
    ("structlog",        "structlog>=24.0.0",        "Structured logging"),
]
# fmt: on


class PreflightResult:
    """Result of a preflight check."""

    def __init__(self):
        self.passed: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.installed: list[str] = []

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        lines = []
        lines.append("=" * 50)
        lines.append("  iTaK Preflight Check")
        lines.append("=" * 50)

        if self.installed:
            lines.append("")
            lines.append(f"  Auto-installed {len(self.installed)} packages:")
            for pkg in self.installed:
                lines.append(f"    + {pkg}")

        if self.passed:
            lines.append("")
            lines.append(f"  Passed: {len(self.passed)}")
            for item in self.passed:
                lines.append(f"    OK  {item}")

        if self.warnings:
            lines.append("")
            lines.append(f"  Warnings: {len(self.warnings)}")
            for item in self.warnings:
                lines.append(f"    !!  {item}")

        if self.errors:
            lines.append("")
            lines.append(f"  Errors: {len(self.errors)}")
            for item in self.errors:
                lines.append(f"    XX  {item}")

        lines.append("")
        lines.append("=" * 50)
        status = "READY" if self.ok else "BLOCKED"
        lines.append(f"  Status: {status}")
        lines.append("=" * 50)
        return "\n".join(lines)


def _try_import(module_name: str) -> bool:
    """Check if a Python module is importable."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def _pip_install(package: str) -> bool:
    """Install a package with pip. Returns True on success."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package, "-q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def run_preflight(config: dict | None = None, auto_install: bool = True) -> PreflightResult:
    """Run all preflight checks.

    Args:
        config: The loaded config.json dict (or None to skip config checks).
        auto_install: If True, attempt to pip install missing required packages.

    Returns:
        PreflightResult with status of all checks.
    """
    result = PreflightResult()

    # ------------------------------------------------------------------
    # 1. Python version
    # ------------------------------------------------------------------
    py_version = sys.version_info
    if py_version >= (3, 11):
        result.passed.append(f"Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        result.errors.append(
            f"Python 3.11+ required, found {py_version.major}.{py_version.minor}"
        )

    # ------------------------------------------------------------------
    # 2. Required packages
    # ------------------------------------------------------------------
    for module_name, pip_name in REQUIRED_PACKAGES:
        if _try_import(module_name):
            result.passed.append(f"Package: {module_name}")
        elif auto_install:
            if _pip_install(pip_name):
                result.installed.append(pip_name)
                result.passed.append(f"Package: {module_name} (auto-installed)")
            else:
                result.errors.append(
                    f"Missing required package: {pip_name}  -->  pip install {pip_name}"
                )
        else:
            result.errors.append(
                f"Missing required package: {pip_name}  -->  pip install {pip_name}"
            )

    # ------------------------------------------------------------------
    # 3. Optional packages (warn only)
    # ------------------------------------------------------------------
    for module_name, pip_name, feature in OPTIONAL_PACKAGES:
        if _try_import(module_name):
            result.passed.append(f"Package: {module_name} ({feature})")
        else:
            result.warnings.append(
                f"{feature} unavailable - install {pip_name}"
            )

    # ------------------------------------------------------------------
    # 4. Config file
    # ------------------------------------------------------------------
    config_path = Path("config.json")
    if config_path.exists():
        result.passed.append("config.json found")
    else:
        example = Path("config.json.example")
        if example.exists():
            result.errors.append(
                "config.json missing - copy config.json.example to config.json"
            )
        else:
            result.errors.append("config.json missing - create from docs/config.md")

    # ------------------------------------------------------------------
    # 5. API keys
    # ------------------------------------------------------------------
    env_path = Path(".env")
    if env_path.exists():
        result.passed.append(".env file found")
    else:
        result.warnings.append(".env file not found - API keys may be missing")

    has_any_key = any(
        os.environ.get(key)
        for key in [
            "GOOGLE_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENROUTER_API_KEY",
            "GROQ_API_KEY",
        ]
    )
    if has_any_key:
        result.passed.append("At least one LLM API key configured")
    elif config:
        # Check config for hardcoded keys (not recommended but valid)
        chat_model = config.get("models", {}).get("chat", {})
        if chat_model.get("api_key", "").startswith("$"):
            result.errors.append(
                "No LLM API key found - add at least one to .env"
            )
        else:
            result.passed.append("LLM API key found in config")
    else:
        result.warnings.append("Cannot verify API keys - .env or env vars may be set at runtime")

    # ------------------------------------------------------------------
    # 6. External tools
    # ------------------------------------------------------------------
    if shutil.which("git"):
        result.passed.append("Git available")
    else:
        result.warnings.append("Git not found - version control unavailable")

    if shutil.which("docker"):
        result.passed.append("Docker available")
    else:
        result.warnings.append("Docker not found - sandbox mode unavailable")

    # ------------------------------------------------------------------
    # 7. Data directories
    # ------------------------------------------------------------------
    for dirname in ["data", "memory", "logs"]:
        dirpath = Path(dirname)
        if not dirpath.exists():
            dirpath.mkdir(parents=True, exist_ok=True)
            result.passed.append(f"Created directory: {dirname}/")
        else:
            result.passed.append(f"Directory exists: {dirname}/")

    return result


if __name__ == "__main__":
    # Run standalone: python -m core.preflight
    r = run_preflight()
    print(r.summary())
    sys.exit(0 if r.ok else 1)
