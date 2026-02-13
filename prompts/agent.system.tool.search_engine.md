# Tool: web_search

## Usage

Search the web for information using SearXNG (self-hosted) or DuckDuckGo (fallback).

## Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `num_results` | int | No | Number of results (default: 5) |

## Example

```json
{
    "thoughts": ["I need to find the latest FastAPI docs for this feature."],
    "headline": "Searching the web",
    "tool_name": "web_search",
    "tool_args": {
        "query": "FastAPI WebSocket dependency injection 2025",
        "num_results": 5
    }
}
```

## Rules

- **Always check memory first** before searching
- Use specific, targeted queries
- Include version numbers or dates when looking for current info
