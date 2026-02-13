"""
iTaK Extension: Auto-Remember — Runs at end of message loop.
Detects "remember this" triggers and auto-saves to memory.
"""


async def execute(agent, **kwargs):
    """Check if the conversation needs auto-remembering."""
    if not agent.history:
        return

    # Check last user message for remember triggers
    last_messages = [m for m in agent.history[-3:] if m.get("role") == "user"]
    if not last_messages:
        return

    last_msg = last_messages[-1].get("content", "").lower()

    # Trigger phrases
    remember_triggers = [
        "remember this",
        "remember that",
        "save this",
        "store this",
        "don't forget",
        "note this",
        "keep in mind",
    ]

    forget_triggers = [
        "forget this",
        "forget that",
        "delete this memory",
        "remove this",
    ]

    for trigger in remember_triggers:
        if trigger in last_msg:
            # The agent should handle this via tool call,
            # but this acts as a safety net
            from core.logger import EventType
            agent.logger.log(
                EventType.EXTENSION_FIRED,
                f"auto_remember: trigger detected '{trigger}'",
            )
            return "remember_triggered"

    for trigger in forget_triggers:
        if trigger in last_msg:
            from core.logger import EventType
            agent.logger.log(
                EventType.EXTENSION_FIRED,
                f"auto_remember: forget trigger detected '{trigger}'",
            )
            return "forget_triggered"
