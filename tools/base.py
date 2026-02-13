"""
iTaK Base Tool — Interface that all tools inherit from.
"""

from typing import TYPE_CHECKING, Any
from dataclasses import dataclass

if TYPE_CHECKING:
    from core.agent import Agent


@dataclass
class ToolResult:
    """Standard tool execution result."""
    output: str = ""
    break_loop: bool = False
    error: bool = False

    def __str__(self):
        return self.output


class BaseTool:
    """Base class for all iTaK tools.

    To create a new tool:
    1. Create a file in tools/ (e.g., my_tool.py)
    2. Define a class inheriting from BaseTool
    3. Implement execute(**kwargs) → ToolResult
    4. Create a matching prompt in prompts/agent.system.tool.my_tool.md
    """

    name: str = "base"
    description: str = "Base tool"

    def __init__(self, agent: "Agent"):
        self.agent = agent

    async def execute(self, **kwargs) -> ToolResult:
        """Override this method in subclasses."""
        raise NotImplementedError("Tool must implement execute()")
