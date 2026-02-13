"""
iTaK Extension: Task Tracker — Runs at message_loop_start.
Creates a new Task on incoming user requests.
"""


async def execute(agent, **kwargs):
    """Create a task when the user sends a new request."""
    if not hasattr(agent, "task_board") or agent.task_board is None:
        return

    # Only create on the first iteration of a new monologue
    if getattr(agent, "_total_iterations", 0) > 1:
        return

    # Get the last user message
    user_messages = [m for m in agent.history if m.get("role") == "user"]
    if not user_messages:
        return

    last_msg = user_messages[-1].get("content", "")
    if not last_msg or len(last_msg) < 5:
        return

    # Generate a short title (first 60 chars, first sentence)
    title = last_msg.split("\n")[0][:60].strip()
    if len(title) < len(last_msg):
        title += "…"

    source = getattr(agent.context, "adapter_name", "cli")
    task = agent.task_board.create(
        title=title,
        description=last_msg[:500],
        source=source,
    )

    # Store the active task ID so other extensions can reference it
    agent.context.data["active_task_id"] = task.id

    # Auto-start it
    agent.task_board.start(task.id)

    from core.logger import EventType
    agent.logger.log(
        EventType.EXTENSION_FIRED,
        f"task_tracker: created task '{task.id}' — {title[:40]}",
    )
    return task.id
