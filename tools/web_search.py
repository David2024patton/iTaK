"""
iTaK Web Search Tool - Search via SearXNG.
"""

import httpx
from tools.base import BaseTool, ToolResult

# Import DuckDuckGo at module level to avoid repeated imports
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


class WebSearchTool(BaseTool):
    """Search the web using SearXNG (self-hosted on VPS).

    Falls back to DuckDuckGo if SearXNG is not configured.
    """

    name = "web_search"
    description = "Search the web for information."

    async def execute(
        self,
        query: str = "",
        num_results: int = 5,
        **kwargs,
    ) -> ToolResult:
        """Search the web and return results."""
        if not query:
            return ToolResult(output="Error: 'query' is required.", error=True)

        searxng_url = self.agent.config.get("searxng", {}).get("url", "")

        if searxng_url:
            # SSRF guard: validate the SearXNG URL before fetching
            try:
                from security.ssrf_guard import SSRFGuard
                guard = SSRFGuard(self.agent.config)
                safe, reason = guard.validate_url(searxng_url, source="web_search")
                if not safe:
                    return ToolResult(
                        output=f"SSRF blocked: {reason}",
                        error=True,
                    )
            except ImportError:
                pass  # Guard not available, proceed without check
            return await self._search_searxng(query, num_results, searxng_url)
        else:
            return await self._search_duckduckgo(query, num_results)

    async def _search_searxng(
        self, query: str, num_results: int, base_url: str
    ) -> ToolResult:
        """Search using self-hosted SearXNG."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"{base_url}/search",
                    params={
                        "q": query,
                        "format": "json",
                        "categories": "general",
                    },
                )
                response.raise_for_status()
                data = response.json()

            results = data.get("results", [])[:num_results]
            if not results:
                return ToolResult(output=f"No results found for: '{query}'")

            output_parts = [f"Search results for '{query}':\n"]
            for i, r in enumerate(results, 1):
                title = r.get("title", "No title")
                url = r.get("url", "")
                snippet = r.get("content", "")[:200]
                output_parts.append(f"**{i}.** [{title}]({url})\n{snippet}\n")

            return ToolResult(output="\n".join(output_parts))

        except Exception as e:
            return ToolResult(output=f"SearXNG error: {e}", error=True)

    async def _search_duckduckgo(self, query: str, num_results: int) -> ToolResult:
        """Fallback: search using DuckDuckGo."""
        if not DDGS_AVAILABLE:
            return ToolResult(
                output="No search backend available. Configure SearXNG or install duckduckgo-search.",
                error=True,
            )
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))

            if not results:
                return ToolResult(output=f"No results found for: '{query}'")

            output_parts = [f"Search results for '{query}':\n"]
            for i, r in enumerate(results, 1):
                title = r.get("title", "No title")
                url = r.get("href", "")
                snippet = r.get("body", "")[:200]
                output_parts.append(f"**{i}.** [{title}]({url})\n{snippet}\n")

            return ToolResult(output="\n".join(output_parts))

        except Exception as e:
            return ToolResult(output=f"DuckDuckGo error: {e}", error=True)
