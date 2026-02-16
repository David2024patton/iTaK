# Core Module Reference

## At a Glance
- Audience: Users, operators, developers, and contributors working with iTaK.
- Scope: This page explains `Core Module Reference`.
- Last reviewed: 2026-02-16.

## Quick Start
- Docs hub: [WIKI.md](WIKI.md)
- Beginner path: [NOOBS_FIRST_DAY.md](NOOBS_FIRST_DAY.md)
- AI-oriented project map: [AI_CONTEXT.md](AI_CONTEXT.md)

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Use explicit file paths and exact command examples from this page when automating tasks.
- Treat scale/compliance statements as environment-dependent unless paired with test or audit evidence.


> Every file in `core/` explained in detail with examples.

## Table of Contents

- [agent.py - The Monologue Engine](#agentpy)
- [models.py - Model Router](#modelspy)
- [logger.py - Structured Logging](#loggerpy)
- [progress.py - Progress Tracking](#progresspy)
- [checkpoint.py - Crash Recovery](#checkpointpy)
- [task_board.py - Task Management](#task_boardpy)
- [self_heal.py - Self-Healing Engine](#self_healpy)
- [sub_agents.py - Sub-Agent Spawner](#sub_agentspy)
- [mcp_client.py - MCP Client](#mcp_clientpy)
- [mcp_server.py - MCP Server](#mcp_serverpy)
- [webhooks.py - Webhook Engine](#webhookspy)
- [swarm.py - Swarm Coordinator](#swarmpy)
- [users.py - User Registry](#userspy)
- [presence.py - Presence Manager](#presencepy)
- [media.py - Media Pipeline](#mediapy)
- [linter.py - Code Quality Gate](#linterpy)

---

## agent.py

**Lines:** ~763 | **The single most important file in the project.**

This is the monologue engine. Everything else orbits around this file.

### Classes

#### `AgentConfig`
```python
@dataclass
class AgentConfig:
    name: str = "iTaK"
    max_iterations: int = 25        # Max LLM calls per conversation
    timeout_seconds: int = 300      # 5 min hard timeout
    repeat_detection: bool = True   # Detect repeated responses
    checkpoint_enabled: bool = True # Save state for crash recovery
    checkpoint_interval_steps: int = 3
```
Loaded from `config.json` under the `agent` key. Controls how the agent behaves at a fundamental level.

#### `AgentContext`
```python
@dataclass
class AgentContext:
    agent_id: str = ""
    adapter_name: str = "cli"       # Which platform sent the message
    room_id: str = "default"        # Chat room / channel
    user_id: str = "owner"          # Who sent the message
    intervention_queue: list = []   # Messages from user mid-execution
    data: dict = {}                 # Arbitrary shared data
```
Shared across the agent lifecycle. Adapters set `adapter_name` and `user_id` before calling `monologue()`.

#### Exception Classes
```python
class RepairableException(Exception):
    """Error that can be forwarded to LLM for self-repair."""

class CriticalException(Exception):
    """Fatal error - 1 retry then kill the loop."""

class InterventionException(Exception):
    """User interrupted mid-execution - restart inner loop."""
```

#### `Agent`
The main class. Key methods:

| Method | Purpose |
|--------|---------|
| `__init__()` | Load config, init all 16+ subsystems |
| `startup()` | Connect memory stores, start heartbeat, MCP servers |
| `shutdown()` | Graceful cleanup |
| `monologue(msg)` | **THE MAIN LOOP** - think/act/iterate |
| `_build_system_prompt()` | Assemble prompt from templates + memory |
| `_prepare_messages()` | Format history for LLM API |
| `_process_tools(response)` | Parse JSON, execute tool, handle errors |
| `_extract_tool_json(text)` | Tolerant JSON parser (handles markdown fences, trailing commas) |
| `_detect_repeat(response)` | Catch infinite loops |
| `_handle_intervention()` | Check if user sent a message mid-execution |
| `execute_tool(name, args)` | Public API for sub-agents |
| `get_subsystem_status()` | Dashboard health check |

### Subsystem Init Order

When `Agent()` is constructed, subsystems load in this order:

1. Config (`_load_config`)
2. Logger
3. Model Router (4 models)
4. Memory Manager (4 layers)
5. Security Scanner
6. Secret Manager
7. Rate Limiter
8. Heartbeat Monitor
9. Progress Tracker
10. Checkpoint Manager
11. Self-Heal Engine
12. Task Board
13. Sub-Agent spawner
14. MCP Client
15. Code Quality Gate (Linter)
16. MCP Server
17. Webhook Engine
18. Swarm Coordinator
19. User Registry
20. Presence Manager
21. Media Pipeline
22. **Output Guard**
23. Tools (dynamic loading)
24. Extensions (dynamic loading)

Each subsystem uses a try/except ImportError pattern so any missing dependency degrades gracefully instead of crashing the whole agent.

---

## models.py

**Lines:** ~280 | **Handles all LLM API calls.**

### `ModelRouter`
Routes requests to the right model based on the task:

```python
router = ModelRouter(config)

# Chat model - for main reasoning
response = await router.chat(messages)

# Utility model - for cheap tasks (summarize, extract, classify)
response = await router.utility(messages)

# Browser model - vision-capable for screenshots
response = await router.browser(messages, images=[screenshot])

# Embeddings - for vector search
vector = await router.embed("some text")
```

#### Model Configuration (config.json)
```json
{
    "models": {
        "chat": {
            "provider": "litellm",
            "model": "gemini/gemini-2.5-pro-preview-05-06",
            "temperature": 0.7,
            "max_tokens": 8192,
            "context_window": 1000000
        },
        "utility": {
            "provider": "litellm",
            "model": "gemini/gemini-2.0-flash"
        },
        "browser": {
            "provider": "litellm",
            "model": "gemini/gemini-2.5-pro-preview-05-06"
        },
        "embeddings": {
            "provider": "litellm",
            "model": "text-embedding-3-small",
            "dimensions": 768
        }
    }
}
```

The `litellm` provider supports 100+ LLM APIs through a single interface. You can swap models just by changing the config.

---

## logger.py

**Lines:** ~185 | **Structured event logging with secret masking.**

Every log entry is a structured event:

```python
class EventType(str, Enum):
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MEMORY_SEARCH = "memory_search"
    MEMORY_SAVE = "memory_save"
    SECURITY_ALERT = "security_alert"
    ERROR = "error"
    INTERVENTION = "intervention"
    CHECKPOINT = "checkpoint"
    HEARTBEAT = "heartbeat"
    SELF_HEAL = "self_heal"
```

Usage:
```python
self.logger.log(EventType.TOOL_CALL, {
    "tool": "code_execution",
    "runtime": "python",
    "code_length": 150,
})
```

The logger automatically masks secrets using registered patterns from `SecretManager.register_with_logger()`.

---

## progress.py

**Lines:** ~92 | **Anti-silence broadcasting.**

The agent sends progress updates to prevent the "is it dead?" feeling:

```python
await self.progress.plan("I'll search memory first, then check the web")
await self.progress.update(step=1, message="Searching memory...")
await self.progress.update(step=2, message="Found 3 results, checking web...")
await self.progress.complete("Here's what I found")
```

Adapters register callbacks to receive these events:

```python
self.agent.progress.register_callback(self._on_progress)
```

---

## checkpoint.py

**Lines:** ~110 | **Crash recovery via state serialization.**

Every N steps (default: 3), the agent saves its state:

```python
checkpoint = {
    "iteration": self.iteration_count,
    "history": self.history,
    "context": asdict(self.context),
    "timestamp": time.time(),
}
```

On restart, if a checkpoint is found, the agent resumes from where it left off instead of starting over.

---

## task_board.py

**Lines:** ~210 | **Kanban-style task management.**

The agent tracks multi-step tasks:

```python
task_id = self.task_board.create(
    title="Deploy new version",
    steps=["Build Docker image", "Push to registry", "Update Dokploy"]
)

self.task_board.advance(task_id, "Building image...")
self.task_board.advance(task_id, "Pushing to registry...")
self.task_board.complete(task_id)
```

Tasks have statuses: `pending`, `in_progress`, `completed`, `failed`. Viewable via the WebUI dashboard.

---

## self_heal.py

**Lines:** 422 | **5-step auto-recovery pipeline.**

When a tool fails, the self-heal engine kicks in:

```
Step 1: CLASSIFY   --> Is it repairable, partial, or critical?
Step 2: REMEMBER   --> Have we seen this error before?
Step 3: REASON     --> Ask the LLM for fix suggestions
Step 4: RETRY      --> Try the fix (with backoff: 1s, 5s, 15s)
Step 5: LEARN      --> If fixed, save the solution to memory
```

### Error Categories
```python
class ErrorCategory(str, Enum):
    DEPENDENCY = "dependency"   # Missing package
    NETWORK = "network"         # Connection failed
    CONFIG = "config"           # Bad configuration
    RUNTIME = "runtime"         # Code error
    TOOL = "tool"              # Tool-specific error
    RESOURCE = "resource"       # Disk/memory/CPU
    SECURITY = "security"       # Permission denied
    DATA = "data"              # Bad input data
    UNKNOWN = "unknown"
```

### Budget Limits
- Max 3 retries per individual error
- Max 10 retries per session
- Backoff: 1s, 5s, 15s between retries

### Example Flow
```
Tool "code_execution" fails: ModuleNotFoundError: requests
  |
  v
CLASSIFY: category=DEPENDENCY, severity=REPAIRABLE
  |
  v
REMEMBER: Searching memory... found previous fix!
  "pip install requests fixed this before"
  |
  v
RETRY: pip install requests --> success
  |
  v
LEARN: Saved fix to memory for next time
```

---

## sub_agents.py

**Lines:** ~130 | **Spawn specialized child agents.**

The main agent can create sub-agents for specific tasks:

```python
# Create a sub-agent with a specialized role
sub = self.sub_agents.spawn(
    role="researcher",
    task="Find the latest Python best practices for async"
)
result = await sub.monologue("Do the research")
```

Sub-agents inherit the parent's config but can have different roles and limited tool access. They share memory but have their own monologue loop.

---

## mcp_client.py

**Lines:** ~170 | **Connect to external MCP tool servers.**

MCP (Model Context Protocol) lets iTaK use tools from external servers:

```json
{
    "mcp_servers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
        }
    }
}
```

The MCP client connects to these servers and adds their tools to the agent's toolbox automatically.

---

## mcp_server.py

**Lines:** ~145 | **Expose iTaK tools to other agents.**

Makes iTaK available as an MCP server, so other AI agents can use iTaK's tools:

```json
{
    "mcp_server": {
        "enabled": true,
        "host": "0.0.0.0",
        "port": 48921
    }
}
```

---

## webhooks.py

**Lines:** ~165 | **n8n/Zapier webhook integration.**

Receive and process webhooks from external automation platforms:

```json
{
    "webhooks": {
        "secret": "$WEBHOOK_SECRET",
        "allowed_sources": ["n8n", "zapier"],
        "auto_respond": true
    }
}
```

When a webhook arrives at `/api/v1/webhooks/inbound`, it's verified, processed, and optionally auto-responded to.

---

## swarm.py

**Lines:** ~198 | **Multi-agent coordination.**

Coordinate multiple agent instances working together:

```python
result = await self.swarm.execute(
    task="Build a full-stack app",
    agents=["coder", "tester", "reviewer"],
    strategy="sequential"  # or "parallel"
)
```

Agent profiles define specialization:
```json
{
    "profiles": {
        "coder": {"role": "Write code", "tools": ["code_execution"]},
        "tester": {"role": "Write and run tests", "tools": ["code_execution"]},
        "reviewer": {"role": "Review code quality", "tools": []}
    }
}
```

---

## users.py

**Lines:** ~165 | **Multi-user RBAC system.**

Three permission tiers:
- **owner** - Full access, can manage other users
- **sudo** - Full tool access, can't manage users
- **user** - Basic access, restricted tools

```json
{
    "users": [
        {
            "id": "admin",
            "name": "Admin",
            "role": "owner",
            "platforms": {"discord": "123456789"}
        }
    ]
}
```

Users are identified by platform ID (Discord ID, Telegram ID, etc.).

---

## presence.py

**Lines:** ~85 | **Typing/status indicators.**

Tells adapters when the agent is thinking, typing, or idle:

```python
await self.presence.set_typing(channel_id)   # "iTaK is typing..."
await self.presence.set_idle()                # Done
await self.presence.set_status("Processing")  # Custom status
```

---

## media.py

**Lines:** ~155 | **Image/audio/video pipeline.**

Handle media files across the agent's workflow:

```python
# Download and process an image
image = await self.media.download("https://example.com/photo.jpg")
description = await self.media.describe(image)  # Use vision model

# Generate an image (placeholder for DALL-E/ComfyUI integration)
result = await self.media.generate("A sunset over mountains")
```

---

## linter.py

**Lines:** ~120 | **Code quality gate.**

Runs basic quality checks on generated code before execution:

```python
result = self.linter.check(code, language="python")
if result.issues:
    for issue in result.issues:
        print(f"Line {issue.line}: {issue.message}")
```

Checks include: syntax validation, import verification, and basic style issues.
