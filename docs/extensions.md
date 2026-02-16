# Extensions Reference

## At a Glance
- Audience: Developers extending iTaK behavior via tools, prompts, models, and core modules.
- Scope: This page explains `Extensions Reference`.
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


> The 24 hook points for extending iTaK behavior with full async/await support.

## Overview

Extensions are the plugin system. iTaK has 24 hook points throughout its lifecycle. To add behavior at any point, drop a `.py` file in the corresponding `extensions/<hook_name>/` directory.

**No registration needed.** The agent auto-discovers and loads extension files at startup.

**Async/Sync Support:** Extensions can be either synchronous functions or async coroutines. The extension runner handles both safely.

---

## How Extensions Work

Every extension file must have an `execute()` function:

### Synchronous Extension
```python
# extensions/monologue_start/my_extension.py

def execute(agent, **kwargs):
    """This runs every time a new monologue starts."""
    agent.logger.log("custom", "Monologue started!")
    return "sync_result"
```

### Asynchronous Extension
```python
# extensions/monologue_start/my_async_extension.py

async def execute(agent, **kwargs):
    """This runs every time a new monologue starts (async version)."""
    await some_async_operation()
    agent.logger.log("custom", "Async monologue started!")
    return "async_result"
```

The `agent` parameter gives you access to the entire agent instance - memory, tools, config, everything.

---

## Extension Best Practices

### ✅ DO

1. **Use async for I/O operations**: Database queries, API calls, file operations
   ```python
   async def execute(agent, **kwargs):
       result = await agent.memory.search("query")
       return result
   ```

2. **Handle errors gracefully**: Extension errors are logged but don't crash the agent
   ```python
   def execute(agent, **kwargs):
       try:
           # Your code
           pass
       except Exception as e:
           agent.logger.log(EventType.WARNING, f"Extension failed: {e}")
           return None
   ```

3. **Check for subsystem availability**:
   ```python
   def execute(agent, **kwargs):
       if not hasattr(agent, "task_board") or agent.task_board is None:
           return  # Subsystem not available
       # Use task_board
   ```

4. **Return meaningful values**: Extensions can return values that get collected
   ```python
   async def execute(agent, **kwargs):
       return {"status": "ok", "data": result}
   ```

### ❌ DON'T

1. **Don't block the event loop**: Use async for long operations
2. **Don't modify global state without locks**: Extensions run sequentially per hook but multiple hooks may run
3. **Don't raise exceptions for normal conditions**: Return None or False instead
4. **Don't assume subsystems are available**: Always check before accessing

---

## Extension Runner Safety

The iTaK extension system has been enhanced with async-safe handling:

- **Automatic async detection**: Coroutines are automatically awaited
- **Error isolation**: One extension failure doesn't affect others
- **Logging**: All extension errors are logged with context
- **Mixed execution**: Sync and async extensions can coexist in the same hook

### Example: Mixed Sync/Async Hook
```python
# extensions/message_loop_start/tracker_sync.py
def execute(agent, **kwargs):
    agent.iteration_count += 1
    return "sync"

# extensions/message_loop_start/tracker_async.py
async def execute(agent, **kwargs):
    await agent.memory.save("iteration", agent.iteration_count)
    return "async"
```

Both extensions will execute correctly in order.

---

## All 24 Hook Points

### Lifecycle Hooks

| Hook | When | Use Case |
|------|------|----------|
| `agent_init` | Agent boots up | Initialize custom state |
| `monologue_start` | User sends a message | Reset per-conversation state |
| `monologue_end` | Agent finishes | Cleanup, save stats |
| `process_chain_end` | Everything is done | Final cleanup |

### Message Loop Hooks

| Hook | When | Use Case |
|------|------|----------|
| `message_loop_start` | Each iteration starts | Track iteration count |
| `message_loop_end` | Each iteration ends | Check budgets |
| `message_loop_prompts_before` | Before building prompts | Inject context |
| `message_loop_prompts_after` | After building prompts | Modify prompts |

### LLM Hooks

| Hook | When | Use Case |
|------|------|----------|
| `before_main_llm_call` | Right before LLM API call | Add context, modify messages |
| `system_prompt` | Building system prompt | Inject custom instructions |
| `util_model_call_before` | Before utility model call | Modify utility prompts |

### Tool Hooks

| Hook | When | Use Case |
|------|------|----------|
| `tool_execute_before` | Before a tool runs | Validate, log, block |
| `tool_execute_after` | After a tool runs | Post-process results |

### Streaming Hooks

| Hook | When | Use Case |
|------|------|----------|
| `response_stream` | Response streaming starts | UI updates |
| `response_stream_chunk` | Each streaming token | Real-time display |
| `response_stream_end` | Streaming finishes | Finalize display |
| `reasoning_stream` | Reasoning stream starts | Debug logging |
| `reasoning_stream_chunk` | Each reasoning token | Debug display |
| `reasoning_stream_end` | Reasoning finishes | Debug finalize |

### History Hooks

| Hook | When | Use Case |
|------|------|----------|
| `hist_add_before` | Before adding to history | Filter, modify |
| `hist_add_tool_result` | Tool result added to history | Summarize results |

### UI Hooks

| Hook | When | Use Case |
|------|------|----------|
| `user_message_ui` | User message received | Custom UI updates |
| `banners` | Dashboard loads | Add status banners |

### Error Hooks

| Hook | When | Use Case |
|------|------|----------|
| `error_format` | Error occurred | Custom error formatting |

---

## Built-in Extensions

### Task Tracker (`message_loop_start/task_tracker.py`)
Logs iteration count and monitors the monologue loop.

### Task Progress (`tool_execute_after/task_progress.py`)
Sends progress updates after tool execution.

### Task Complete (`process_chain_end/task_complete.py`)
Marks tasks as complete when the agent finishes.

### OS Detection (`agent_init/os_detect.py`)
Detects the host OS and loads appropriate skill guides.

### Self-Heal Hook (`tool_execute_after/self_heal.py`)
Triggers the self-healing engine when tools fail.

### Error Classifier (`error_format/error_classifier.py`)
Classifies errors into categories for better LLM understanding.

---

## Examples

### Example 1: Log every tool call to a file

```python
# extensions/tool_execute_before/tool_logger.py
import json
from datetime import datetime

def execute(agent, tool_name="", tool_args=None, **kwargs):
    """Log every tool call with timestamp."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "args": tool_args or {},
        "user": agent.context.user_id,
    }
    with open("data/tool_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

### Example 2: Inject custom context into system prompt

```python
# extensions/system_prompt/inject_context.py

def execute(agent, prompt="", **kwargs):
    """Add current date/time to every system prompt."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return prompt + f"\n\nCurrent date/time: {now}"
```

### Example 3: Block dangerous tools for non-owner users

```python
# extensions/tool_execute_before/access_control.py

RESTRICTED_TOOLS = ["code_execution", "delegate_task"]

def execute(agent, tool_name="", **kwargs):
    """Block restricted tools for non-owner users."""
    user = agent.context.user_id
    role = "user"

    if agent.user_registry:
        user_data = agent.user_registry.get_user(user)
        role = user_data.get("role", "user") if user_data else "user"

    if tool_name in RESTRICTED_TOOLS and role not in ("owner", "sudo"):
        raise PermissionError(f"Tool '{tool_name}' requires owner/sudo role")
```

### Example 4: Auto-save useful responses to memory

```python
# extensions/process_chain_end/auto_memorize.py

def execute(agent, **kwargs):
    """Save the agent's last response to memory if it was long/detailed."""
    response = agent.last_response
    if response and len(response) > 500:
        agent.memory.save(
            content=response[:1000],
            category="auto_saved",
            metadata={"source": "auto_memorize"}
        )
```
