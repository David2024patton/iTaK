"""
iTaK Extension: Security Scan — Runs after code_execution tool.
Scans generated/written code for dangerous patterns.
"""


async def execute(agent, tool_name: str = "", tool_args: dict = None, result: str = "", **kwargs):
    """Auto-scan code after code execution for security issues."""
    if tool_name != "code_execution":
        return

    code = (tool_args or {}).get("code", "")
    if not code or len(code) < 20:
        return

    # Run security scanner
    try:
        from security.scanner import SecurityScanner
        scanner = SecurityScanner()
        scan_result = scanner.scan_code(code, source="agent_generated")

        if scan_result["blocked"]:
            from core.logger import EventType
            agent.logger.log(
                EventType.SECURITY_WARNING,
                {
                    "event": "code_blocked",
                    "findings": scan_result["findings"][:5],
                    "secrets_found": len(scan_result["secrets_found"]),
                },
            )
            return "SECURITY_BLOCKED"

        if scan_result["findings"]:
            from core.logger import EventType
            agent.logger.log(
                EventType.EXTENSION_FIRED,
                f"security_scan: {len(scan_result['findings'])} findings in agent code",
            )

    except ImportError:
        pass

    return None
