"""
iTaK Knowledge Tool — Save and query reusable knowledge files.
"""

import time
from pathlib import Path

from tools.base import BaseTool, ToolResult


class KnowledgeTool(BaseTool):
    """Save and query reusable knowledge files in the skills directory.

    Knowledge files are markdown documents that persist across sessions
    and can be loaded into context when relevant.
    """

    name = "knowledge_tool"
    description = "Save or query reusable knowledge files."

    KNOWLEDGE_DIR = Path("skills")

    async def execute(
        self,
        action: str = "query",
        filename: str = "",
        content: str = "",
        query: str = "",
        **kwargs,
    ) -> ToolResult:
        """Save or query knowledge files."""
        self.KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

        if action == "save":
            return await self._save(filename, content)
        elif action == "query":
            return await self._query(query or filename)
        elif action == "list":
            return await self._list()
        elif action == "read":
            return await self._read(filename)
        else:
            return ToolResult(
                output=f"Error: Invalid action '{action}'. Use: save, query, list, read",
                error=True,
            )

    async def _save(self, filename: str, content: str) -> ToolResult:
        """Save a knowledge file."""
        if not filename or not content:
            return ToolResult(output="Error: 'filename' and 'content' required.", error=True)

        if not filename.endswith(".md"):
            filename += ".md"

        filepath = self.KNOWLEDGE_DIR / filename
        filepath.write_text(content, encoding="utf-8")

        return ToolResult(output=f"Knowledge saved: {filepath}")

    async def _query(self, query: str) -> ToolResult:
        """Search knowledge files for relevant content."""
        if not query:
            return ToolResult(output="Error: 'query' is required.", error=True)

        results = []
        query_lower = query.lower()

        for md_file in self.KNOWLEDGE_DIR.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    # Extract matching section
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            start = max(0, i - 2)
                            end = min(len(lines), i + 5)
                            snippet = "\n".join(lines[start:end])
                            results.append({
                                "file": md_file.name,
                                "snippet": snippet,
                            })
                            break
            except Exception:
                continue

        if not results:
            return ToolResult(output=f"No knowledge found for: '{query}'")

        output_parts = [f"Found {len(results)} knowledge files:\n"]
        for r in results:
            output_parts.append(f"**{r['file']}:**\n{r['snippet']}\n")

        return ToolResult(output="\n".join(output_parts))

    async def _list(self) -> ToolResult:
        """List all knowledge files."""
        files = list(self.KNOWLEDGE_DIR.glob("*.md"))
        if not files:
            return ToolResult(output="No knowledge files found.")

        output = "Knowledge files:\n"
        for f in sorted(files):
            size = f.stat().st_size
            output += f"- {f.name} ({size} bytes)\n"

        return ToolResult(output=output)

    async def _read(self, filename: str) -> ToolResult:
        """Read a specific knowledge file."""
        if not filename:
            return ToolResult(output="Error: 'filename' is required.", error=True)

        if not filename.endswith(".md"):
            filename += ".md"

        filepath = self.KNOWLEDGE_DIR / filename
        if not filepath.exists():
            return ToolResult(output=f"File not found: {filename}", error=True)

        content = filepath.read_text(encoding="utf-8")
        return ToolResult(output=f"**{filename}:**\n\n{content}")
