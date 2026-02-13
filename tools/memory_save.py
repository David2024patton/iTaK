"""
iTaK Memory Save Tool - Store new knowledge/facts/decisions.
"""

from tools.base import BaseTool, ToolResult


class MemorySaveTool(BaseTool):
    """Save a new memory to the agent's brain.

    Categories:
    - general: Default catch-all
    - fact: Discovered facts about the world
    - decision: Architecture or design decisions
    - lesson: Learned from mistakes or experience
    - solution: Working fix for a specific problem
    - preference: User preferences
    """

    name = "memory_save"
    description = "Save new knowledge, facts, or decisions to memory."

    async def execute(
        self,
        content: str = "",
        category: str = "general",
        metadata: dict | None = None,
        **kwargs,
    ) -> ToolResult:
        """Save a memory entry."""
        if not content:
            return ToolResult(output="Error: 'content' is required.", error=True)

        valid_categories = [
            "general", "fact", "decision", "lesson",
            "solution", "preference",
        ]
        if category not in valid_categories:
            return ToolResult(
                output=f"Error: Invalid category '{category}'. Valid: {valid_categories}",
                error=True,
            )

        try:
            from memory.manager import MemoryManager
            memory = MemoryManager(
                config=self.agent.config.get("memory", {}),
                model_router=self.agent.model_router,
            )

            memory_id = await memory.save(
                content=content,
                category=category,
                metadata=metadata,
                source="agent",
            )

            return ToolResult(
                output=f"Memory saved (ID: {memory_id}, category: {category}):\n{content[:200]}"
            )

        except Exception as e:
            return ToolResult(output=f"Memory save error: {e}", error=True)
