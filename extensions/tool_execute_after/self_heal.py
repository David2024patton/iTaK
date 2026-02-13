"""
iTaK Extension: Self-Heal - Runs after tool execution.
Catches tool failures and routes them to the SelfHealEngine.
"""


async def execute(agent, tool_name: str = "", tool_args: dict = None,
                  result: str = "", error: Exception = None, **kwargs):
    """If a tool failed, try to self-heal before reporting to the user."""
    # Only act on actual failures
    if error is None:
        return

    if not hasattr(agent, "self_heal") or agent.self_heal is None:
        return

    from core.logger import EventType
    agent.logger.log(
        EventType.EXTENSION_FIRED,
        f"self_heal: attempting recovery for {tool_name}",
    )

    # Run the healing pipeline (no retry_fn - the agent loop will retry)
    heal_result = await agent.self_heal.heal(
        exc=error,
        tool_name=tool_name,
        tool_args=tool_args or {},
    )

    if heal_result["healed"]:
        agent.logger.log(
            EventType.SYSTEM,
            f"self_heal: SUCCESS - {heal_result['message']}",
        )
        return heal_result["message"]
    else:
        agent.logger.log(
            EventType.ERROR,
            f"self_heal: FAILED - {heal_result['message']}",
        )
        return f"SELF_HEAL_FAILED: {heal_result['message']}"
