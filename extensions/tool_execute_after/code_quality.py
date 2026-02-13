"""
iTaK Extension: Code Quality Gate - Runs after code_execution tool.
Automatically lints code files after the agent writes them.

Upgraded from stub to full CodeQualityGate integration (Phase 5).
"""

import re
from pathlib import Path


async def execute(agent, tool_name: str = "", tool_args: dict = None,
                  result: str = "", **kwargs):
    """Auto-lint code after the agent writes or modifies files."""
    if tool_name != "code_execution":
        return

    code = (tool_args or {}).get("code", "")
    if not code:
        return

    # Extract file paths from the code (open/write/Path patterns)
    file_patterns = [
        r'open\(["\']([^"\']+)["\']',
        r'Path\(["\']([^"\']+)["\']',
        r'> ([^\s]+\.\w+)',               # shell redirect
        r'cat > ([^\s]+)',
        r'tee ([^\s]+)',
    ]
    
    files_to_lint = set()
    for pattern in file_patterns:
        matches = re.findall(pattern, code)
        for match in matches:
            p = Path(match)
            if p.suffix in {".py", ".js", ".ts", ".jsx", ".tsx", ".sh", ".bash"}:
                files_to_lint.add(str(p))

    if not files_to_lint:
        return

    from core.logger import EventType
    agent.logger.log(
        EventType.EXTENSION_FIRED,
        f"code_quality: linting {len(files_to_lint)} file(s)",
    )

    # Use the CodeQualityGate if available
    try:
        from core.linter import CodeQualityGate
        gate = CodeQualityGate(agent)
        results = await gate.check_files(list(files_to_lint))
        
        failed = [r for r in results if not r.passed]
        if failed:
            report = gate.format_report(results)
            agent.logger.log(
                EventType.WARNING,
                f"code_quality: {len(failed)} file(s) have lint errors",
            )
            return f"LINT_ERRORS:\n{report}"
        else:
            agent.logger.log(
                EventType.SYSTEM,
                f"code_quality: all {len(files_to_lint)} file(s) clean ✅",
            )
            return "lint_passed"
    except ImportError:
        agent.logger.log(
            EventType.WARNING,
            "code_quality: CodeQualityGate not available - skipping",
        )
        return "lint_skipped"
