"""
iTaK Sub-Agent - Spawnable child agents for task delegation.
The main agent can create specialized sub-agents for complex workflows.
"""

import asyncio
import json
import logging
import uuid
from typing import TYPE_CHECKING, Any, Optional

# Optional import for better JSON parsing
try:
    import dirtyjson
    HAS_DIRTYJSON = True
except ImportError:
    HAS_DIRTYJSON = False

if TYPE_CHECKING:
    from core.agent import Agent

logger = logging.getLogger(__name__)


class SubAgent:
    """A lightweight child agent spawned by the main agent.

    Sub-agents:
    - Inherit the parent's model router and memory
    - Have their own conversation history
    - Can use a subset of tools
    - Report results back to the parent
    - Support parallel execution
    """

    def __init__(
        self,
        parent: "Agent",
        task: str,
        agent_id: str | None = None,
        allowed_tools: list[str] | None = None,
        system_prompt_override: str | None = None,
        max_iterations: int = 15,
    ):
        self.parent = parent
        self.task = task
        self.agent_id = agent_id or f"sub-{uuid.uuid4().hex[:8]}"
        self.allowed_tools = allowed_tools
        self.system_prompt_override = system_prompt_override
        self.max_iterations = max_iterations

        # Sub-agent state
        self.history: list[dict] = []
        self.result: str = ""
        self.status: str = "pending"  # pending, running, complete, error
        self.iterations: int = 0

    async def run(self) -> str:
        """Execute the sub-agent's task and return the result."""
        self.status = "running"
        logger.info(f"Sub-agent {self.agent_id} starting: {self.task[:80]}")

        try:
            # Build sub-agent system prompt
            system_prompt = self.system_prompt_override or self._build_system_prompt()

            # Initialize history
            self.history = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.task},
            ]

            # Run the monologue loop (similar to parent but limited)
            for i in range(self.max_iterations):
                self.iterations = i + 1

                # Get LLM response
                response = await self.parent.model_router.chat(
                    self.history,
                    model_type="utility",  # Sub-agents use cheap model
                )

                if not response:
                    break

                # Parse for tool calls
                tool_calls = self._parse_tool_calls(response)

                if not tool_calls:
                    # Plain text response - we're done
                    self.result = response
                    break

                self.history.append({"role": "assistant", "content": response})

                # Execute tools
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("arguments", {})

                    # Check allowed tools
                    if self.allowed_tools and tool_name not in self.allowed_tools:
                        self.history.append({
                            "role": "tool",
                            "content": f"Tool '{tool_name}' is not allowed for this sub-agent.",
                        })
                        continue

                    # Check for response tool (breaks loop)
                    if tool_name == "response":
                        self.result = tool_args.get("text", tool_args.get("message", ""))
                        self.status = "complete"
                        return self.result

                    # Execute via parent's tool registry
                    tool_result = await self.parent.execute_tool(tool_name, tool_args)
                    self.history.append({
                        "role": "tool",
                        "content": str(tool_result),
                    })

            self.status = "complete"
            return self.result

        except Exception as e:
            self.status = "error"
            self.result = f"Sub-agent error: {e}"
            logger.error(f"Sub-agent {self.agent_id} failed: {e}")
            return self.result

    def _build_system_prompt(self) -> str:
        """Build a system prompt for the sub-agent."""
        tools_desc = ""
        if self.allowed_tools:
            tools_desc = f"You may only use these tools: {', '.join(self.allowed_tools)}"
        else:
            tools_desc = "You have access to the same tools as the main agent."

        return f"""You are a sub-agent of iTaK, focused on a specific task.
You must complete the task and return your result using the response tool.
Be concise and focused. Do not deviate from the assigned task.

{tools_desc}

When done, call the response tool with your final answer.
Maximum iterations: {self.max_iterations}
"""

    def _parse_tool_calls(self, response: str) -> list[dict]:
        """Parse tool calls from LLM response (JSON format).
        
        Uses dirtyjson to handle malformed JSON from LLM responses.
        """
        try:
            # Try dirtyjson first for better handling of malformed JSON
            if HAS_DIRTYJSON:
                data = dirtyjson.loads(response)
            else:
                data = json.loads(response)

            if isinstance(data, dict):
                tool_calls = data.get("tool_calls", data.get("tools", []))
                if isinstance(tool_calls, list):
                    return tool_calls
                # Single tool call format
                if "tool_name" in data or "name" in data:
                    return [data]
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        return []


class SubAgentManager:
    """Manages spawning and tracking of sub-agents."""

    def __init__(self, parent: "Agent"):
        self.parent = parent
        self.agents: dict[str, SubAgent] = {}
        self._results: dict[str, str] = {}

    async def spawn(
        self,
        task: str,
        allowed_tools: list[str] | None = None,
        system_prompt: str | None = None,
        max_iterations: int = 15,
    ) -> SubAgent:
        """Spawn a new sub-agent."""
        agent = SubAgent(
            parent=self.parent,
            task=task,
            allowed_tools=allowed_tools,
            system_prompt_override=system_prompt,
            max_iterations=max_iterations,
        )
        self.agents[agent.agent_id] = agent
        return agent

    async def run(self, agent_id: str) -> str:
        """Run a specific sub-agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return f"Sub-agent {agent_id} not found."

        result = await agent.run()
        self._results[agent_id] = result
        return result

    async def run_parallel(self, tasks: list[dict]) -> list[str]:
        """Spawn and run multiple sub-agents in parallel.

        Args:
            tasks: List of {"task": str, "tools": list[str]}

        Returns:
            List of results in same order.
        """
        agents = []
        for t in tasks:
            agent = await self.spawn(
                task=t["task"],
                allowed_tools=t.get("tools"),
                max_iterations=t.get("max_iterations", 10),
            )
            agents.append(agent)

        # Run all in parallel
        results = await asyncio.gather(
            *[a.run() for a in agents],
            return_exceptions=True,
        )

        return [str(r) for r in results]

    def get_status(self) -> dict:
        """Get status of all sub-agents."""
        return {
            aid: {
                "status": a.status,
                "task": a.task[:80],
                "iterations": a.iterations,
                "has_result": bool(a.result),
            }
            for aid, a in self.agents.items()
        }
