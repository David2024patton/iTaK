"""
iTaK Response Tool - The only way to break the monologue loop.
When the agent calls this tool, the response is sent to the user.
"""

from tools.base import BaseTool, ToolResult


class ResponseTool(BaseTool):
    """Final response to the user - this breaks the agent loop.

    The agent must call this tool to deliver its final answer.
    Without it, the monologue loop continues indefinitely.
    This is the single most important tool in the system.
    """

    name = "response"
    description = "Send final response to the user. This ends the current task."

    async def execute(self, message: str = "", **kwargs) -> ToolResult:
        """Send the final response and break the loop."""
        if not message:
            message = "Task completed."

        # Run through output guard before delivering to user
        if hasattr(self.agent, 'output_guard') and self.agent.output_guard:
            result = self.agent.output_guard.sanitize(message)
            message = result.sanitized_text

        await self.agent.progress.complete(message[:100])

        return ToolResult(
            output=message,
            break_loop=True,  # This is what stops the monologue
        )
