"""
iTaK Tool: delegate_task — Spawn a sub-agent to handle a specific task.
Allows the main agent to parallelize work.
"""

import json

from tools.base import BaseTool, ToolResult


class DelegateTaskTool(BaseTool):
    """Delegate a task to a sub-agent for parallel execution.

    The sub-agent runs independently with access to a subset of tools
    and reports results back. Use this for complex multi-step tasks
    that can be broken into independent work items.
    """

    name = "delegate_task"
    description = "Spawn a sub-agent to work on a specific task in parallel"

    async def execute(self, **kwargs) -> ToolResult:
        task = kwargs.get("task", "")
        allowed_tools = kwargs.get("tools", None)
        max_iterations = kwargs.get("max_iterations", 10)
        wait = kwargs.get("wait", True)

        if not task:
            return ToolResult(output="Error: 'task' is required.", error=True)

        # Get or create the sub-agent manager
        if not hasattr(self.agent, "sub_agents"):
            from core.sub_agent import SubAgentManager
            self.agent.sub_agents = SubAgentManager(self.agent)

        # Spawn the sub-agent
        sub = await self.agent.sub_agents.spawn(
            task=task,
            allowed_tools=allowed_tools,
            max_iterations=max_iterations,
        )

        if wait:
            # Wait for the result
            result = await self.agent.sub_agents.run(sub.agent_id)
            return ToolResult(
                output=json.dumps({
                    "agent_id": sub.agent_id,
                    "status": sub.status,
                    "iterations": sub.iterations,
                    "result": result,
                })
            )
        else:
            # Fire and forget — agent can check status later
            import asyncio
            asyncio.create_task(self.agent.sub_agents.run(sub.agent_id))
            return ToolResult(
                output=json.dumps({
                    "agent_id": sub.agent_id,
                    "status": "running",
                    "message": "Sub-agent spawned. Check status with delegate_task status.",
                })
            )
