# Tools Reference

## At a Glance
- Audience: Developers extending iTaK behavior via tools, prompts, models, and core modules.
- Scope: This page explains `Tools Reference`.
- Last reviewed: 2026-02-16.

## Quick Start
- Docs hub: [WIKI.md](WIKI.md)
- Beginner path: [NOOBS_FIRST_DAY.md](NOOBS_FIRST_DAY.md)
- AI-oriented project map: [AI_CONTEXT.md](AI_CONTEXT.md)

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Keep argument names and defaults exact when generating tool/model calls.
- Prefer evidence from code paths over assumptions when documenting behavior.


> Every tool the agent can use, with arguments and examples.

## Overview

Tools live in the `tools/` directory. The agent auto-loads them at startup - just drop a `.py` file and it's available. Each tool is a class that inherits from `BaseTool`.

---

## BaseTool Interface

**File:** `tools/base.py` | **Lines:** ~40

```python
class BaseTool:
    name: str          # Tool name (used in JSON tool calls)
    description: str   # One-line description for the LLM

    async def execute(self, **kwargs) -> ToolResult:
        """Override this to implement the tool."""
        raise NotImplementedError

@dataclass
class ToolResult:
    output: str            # The result text
    error: bool = False    # Did it fail?
    break_loop: bool = False  # Should the monologue loop stop?
```

### Creating a Custom Tool

```python
# tools/my_custom_tool.py
from tools.base import BaseTool, ToolResult

class MyCustomTool(BaseTool):
    name = "my_tool"
    description = "Does something useful."

    async def execute(self, arg1: str = "", arg2: int = 0, **kwargs) -> ToolResult:
        # Do the thing
        result = f"Processed {arg1} with {arg2}"
        return ToolResult(output=result)
```

Drop this file in `tools/` and the agent can immediately use it. The LLM sees it in its tool list as:
```json
{"tool_name": "my_tool", "tool_args": {"arg1": "hello", "arg2": 42}}
```

---

## response - Break the Loop

**File:** `tools/response.py` | **Lines:** ~35

**The most important tool.** This is the ONLY way to end the monologue loop and send a response to the user.

### Arguments
| Arg | Type | Description |
|-----|------|-------------|
| `message` | str | The final response text |

### Example LLM Call
```json
{
    "thoughts": ["I have all the information, time to respond."],
    "tool_name": "response",
    "tool_args": {"message": "Here's what I found: ..."}
}
```

### What happens internally
1. The message passes through the **Output Guard** (PII/secret scrubbing)
2. Progress tracker marks the task as complete
3. `ToolResult.break_loop = True` stops the monologue
4. The sanitized message is returned to the adapter

---

## code_execution - Run Code

**File:** `tools/code_execution.py` | **Lines:** 207

Execute Python, Node.js, or shell commands.

### Arguments
| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `runtime` | str | `"terminal"` | `python`, `nodejs`, or `terminal` |
| `code` | str | (required) | The code to execute |
| `timeout` | int | 60 | Max execution time in seconds |
| `workdir` | str | cwd | Working directory |

### Example: Python
```json
{
    "tool_name": "code_execution",
    "tool_args": {
        "runtime": "python",
        "code": "import json\ndata = {'name': 'iTaK', 'version': 4}\nprint(json.dumps(data, indent=2))"
    }
}
```

### Example: Terminal (Shell)
```json
{
    "tool_name": "code_execution",
    "tool_args": {
        "runtime": "terminal",
        "code": "ls -la /tmp"
    }
}
```

### Sandbox Mode
When `security.sandbox_enabled = true` in config, code runs inside a Docker container:
- No network access (`--network=none`)
- 512MB memory limit
- 1 CPU limit
- Automatic cleanup after execution

### Timeout Cascade
```python
DEFAULT_TIMEOUT = 60   # Normal limit
MAX_TIMEOUT = 300      # Hard cap (5 minutes)
NO_OUTPUT_TIMEOUT = 30 # Kill if no output for 30s
```

---

## web_search - Search the Web

**File:** `tools/web_search.py` | **Lines:** ~110

Search the web using SearXNG (self-hosted search engine).

### Arguments
| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `query` | str | (required) | Search query |
| `num_results` | int | 5 | Number of results to return |
| `engines` | str | `""` | Specific engines (e.g., "google,duckduckgo") |

### Example
```json
{
    "tool_name": "web_search",
    "tool_args": {
        "query": "Python asyncio best practices 2025",
        "num_results": 10
    }
}
```

### Configuration
```json
{
    "tools": {
        "web_search": {
            "searxng_url": "http://localhost:8080/search",
            "default_results": 5
        }
    }
}
```

---

## memory_save - Save to Memory

**File:** `tools/memory_save.py` | **Lines:** ~65

Save information to the agent's memory for future recall.

### Arguments
| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `content` | str | (required) | What to remember |
| `category` | str | `"general"` | Category tag |
| `metadata` | dict | `{}` | Extra context |

### Example
```json
{
    "tool_name": "memory_save",
    "tool_args": {
        "content": "Docker compose v2 uses 'docker compose' (space) not 'docker-compose' (hyphen)",
        "category": "devops",
        "metadata": {"source": "learned_from_error", "confidence": "high"}
    }
}
```

Saves to ALL configured layers (Markdown, SQLite, Neo4j, Weaviate).

---

## memory_load - Search Memory

**File:** `tools/memory_load.py` | **Lines:** ~70

Search across all memory layers.

### Arguments
| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `query` | str | (required) | Search query |
| `category` | str | `""` | Filter by category |
| `limit` | int | 10 | Max results |

### Example
```json
{
    "tool_name": "memory_load",
    "tool_args": {
        "query": "docker port conflict solution",
        "category": "devops",
        "limit": 5
    }
}
```

---

## knowledge_tool - Knowledge Graph

**File:** `tools/knowledge_tool.py` | **Lines:** ~140

Query and modify the Neo4j knowledge graph.

### Arguments
| Arg | Type | Description |
|-----|------|-------------|
| `action` | str | `search`, `save_entity`, `save_relationship`, `get_context` |
| `entity` | str | Entity name |
| `entity_type` | str | Entity type (person, project, tool, etc.) |
| `related_to` | str | Related entity name |
| `relationship` | str | Relationship type |
| `properties` | dict | Extra properties |

### Example: Save a relationship
```json
{
    "tool_name": "knowledge_tool",
    "tool_args": {
        "action": "save_relationship",
        "entity": "iTaK",
        "entity_type": "project",
        "related_to": "FastAPI",
        "relationship": "uses"
    }
}
```

### Example: Get context for an entity
```json
{
    "tool_name": "knowledge_tool",
    "tool_args": {
        "action": "get_context",
        "entity": "iTaK"
    }
}
```
Returns all connected nodes and relationships.

---

## browser_agent - Vision Web Browser

**File:** `tools/browser_agent.py` | **Lines:** ~95

Browse the web with a vision-capable browser. Can take screenshots and read page content.

### Arguments
| Arg | Type | Description |
|-----|------|-------------|
| `url` | str | URL to navigate to |
| `action` | str | `navigate`, `screenshot`, `read`, `click`, `type` |
| `selector` | str | CSS selector for click/type actions |
| `text` | str | Text to type |

### Example
```json
{
    "tool_name": "browser_agent",
    "tool_args": {
        "url": "https://github.com/trending",
        "action": "screenshot"
    }
}
```

The screenshot is processed by the vision model (browser model) to understand page content.

---

## delegate_task - Spawn Sub-Agent

**File:** `tools/delegate_task.py` | **Lines:** ~75

Spawn a specialized sub-agent for a specific task.

### Arguments
| Arg | Type | Description |
|-----|------|-------------|
| `task` | str | Task description |
| `role` | str | Specialized role (coder, researcher, tester) |
| `tools` | list | Tools the sub-agent can use |

### Example
```json
{
    "tool_name": "delegate_task",
    "tool_args": {
        "task": "Research the top 5 Python testing frameworks and summarize their pros/cons",
        "role": "researcher",
        "tools": ["web_search", "memory_save"]
    }
}
```

---

## gogcli_tool - Google Workspace CLI Integration

**File:** `tools/gogcli_tool.py`

Execute `gog` (gogcli) commands from the agent in non-interactive mode.

### Arguments
| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `action` | str | `"run"` | One of `run`, `help`, `version` |
| `command` | str | `""` | gog subcommand string (required for `action=run`) |
| `json_output` | bool | `true` | Appends `--json` when missing |
| `no_input` | bool | `true` | Appends `--no-input` when missing |
| `account` | str | `""` | Optional `GOG_ACCOUNT` override |
| `client` | str | `""` | Optional `GOG_CLIENT` override |
| `timeout` | int | `60` | Max execution time in seconds |

### Example
```json
{
    "tool_name": "gogcli_tool",
    "tool_args": {
        "action": "run",
        "command": "users list",
        "json_output": true,
        "no_input": true,
        "timeout": 60
    }
}
```

### Config
`settings.external.gogcli` controls binary and timeout defaults (UI-backed fields):
- `gogcli_binary`
- `gogcli_timeout_seconds`

---

## Operator Smoke Scripts (CLI)

These scripts are for operators/developers and are also callable via the WebUI settings smoke-test panel.

| Script | Purpose |
|--------|---------|
| `tools/check_resource_endpoints.sh` | Validates key resource/catalog endpoints |
| `tools/check_memory_smoke.sh` | Save/search/delete memory roundtrip |
| `tools/check_chat_smoke.sh` | Chat context + response log roundtrip |
| `tools/check_system_smoke.sh` | Runs all smoke checks |

Usage:
```bash
bash tools/check_system_smoke.sh
```

Optional target override:
```bash
WEBUI_BASE_URL=http://127.0.0.1:43067 bash tools/check_system_smoke.sh
```

The sub-agent runs its own monologue loop and returns the result to the parent.
