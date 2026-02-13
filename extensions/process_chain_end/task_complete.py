"""
iTaK Extension: Task Complete — Runs at process_chain_end.
Moves the active task to review/done when the process chain completes.
"""


async def execute(agent, **kwargs):
    """Move the active task to done when the agent finishes."""
    if not hasattr(agent, "task_board") or agent.task_board is None:
        return

    task_id = agent.context.data.get("active_task_id")
    if not task_id:
        return

    task = agent.task_board.get(task_id)
    if not task or task.status not in ("in_progress", "review"):
        return

    # If the task has deliverables or screenshots, mark as review
    # Otherwise, mark as done
    if task.deliverables:
        agent.task_board.set_review(task_id)
        status = "review"
    else:
        agent.task_board.complete(task_id)
        status = "done"

    from core.logger import EventType
    agent.logger.log(
        EventType.EXTENSION_FIRED,
        f"task_complete: task '{task_id}' → {status}",
    )

    # Clear active task
    agent.context.data.pop("active_task_id", None)
    return status
