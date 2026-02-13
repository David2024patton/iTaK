"""
iTaK Security Scanner — Scans code, skills, and tools for dangerous patterns.
Defense in depth: prevent injection, data exfiltration, and privilege escalation.
"""

import ast
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SecurityScanner:
    """Scans code and skills for dangerous patterns before execution.

    Three scan levels:
    - CRITICAL: Blocks execution immediately (e.g., os.system with user input)
    - WARNING: Flags for review but allows execution
    - INFO: Informational findings for audit trail

    From gameplan §13: Defense in depth, two-store secrets,
    placeholder replacement.
    """

    # Dangerous patterns (regex → severity, description)
    DANGEROUS_PATTERNS: list[tuple[str, str, str]] = [
        # Critical — always block
        (r"os\.system\s*\(", "CRITICAL", "os.system() — use subprocess instead"),
        (r"subprocess\.call\s*\(.+shell\s*=\s*True", "CRITICAL", "subprocess with shell=True — injection risk"),
        (r"eval\s*\(", "CRITICAL", "eval() — arbitrary code execution"),
        (r"exec\s*\(", "CRITICAL", "exec() — arbitrary code execution"),
        (r"__import__\s*\(", "CRITICAL", "__import__() — dynamic import bypass"),
        (r"pickle\.loads?\s*\(", "CRITICAL", "pickle deserialization — arbitrary code execution"),
        (r"yaml\.load\s*\([^)]*\)", "CRITICAL", "yaml.load without SafeLoader — code execution"),
        (r"shutil\.rmtree\s*\(\s*['\"/]", "CRITICAL", "shutil.rmtree on root paths — data loss"),
        (r"rm\s+-rf\s+/", "CRITICAL", "rm -rf / — catastrophic data loss"),

        # Warning — flag but allow
        (r"subprocess\.\w+\s*\(", "WARNING", "subprocess usage — verify arguments"),
        (r"requests\.(get|post|put|delete)\s*\(", "WARNING", "HTTP request — verify URL is expected"),
        (r"open\s*\(.+['\"]w['\"]", "WARNING", "File write operation — verify path"),
        (r"sqlite3\.connect\s*\(", "WARNING", "Direct SQLite access — use memory manager"),
        (r"socket\.\w+\s*\(", "WARNING", "Raw socket — verify network access"),
        (r"ctypes\.\w+", "WARNING", "ctypes usage — low-level system access"),

        # Info — audit trail
        (r"import\s+os", "INFO", "os module imported"),
        (r"import\s+sys", "INFO", "sys module imported"),
        (r"import\s+shutil", "INFO", "shutil module imported"),
    ]

    # Secret patterns — things that should never appear in code/logs
    SECRET_PATTERNS: list[tuple[str, str]] = [
        (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API key"),
        (r"AIza[a-zA-Z0-9_-]{35}", "Google API key"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub personal access token"),
        (r"xoxb-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}", "Slack bot token"),
        (r"[0-9]{17,19}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27}", "Discord bot token"),
        (r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "Private key"),
        (r"(?:password|passwd|pwd)\s*=\s*['\"][^'\"]{4,}", "Hardcoded password"),
        (r"(?:secret|token|key)\s*=\s*['\"][^'\"]{8,}", "Hardcoded secret"),
    ]

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.strict_mode = self.config.get("strict_mode", True)

    def scan_code(self, code: str, source: str = "unknown") -> dict:
        """Scan a code string for dangerous patterns.

        Returns:
            {
                "safe": bool,
                "findings": [{"severity", "pattern", "line", "source"}],
                "secrets_found": [{"type", "line"}],
                "blocked": bool
            }
        """
        findings = []
        secrets = []
        blocked = False

        lines = code.split("\n")

        # Check dangerous patterns
        for pattern, severity, description in self.DANGEROUS_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    finding = {
                        "severity": severity,
                        "pattern": description,
                        "line": i,
                        "line_content": line.strip()[:100],
                        "source": source,
                    }
                    findings.append(finding)
                    if severity == "CRITICAL":
                        blocked = True

        # Check for exposed secrets
        for pattern, secret_type in self.SECRET_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    secrets.append({
                        "type": secret_type,
                        "line": i,
                        "source": source,
                    })
                    blocked = True  # Always block if secrets found

        return {
            "safe": not blocked,
            "findings": findings,
            "secrets_found": secrets,
            "blocked": blocked,
            "source": source,
        }

    def scan_file(self, filepath: str | Path) -> dict:
        """Scan a file for dangerous patterns."""
        filepath = Path(filepath)
        if not filepath.exists():
            return {"safe": True, "findings": [], "secrets_found": [], "blocked": False}

        try:
            content = filepath.read_text(encoding="utf-8")
            return self.scan_code(content, source=str(filepath))
        except Exception as e:
            return {
                "safe": False,
                "findings": [{"severity": "WARNING", "pattern": f"Could not read file: {e}"}],
                "secrets_found": [],
                "blocked": False,
            }

    def scan_directory(self, directory: str | Path, extensions: list[str] | None = None) -> dict:
        """Scan all files in a directory."""
        directory = Path(directory)
        extensions = extensions or [".py", ".js", ".sh", ".md"]

        all_findings = []
        all_secrets = []
        blocked = False

        for ext in extensions:
            for filepath in directory.rglob(f"*{ext}"):
                result = self.scan_file(filepath)
                all_findings.extend(result["findings"])
                all_secrets.extend(result["secrets_found"])
                if result["blocked"]:
                    blocked = True

        return {
            "safe": not blocked,
            "findings": all_findings,
            "secrets_found": all_secrets,
            "blocked": blocked,
            "files_scanned": sum(
                len(list(directory.rglob(f"*{ext}"))) for ext in extensions
            ),
        }

    def scan_python_ast(self, code: str) -> list[dict]:
        """Deep scan Python code using AST analysis."""
        findings = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # Check for dangerous function calls
                if isinstance(node, ast.Call):
                    func_name = self._get_call_name(node)
                    if func_name in ("eval", "exec", "compile", "__import__"):
                        findings.append({
                            "severity": "CRITICAL",
                            "pattern": f"{func_name}() call detected via AST",
                            "line": node.lineno,
                        })

                # Check for dangerous imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ("ctypes", "subprocess"):
                            findings.append({
                                "severity": "WARNING",
                                "pattern": f"import {alias.name} detected via AST",
                                "line": node.lineno,
                            })

                if isinstance(node, ast.ImportFrom):
                    if node.module in ("os", "subprocess", "shutil"):
                        for alias in node.names:
                            if alias.name in ("system", "popen", "rmtree", "call"):
                                findings.append({
                                    "severity": "CRITICAL",
                                    "pattern": f"from {node.module} import {alias.name}",
                                    "line": node.lineno,
                                })

        except SyntaxError:
            pass  # Not valid Python

        return findings

    @staticmethod
    def _get_call_name(node: ast.Call) -> str:
        """Extract the function name from an AST Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def format_report(self, scan_result: dict) -> str:
        """Format a scan result into a human-readable report."""
        lines = ["# Security Scan Report\n"]

        if scan_result["safe"]:
            lines.append("✅ **SAFE** — No critical issues found.\n")
        else:
            lines.append("❌ **BLOCKED** — Critical security issues detected.\n")

        if scan_result["secrets_found"]:
            lines.append("## 🔑 Exposed Secrets\n")
            for s in scan_result["secrets_found"]:
                lines.append(f"- **{s['type']}** on line {s.get('line', '?')}")
            lines.append("")

        critical = [f for f in scan_result["findings"] if f["severity"] == "CRITICAL"]
        warnings = [f for f in scan_result["findings"] if f["severity"] == "WARNING"]
        infos = [f for f in scan_result["findings"] if f["severity"] == "INFO"]

        if critical:
            lines.append("## 🚨 Critical\n")
            for f in critical:
                lines.append(f"- Line {f.get('line', '?')}: {f['pattern']}")
            lines.append("")

        if warnings:
            lines.append("## ⚠️ Warnings\n")
            for f in warnings:
                lines.append(f"- Line {f.get('line', '?')}: {f['pattern']}")
            lines.append("")

        if infos:
            lines.append("## ℹ️ Info\n")
            for f in infos:
                lines.append(f"- Line {f.get('line', '?')}: {f['pattern']}")

        return "\n".join(lines)
