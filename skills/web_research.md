# Skill: Web Research Protocol
Category: tool
Tags: search, web, research, scraping, browser

## Overview
iTaK has two tools for web research:
1. **web_search** - SearXNG search engine queries (fast, text results)
2. **browser_agent** - Full browser automation (slower, visual, interactive)

## When to Use Which

| Scenario | Tool |
|----------|------|
| Quick fact lookup | `web_search` |
| Find documentation URL | `web_search` |
| Current events / news | `web_search` |
| Read a specific webpage | `browser_agent` |
| Fill out a form | `browser_agent` |
| Take a screenshot | `browser_agent` |
| JavaScript-rendered content | `browser_agent` |
| Login-required pages | `browser_agent` |

## Research Protocol

1. **Search first** - Use `web_search` to find relevant URLs
2. **Read top results** - Use `browser_agent` to read specific pages
3. **Extract key info** - Note important facts, code, patterns
4. **Save to memory** - Use `memory_save` for important findings
5. **Create skill** - If the info is reusable, save as a skill file

## Search Tips

- Use specific, focused queries
- Include version numbers for tech queries (e.g., "FastAPI 0.109 middleware")
- Use quotes for exact phrases
- Add "site:github.com" to search within GitHub
- Add "filetype:py" to find Python files

## Browser Tips

- Always wait for page to fully load
- Use CSS selectors for element interaction
- Handle cookie consent banners (init_override.js does this automatically)
- Take screenshots for visual verification
- Set reasonable timeouts (30-60s per page)

## Common Research Tasks

### Find and read documentation
```
1. web_search("FastAPI middleware documentation")
2. browser_agent("Navigate to [URL] and extract the middleware example")
```

### Compare solutions
```
1. web_search("best Python HTTP client library 2024")
2. Read top 3 articles
3. Summarize pros/cons
```

### Solve an error
```
1. web_search("Python error: [exact error message]")
2. Find Stack Overflow answer
3. Extract the solution
```
