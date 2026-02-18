"""
iTaK Security Scanner - Scans code, skills, and tools for dangerous patterns.
Defense in depth: prevent injection, data exfiltration, and privilege escalation.
"""

import ast
import logging
import re
from pathlib import Path

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

    # Dangerous patterns (regex → severity, description, category)
    DANGEROUS_PATTERNS: list[tuple[str, str, str, str]] = [
        # Critical - always block
        (r"os\.system\s*\(", "CRITICAL", "os.system() - use subprocess instead", "command_execution"),
        (r"subprocess\.call\s*\(.+shell\s*=\s*True", "CRITICAL", "subprocess with shell=True - injection risk", "command_execution"),
        (r"eval\s*\(", "CRITICAL", "eval() - arbitrary code execution", "code_execution"),
        (r"exec\s*\(", "CRITICAL", "exec() - arbitrary code execution", "code_execution"),
        (r"__import__\s*\(", "CRITICAL", "__import__() - dynamic import bypass", "code_execution"),
        (r"pickle\.loads?\s*\(", "CRITICAL", "pickle deserialization - arbitrary code execution", "deserialization"),
        (r"yaml\.load\s*\([^)]*\)", "CRITICAL", "yaml.load without SafeLoader - code execution", "deserialization"),
        (r"shutil\.rmtree\s*\(\s*['\"/]", "CRITICAL", "shutil.rmtree on root paths - data loss", "filesystem"),
        (r"rm\s+-rf\s+/", "CRITICAL", "rm -rf / - catastrophic data loss", "filesystem"),

        # Warning - flag but allow
        (r"subprocess\.\w+\s*\(", "WARNING", "subprocess usage - verify arguments", "process"),
        (r"requests\.(get|post|put|delete)\s*\(", "WARNING", "HTTP request - verify URL is expected", "network"),
        (r"open\s*\(.+['\"]w['\"]", "WARNING", "File write operation - verify path", "filesystem"),
        (r"sqlite3\.connect\s*\(", "WARNING", "Direct SQLite access - use memory manager", "database"),
        (r"socket\.\w+\s*\(", "WARNING", "Raw socket - verify network access", "network"),
        (r"ctypes\.\w+", "WARNING", "ctypes usage - low-level system access", "system"),

        # Info - audit trail
        (r"import\s+os", "INFO", "os module imported", "audit"),
        (r"import\s+sys", "INFO", "sys module imported", "audit"),
        (r"import\s+shutil", "INFO", "shutil module imported", "audit"),
    ]

    # Secret patterns - things that should never appear in code/logs
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

    SKILL_INJECTION_PATTERNS: list[tuple[str, str, str, str]] = [
        (r"ignore\s+all\s+previous\s+instructions", "CRITICAL", "Prompt-injection pattern: instruction override", "prompt_injection"),
        (r"reveal\s+all\s+secrets", "CRITICAL", "Prompt-injection pattern: secret exfiltration", "data_exfiltration"),
        (r"send\s+credentials\s+to", "CRITICAL", "Prompt-injection pattern: credential exfiltration", "data_exfiltration"),
        (r"disable\s+security", "WARNING", "Security bypass language", "security_bypass"),
        (r"run\s+without\s+confirmation", "WARNING", "Unsafe execution guidance", "unsafe_execution"),
    ]

    RISK_WEIGHTS: dict[str, int] = {
        "CRITICAL": 40,
        "WARNING": 10,
        "INFO": 1,
        "SECRET": 50,
    }

    REQUIRED_SKILL_SECTIONS: list[str] = [
        "## When to Use",
        "## Steps",
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
        for pattern, severity, description, category in self.DANGEROUS_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    finding = {
                        "severity": severity,
                        "pattern": description,
                        "category": category,
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

        risk_summary = self._build_risk_summary(findings, secrets, blocked)

        return {
            "safe": not blocked,
            "findings": findings,
            "secrets_found": secrets,
            "blocked": blocked,
            "source": source,
            "severity_counts": risk_summary["severity_counts"],
            "category_counts": risk_summary["category_counts"],
            "risk_score": risk_summary["risk_score"],
            "risk_level": risk_summary["risk_level"],
        }

    def scan_file(self, filepath: str | Path) -> dict:
        """Scan a file for dangerous patterns."""
        filepath = Path(filepath)
        if not filepath.exists():
            return {
                "safe": True,
                "findings": [],
                "secrets_found": [],
                "blocked": False,
                "severity_counts": {"CRITICAL": 0, "WARNING": 0, "INFO": 0, "SECRETS": 0},
                "category_counts": {},
                "risk_score": 0,
                "risk_level": "LOW",
            }

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

        risk_summary = self._build_risk_summary(all_findings, all_secrets, blocked)

        return {
            "safe": not blocked,
            "findings": all_findings,
            "secrets_found": all_secrets,
            "blocked": blocked,
            "severity_counts": risk_summary["severity_counts"],
            "category_counts": risk_summary["category_counts"],
            "risk_score": risk_summary["risk_score"],
            "risk_level": risk_summary["risk_level"],
            "files_scanned": sum(
                len(list(directory.rglob(f"*{ext}"))) for ext in extensions
            ),
        }

    def _build_risk_summary(self, findings: list[dict], secrets: list[dict], blocked: bool) -> dict:
        """Build normalized severity and risk metadata for scan outputs."""
        severity_counts = {
            "CRITICAL": 0,
            "WARNING": 0,
            "INFO": 0,
            "SECRETS": len(secrets),
        }
        category_counts: dict[str, int] = {}

        for finding in findings:
            sev = str(finding.get("severity", "INFO")).upper()
            if sev not in severity_counts:
                severity_counts[sev] = 0
            severity_counts[sev] += 1

            cat = finding.get("category") or "uncategorized"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        risk_score = (
            severity_counts.get("CRITICAL", 0) * self.RISK_WEIGHTS["CRITICAL"]
            + severity_counts.get("WARNING", 0) * self.RISK_WEIGHTS["WARNING"]
            + min(severity_counts.get("INFO", 0), 25) * self.RISK_WEIGHTS["INFO"]
            + severity_counts.get("SECRETS", 0) * self.RISK_WEIGHTS["SECRET"]
        )

        if blocked:
            risk_score = max(risk_score, 85)
        risk_score = min(risk_score, 100)

        if risk_score >= 85:
            risk_level = "CRITICAL"
        elif risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "risk_score": risk_score,
            "risk_level": risk_level,
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
            lines.append("✅ **SAFE** - No critical issues found.\n")
        else:
            lines.append("❌ **BLOCKED** - Critical security issues detected.\n")

        risk_level = scan_result.get("risk_level")
        risk_score = scan_result.get("risk_score")
        if risk_level is not None and risk_score is not None:
            lines.append(f"Risk: **{risk_level}** ({risk_score}/100)\n")

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

    def validate_skill_markdown(self, content: str) -> dict:
        """Validate SKILL.md structure for required sections."""
        errors: list[str] = []
        text = content or ""
        if not text.strip():
            errors.append("Skill file is empty")
        if not text.lstrip().startswith("# Skill"):
            errors.append("Missing '# Skill' heading")

        for section in self.REQUIRED_SKILL_SECTIONS:
            if section not in text:
                errors.append(f"Missing required section: {section}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    def scan_skill_markdown(self, content: str, source: str = "skill") -> dict:
        """Scan skill markdown for prompt-injection and unsafe guidance patterns."""
        findings: list[dict] = []
        blocked = False
        lines = (content or "").splitlines()

        for pattern, severity, description, category in self.SKILL_INJECTION_PATTERNS:
            regex = re.compile(pattern, re.IGNORECASE)
            for idx, line in enumerate(lines, 1):
                if regex.search(line):
                    findings.append({
                        "severity": severity,
                        "pattern": description,
                        "category": category,
                        "line": idx,
                        "line_content": line.strip()[:120],
                        "source": source,
                    })
                    if severity == "CRITICAL":
                        blocked = True

        risk_summary = self._build_risk_summary(findings, [], blocked)

        return {
            "safe": not blocked,
            "blocked": blocked,
            "findings": findings,
            "source": source,
            "severity_counts": risk_summary["severity_counts"],
            "category_counts": risk_summary["category_counts"],
            "risk_score": risk_summary["risk_score"],
            "risk_level": risk_summary["risk_level"],
        }
