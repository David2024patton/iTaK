"""
iTaK Extension: Task Progress - Runs after tool execution.
Updates the active task's step progress on every tool completion.
"""


async def execute(agent, tool_name: str = "", tool_args: dict = None,
                  result: str = "", **kwargs):
    """Update task progress when a tool completes."""
    if not hasattr(agent, "task_board") or agent.task_board is None:
        return

    task_id = agent.context.data.get("active_task_id")
    if not task_id:
        return

    task = agent.task_board.get(task_id)
    if not task or task.status not in ("in_progress", "review"):
        return

    # Summarize what the tool did
    summary = f"{tool_name}"
    if tool_args:
        # Include key details without leaking secrets
        safe_keys = [k for k in tool_args if k not in ("code", "password", "token")]
        details = ", ".join(f"{k}={str(tool_args[k])[:30]}" for k in safe_keys[:3])
        if details:
            summary += f"({details})"

    # Check if there are steps to advance
    if task.steps and task.current_step < len(task.steps):
        agent.task_board.advance_step(task_id, notes=summary)
    else:
        # No formal steps - just log the tool execution
        task.error_log.append(f"tool: {summary}")
        agent.task_board.update(task)

    return "task_progress_updated"
