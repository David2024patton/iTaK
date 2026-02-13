"""
iTaK Extension: Cost Tracking — Runs after every LLM call.
Logs token usage and cost per model for budget tracking.
"""


async def execute(agent, tool_name: str = "", result: str = "", **kwargs):
    """Track token usage and cost after LLM calls."""
    # Get cost data from the most recent LLM call
    if not hasattr(agent, "_last_llm_meta"):
        return

    meta = agent._last_llm_meta
    tokens = meta.get("tokens_used", 0)
    cost = meta.get("cost_usd", 0.0)
    model = meta.get("model", "unknown")

    if tokens == 0:
        return

    # Log to logger
    from core.logger import EventType
    agent.logger.log(
        EventType.TOKEN_USAGE,
        {
            "model": model,
            "tokens": tokens,
            "cost_usd": cost,
        },
        tokens_used=tokens,
        cost_usd=cost,
    )

    # Update rate limiter
    if hasattr(agent, "rate_limiter") and agent.rate_limiter:
        agent.rate_limiter.record(category=model, cost_usd=cost)
