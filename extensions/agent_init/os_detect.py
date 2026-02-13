"""
iTaK Extension: OS Detection — Runs on agent_init.
Detects the host OS and stores it in memory.
"""


async def execute(agent, **kwargs):
    """Detect the host and sandbox operating systems."""
    import platform

    os_info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }

    # Store OS info in agent context
    agent.context.data["os_info"] = os_info

    # Log it
    from core.logger import EventType
    agent.logger.log(EventType.SYSTEM, f"OS detected: {os_info['system']} {os_info['release']}")

    return os_info
