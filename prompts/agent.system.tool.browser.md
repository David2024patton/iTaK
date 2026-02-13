# Tool: browser_agent

## Usage

Send a task to the AI-powered browser agent. It navigates, clicks, types, and reads web pages using vision.

**This is NOT raw Playwright.** It's a full AI agent with its own LLM that sees screenshots and reasons about interactions.

## Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `task` | string | Yes | What to do in the browser (natural language) |
| `url` | string | No | Starting URL to navigate to |

## Example

```json
{
    "thoughts": ["I need to check the current Polymarket prices for this event."],
    "headline": "Browsing Polymarket",
    "tool_name": "browser_agent",
    "tool_args": {
        "task": "Find the current Yes/No prices for the 'Will Bitcoin hit $100k by March 2026?' market",
        "url": "https://polymarket.com"
    }
}
```

## Rules

- Use for anything that requires interacting with a web page
- The browser agent uses the dedicated **browser model** (cheap, fast, vision-capable)
- Keep tasks focused - one website, one objective
- For simple data retrieval, prefer `web_search` over browser
