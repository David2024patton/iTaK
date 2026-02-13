"""
iTaK Extension: Error Classifier — Runs in error_format hook.
Classifies errors by category and severity for the self-healing engine.
"""


async def execute(agent, error: Exception = None, error_message: str = "", **kwargs):
    """Classify an error and annotate it for the self-heal engine."""
    if not error and not error_message:
        return

    if not hasattr(agent, "self_heal") or agent.self_heal is None:
        return

    from core.self_heal import ErrorCategory, ErrorSeverity

    exc = error if error else Exception(error_message)
    classified = agent.self_heal.classify(exc)

    from core.logger import EventType
    agent.logger.log(
        EventType.EXTENSION_FIRED,
        f"error_classifier: {classified.category.value} "
        f"({classified.severity.value}) — {classified.message[:80]}",
    )

    return {
        "category": classified.category.value,
        "severity": classified.severity.value,
        "self_healable": classified.severity != ErrorSeverity.CRITICAL,
    }
