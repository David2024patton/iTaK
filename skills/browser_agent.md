# Skill: Browser Agent

Category: tool
Tags: browser, web, screenshot, vision, scraping

## When to Use

When the user needs you to interact with websites visually - read page content, take screenshots, click buttons, fill forms, or verify that a deployed site looks correct.

## Steps

1. Navigate to the URL with `action: "navigate"`
2. Take a screenshot with `action: "screenshot"` to see the current state
3. Use the vision model to understand what's on screen
4. Interact with elements using `action: "click"` or `action: "type"` with CSS selectors
5. Take another screenshot to verify the result

## Examples

### Example 1: Verify a deployment

```json
{"tool_name": "browser_agent", "tool_args": {"url": "https://mysite.com", "action": "screenshot"}}
```

Then describe what you see to the user.

### Example 2: Fill a form

```json
{"tool_name": "browser_agent", "tool_args": {"action": "type", "selector": "#search-input", "text": "iTaK framework"}}
```

### Example 3: Read page content

```json
{"tool_name": "browser_agent", "tool_args": {"url": "https://docs.python.org/3/library/asyncio.html", "action": "read"}}
```

## Common Errors

| Error | Fix |
|-------|-----|
| Playwright not installed | Run `playwright install chromium` |
| Element not found | Verify the CSS selector, take a screenshot first |
| Page timeout | Site may be slow or down, increase timeout |
| Vision model missing | Ensure browser model is configured in config.json |
