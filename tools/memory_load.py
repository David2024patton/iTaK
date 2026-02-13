"""
iTaK Memory Load Tool — Search across all 4 memory layers.
"""

from tools.base import BaseTool, ToolResult


class MemoryLoadTool(BaseTool):
    """Search the agent's memory across all layers.

    Layers searched (in order):
    1. SQLite + embeddings (fast vector search)
    2. Markdown files (SOUL, USER, MEMORY, AGENTS)
    3. Neo4j graph (relationships) — Phase 2
    4. Weaviate vectors (semantic search) — Phase 2
    """

    name = "memory_load"
    description = "Search memory for relevant information."

    async def execute(
        self,
        query: str = "",
        category: str | None = None,
        limit: int = 10,
        **kwargs,
    ) -> ToolResult:
        """Search memory with a natural language query."""
        if not query:
            return ToolResult(output="Error: 'query' is required.", error=True)

        try:
            # Import memory manager from agent
            from memory.manager import MemoryManager
            memory = MemoryManager(
                config=self.agent.config.get("memory", {}),
                model_router=self.agent.model_router,
            )

            results = await memory.search(
                query=query,
                category=category,
                limit=limit,
            )

            if not results:
                return ToolResult(output=f"No memories found for query: '{query}'")

            # Format results
            output_parts = [f"Found {len(results)} memories for '{query}':\n"]
            for i, r in enumerate(results, 1):
                score = r.get("score", 0)
                content = r.get("content", "")[:300]
                cat = r.get("category", "general")
                meta = r.get("metadata", {})
                source = meta.get("source_file", r.get("source", "sqlite"))

                output_parts.append(
                    f"**{i}.** [{cat}] (score: {score:.2f}, source: {source})\n{content}\n"
                )

            return ToolResult(output="\n".join(output_parts))

        except Exception as e:
            return ToolResult(output=f"Memory search error: {e}", error=True)
