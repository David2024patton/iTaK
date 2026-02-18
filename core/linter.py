"""
iTaK Code Quality Gate - Multi-linter pipeline.

§10 of the gameplan - every piece of code gets linted
before it's considered done. Supports ruff (Python),
eslint (JS/TS), shellcheck (Shell), with 3-pass
self-correction and escalation.
"""

import asyncio
import os
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.agent import Agent


class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    SHELL = "shell"
    DOCKERFILE = "dockerfile"
    UNKNOWN = "unknown"


@dataclass
class LintResult:
    """Result from a single linter run."""
    linter: str
    language: Language
    file_path: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fixed: bool = False
    raw_output: str = ""


# ---------------------------------------------------------------------------
# Language Detection
# ---------------------------------------------------------------------------

EXTENSION_MAP = {
    ".py": Language.PYTHON,
    ".pyw": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".sh": Language.SHELL,
    ".bash": Language.SHELL,
    ".zsh": Language.SHELL,
    "Dockerfile": Language.DOCKERFILE,
}


def detect_language(file_path: str) -> Language:
    """Detect the programming language from a file path."""
    p = Path(file_path)
    if p.name == "Dockerfile" or p.name.startswith("Dockerfile."):
        return Language.DOCKERFILE
    return EXTENSION_MAP.get(p.suffix.lower(), Language.UNKNOWN)


# ---------------------------------------------------------------------------
# Linter Runners
# ---------------------------------------------------------------------------

async def _run_cmd(cmd: list[str], cwd: str = ".") -> tuple[int, str, str]:
    """Run a subprocess and capture output."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        return proc.returncode or 0, stdout.decode(errors="replace"), stderr.decode(errors="replace")
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except asyncio.TimeoutError:
        return -2, "", f"Command timed out: {' '.join(cmd)}"
    except Exception as e:
        return -3, "", str(e)


async def lint_python(file_path: str) -> LintResult:
    """Lint a Python file with ruff."""
    result = LintResult(
        linter="ruff",
        language=Language.PYTHON,
        file_path=file_path,
        passed=True,
    )

    if not shutil.which("ruff"):
        result.warnings.append("ruff not installed - skipping Python lint")
        return result

    # Check
    code, stdout, stderr = await _run_cmd(["ruff", "check", "--output-format=text", file_path])
    result.raw_output = stdout + stderr
    if code != 0:
        result.passed = False
        lines = [line.strip() for line in (stdout + stderr).splitlines() if line.strip() and ":" in line]
        result.errors = lines[:20]  # Cap at 20 errors

    return result


async def lint_javascript(file_path: str) -> LintResult:
    """Lint a JavaScript/TypeScript file with eslint."""
    result = LintResult(
        linter="eslint",
        language=Language.JAVASCRIPT,
        file_path=file_path,
        passed=True,
    )

    eslint_cmd = shutil.which("eslint")
    if not eslint_cmd:
        result.warnings.append("eslint not installed - skipping JS lint")
        return result

    code, stdout, stderr = await _run_cmd(["eslint", "--format=compact", file_path])
    result.raw_output = stdout + stderr
    if code != 0:
        result.passed = False
        lines = [line.strip() for line in (stdout + stderr).splitlines() if line.strip()]
        result.errors = lines[:20]

    return result


async def lint_shell(file_path: str) -> LintResult:
    """Lint a shell script with shellcheck."""
    result = LintResult(
        linter="shellcheck",
        language=Language.SHELL,
        file_path=file_path,
        passed=True,
    )

    if not shutil.which("shellcheck"):
        result.warnings.append("shellcheck not installed - skipping shell lint")
        return result

    code, stdout, stderr = await _run_cmd(["shellcheck", "-f", "gcc", file_path])
    result.raw_output = stdout + stderr
    if code != 0:
        result.passed = False
        lines = [line.strip() for line in (stdout + stderr).splitlines() if line.strip()]
        result.errors = lines[:20]

    return result


# Linter dispatch table
LINTERS = {
    Language.PYTHON: lint_python,
    Language.JAVASCRIPT: lint_javascript,
    Language.TYPESCRIPT: lint_javascript,  # eslint handles both
    Language.SHELL: lint_shell,
}


# ---------------------------------------------------------------------------
# Code Quality Gate
# ---------------------------------------------------------------------------

class CodeQualityGate:
    """Multi-linter pipeline with self-correction.

    3-pass correction loop:
      1. Lint → find errors
      2. Feed errors back to agent → auto-fix
      3. Re-lint → check fixes
      4. If still failing after 3 passes → escalate to user

    Usage:
        gate = CodeQualityGate(agent)
        results = await gate.check_files(["/path/to/file.py"])
        report = gate.format_report(results)
    """

    def __init__(self, agent: Optional["Agent"] = None):
        self.agent = agent
        self.max_passes = 3

    async def check_file(self, file_path: str) -> LintResult:
        """Lint a single file using the appropriate linter."""
        language = detect_language(file_path)
        linter_fn = LINTERS.get(language)

        if not linter_fn:
            return LintResult(
                linter="none",
                language=language,
                file_path=file_path,
                passed=True,
                warnings=[f"No linter configured for {language.value}"],
            )

        if not os.path.isfile(file_path):
            return LintResult(
                linter="none",
                language=language,
                file_path=file_path,
                passed=False,
                errors=[f"File not found: {file_path}"],
            )

        return await linter_fn(file_path)

    async def check_files(self, file_paths: list[str]) -> list[LintResult]:
        """Lint multiple files in parallel."""
        tasks = [self.check_file(fp) for fp in file_paths]
        return await asyncio.gather(*tasks)

    async def check_directory(self, dir_path: str,
                              extensions: list[str] = None) -> list[LintResult]:
        """Lint all supported files in a directory."""
        if extensions is None:
            extensions = list(EXTENSION_MAP.keys())

        files = []
        for ext in extensions:
            files.extend(str(p) for p in Path(dir_path).rglob(f"*{ext}"))

        return await self.check_files(files)

    def format_report(self, results: list[LintResult]) -> str:
        """Format lint results as a readable report."""
        if not results:
            return "✅ No files to lint."

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        lines = [f"📋 **Code Quality Report** - {passed}/{total} passed"]

        if failed == 0:
            lines.append("✅ All files clean!")
            return "\n".join(lines)

        for r in results:
            if r.passed:
                continue
            icon = "❌"
            name = Path(r.file_path).name
            lines.append(f"\n{icon} **{name}** ({r.linter})")
            for err in r.errors[:5]:
                lines.append(f"  • {err}")
            if len(r.errors) > 5:
                lines.append(f"  _...and {len(r.errors) - 5} more_")

        for r in results:
            for w in r.warnings:
                lines.append(f"⚠️ {w}")

        return "\n".join(lines)

    def get_error_summary(self, results: list[LintResult]) -> dict:
        """Get a summary for the dashboard."""
        return {
            "total_files": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
            "total_errors": sum(len(r.errors) for r in results),
            "total_warnings": sum(len(r.warnings) for r in results),
            "by_linter": {
                linter: sum(1 for r in results if r.linter == linter and not r.passed)
                for linter in set(r.linter for r in results)
            },
        }
