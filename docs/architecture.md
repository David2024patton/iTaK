# iTaK Architecture Guide

## At a Glance

- Audience: Developers integrating channels, APIs, and system architecture components.
- Scope: Explain component boundaries, integration points, and expected behavior across interfaces.
- Last reviewed: 2026-02-16.

## Quick Start

- Identify the integration boundary first (adapter, API endpoint, or UI component).
- Trace implementation details from [root/IMPLEMENTATION_SUMMARY.md](root/IMPLEMENTATION_SUMMARY.md).
- Validate behavior with smoke checks after each configuration change.

## Deep Dive

The detailed content for this topic starts below.

## AI Notes

- Use explicit endpoint names, adapter flags, and file paths for automation tasks.
- Note root endpoints vs `/api/*` endpoints to avoid integration mismatches.

> This document explains how iTaK works from the ground up. Every component, every flow, every decision. If you're an LLM reading this to understand your own code - this is your map.

## Table of Contents

- [The Big Picture](#the-big-picture)
- [The Monologue Loop](#the-monologue-loop)
- [Data Flow](#data-flow)
- [Subsystem Map](#subsystem-map)
- [File Structure](#file-structure)
- [How the Pieces Connect](#how-the-pieces-connect)

---

## The Big Picture

iTaK is an **autonomous AI agent** that operates in a monologue loop. It is NOT a chatbot - it doesn't just respond to messages. It thinks, plans, uses tools, and iterates until the task is done.

The architecture is inspired by [Agent Zero](https://github.com/frdel/agent-zero)'s double while-True loop pattern, enhanced with:

- 4-tier memory system (Markdown - SQLite - Neo4j - Weaviate)
- 24 extension hooks for plugin behavior
- Self-healing error recovery
- Output guard (PII/secret scrubbing on all output)
- WebUI dashboard with real-time monitoring
- Multi-platform adapters (Discord, Telegram, Slack, CLI)

---

## The Monologue Loop

This is the heart of iTaK. The agent runs in a double while-True loop:

```
User sends message
         |
         v
┌──────────────────────────────────────┐
│  OUTER LOOP (handles intervention)   │
│  ┌────────────────────────────────┐  │
│  │  INNER LOOP (LLM reasoning)   │  │
│  │                                │  │
│  │  1. Build system prompt        │  │
│  │  2. Prepare message history    │  │
│  │  3. Call LLM                   │  │
│  │  4. Parse JSON response        │  │
│  │  5. Extract tool call          │  │
│  │  6. Execute tool               │  │
│  │  7. Add result to history      │  │
│  │  8. Check: break_loop?         │──│──> YES: Return response
│  │  9. Go back to step 1          │  │
│  │                                │  │
│  └────────────────────────────────┘  │
│  Check for user intervention ────────│──> Restart inner loop
└──────────────────────────────────────┘
```

### How it works in code

The `Agent.monologue()` method in `core/agent.py` is the engine:

```python
async def monologue(self, user_message: str):
    # Add user message to history
    self.history.append({"role": "user", "content": user_message})

    while True:  # Outer loop - intervention handling
        try:
            while True:  # Inner loop - LLM reasoning
                # Build prompt with memory context
                system_prompt = self._build_system_prompt()
                messages = self._prepare_messages()

                # Call the LLM
                response = await self.model_router.chat(messages)

                # Parse and execute tool call
                tool_result, should_break = await self._process_tools(response)

                if should_break:
                    return self.last_response

                # Repeat detection
                if self._detect_repeat(response):
                    self.history.append({"role": "system",
                        "content": "You appear to be repeating yourself."})

        except InterventionException:
            continue  # User interrupted, restart inner loop
```

### Key Concepts

- **The response tool is the ONLY way to break the loop.** Without calling `response`, the agent keeps iterating.
- **Interventions** allow users to inject messages mid-execution. The outer loop catches these and restarts the inner loop with the new context.
- **Repeat detection** prevents the LLM from getting stuck. If it says the same thing twice, it gets nudged.
- **Checkpoints** save state every N steps, so recovery is possible after crashes.

---

## Data Flow

Here's the complete flow of a message through the system:

```
User (Discord/Telegram/Slack/CLI)
         |
         v
    BaseAdapter.handle_message()
         |
         v
    Agent.monologue(user_message)
         |
    ┌────┴────┐
    │ Memory  │ <-- Check SOUL.md, USER.md, MEMORY.md, AGENTS.md
    │ Search  │ <-- Search SQLite, Neo4j, Weaviate
    └────┬────┘
         |
         v
    ModelRouter.chat()  --> LLM API (Gemini/OpenAI/Ollama)
         |
         v
    Parse JSON response
         |
         v
    SecurityScanner.scan_code()  --> Check for dangerous patterns
         |
         v
    Tool execution (code_execution, web_search, etc.)
         |
         v
    SelfHealEngine.heal()  --> If tool fails, try to recover
         |
         v
    ResponseTool.execute()
         |
         v
    OutputGuard.sanitize()  --> Scrub PII/secrets from output
         |
         v
    BaseAdapter._sanitize_output()
         |
         v
    User sees the response
```

---

## Subsystem Map

| Subsystem | File(s) | Purpose |
|-----------|---------|---------|
| **Core Engine** | `core/agent.py` | Monologue loop, tool dispatch, extension hooks |
| **Model Router** | `core/models.py` | 4-model routing (chat/utility/browser/embeddings) |
| **Memory** | `memory/manager.py` | Unified interface to all 4 memory layers |
| **Security** | `security/*.py` | Scanner, secrets, rate limiter, output guard |
| **Tools** | `tools/*.py` | Code execution, web search, memory, browser, delegation |
| **Extensions** | `extensions/*/` | 24 hook points for plugin behavior |
| **Adapters** | `adapters/*.py` | Discord, Telegram, Slack, CLI |
| **WebUI** | `webui/server.py` | FastAPI dashboard + WebSocket monitoring |
| **Prompts** | `prompts/*.md` | System prompt templates |
| **Self-Healing** | `core/self_heal.py` | 5-step error recovery pipeline |
| **MCP Client** | `core/mcp_client.py` | Connect to external MCP tool servers |
| **MCP Server** | `core/mcp_server.py` | Expose iTaK tools to other agents |
| **Webhooks** | `core/webhooks.py` | n8n/Zapier integration |
| **Swarm** | `core/swarm.py` | Multi-agent coordination |
| **Users** | `core/users.py` | Multi-user RBAC |
| **Presence** | `core/presence.py` | Typing/status indicators |
| **Heartbeat** | `heartbeat/monitor.py` | System health monitoring |

---

## File Structure

```
iTaK/
├── app/main.py                # Entry point - boots the agent
├── config.json                # Configuration (never committed)
├── install/config/config.json.example  # Template configuration
├── .env                       # Secrets (never committed)
├── install/config/.env.example # Template secrets
├── install/docker/Dockerfile  # Container build
├── install/docker/docker-compose.yml  # Full stack deployment
├── install/requirements/requirements.txt  # Python dependencies
│
├── core/                      # The brain
│   ├── agent.py               # Monologue engine (763 lines)
│   ├── models.py              # 4-model LLM router
│   ├── logger.py              # Structured event logging
│   ├── progress.py            # Progress tracking + broadcasting
│   ├── checkpoint.py          # Crash recovery checkpoints
│   ├── task_board.py          # Task management (Kanban)
│   ├── self_heal.py           # 5-step error recovery (422 lines)
│   ├── sub_agents.py          # Spawn specialized child agents
│   ├── mcp_client.py          # Connect to external MCP servers
│   ├── mcp_server.py          # Expose iTaK as MCP server
│   ├── webhooks.py            # n8n/Zapier webhook engine
│   ├── swarm.py               # Multi-agent coordination
│   ├── users.py               # Multi-user RBAC system
│   ├── presence.py            # Typing/status for adapters
│   ├── media.py               # Image/audio/video pipeline
│   └── linter.py              # Code quality gate
│
├── memory/                    # 4-tier storage
│   ├── manager.py             # Unified memory interface
│   ├── sqlite_store.py        # Layer 2 - embedded vector DB
│   ├── neo4j_store.py         # Layer 3 - knowledge graph
│   ├── weaviate_store.py      # Layer 4 - semantic search
│   ├── SOUL.md                # Layer 1 - agent identity
│   ├── USER.md                # Layer 1 - user preferences
│   ├── MEMORY.md              # Layer 1 - learned facts
│   └── AGENTS.md              # Layer 1 - behavioral rules
│
├── security/                  # Defense-in-depth
│   ├── secrets.py             # Secret detection + masking
│   ├── scanner.py             # Code vulnerability scanner
│   ├── rate_limiter.py        # Rate limiting engine
│   └── output_guard.py        # PII/secret redaction (DLP)
│
├── tools/                     # Agent capabilities
│   ├── base.py                # BaseTool interface
│   ├── response.py            # Break the loop (CRITICAL)
│   ├── code_execution.py      # Python/Node/Shell execution
│   ├── web_search.py          # SearXNG web search
│   ├── memory_save.py         # Save to memory
│   ├── memory_load.py         # Search memory
│   ├── knowledge_tool.py      # Knowledge graph queries
│   ├── browser_agent.py       # Vision-capable web browser
│   └── delegate_task.py       # Spawn sub-agent
│
├── adapters/                  # Communication platforms
│   ├── base.py                # Shared adapter interface
│   ├── cli.py                 # Terminal adapter
│   ├── discord.py             # Discord bot
│   ├── telegram.py            # Telegram bot
│   └── slack.py               # Slack bot
│
├── extensions/                # 24 hook points
│   ├── agent_init/            # After agent boots
│   ├── monologue_start/       # Before first LLM call
│   ├── message_loop_start/    # Start of inner loop
│   ├── before_main_llm_call/  # Right before LLM API call
│   ├── tool_execute_before/   # Before tool runs
│   ├── tool_execute_after/    # After tool runs
│   ├── process_chain_end/     # After monologue ends
│   └── ... (24 total)         # See extensions.md for all
│
├── prompts/                   # LLM instructions
│   ├── agent.system.main.md   # Core system prompt
│   ├── agent.system.main.role.md        # Personality
│   ├── agent.system.main.solving.md     # Problem-solving
│   ├── agent.system.tool.*.md           # Per-tool prompts
│   └── profiles/              # Specialized personas
│
├── skills/                    # Downloadable capabilities
│   ├── SKILL.md               # Skill format spec
│   ├── code_execution.md      # Code execution guide
│   ├── web_research.md        # Web research guide
│   ├── docker_ops.md          # Docker operations
│   └── os_*.md                # OS-specific guides
│
├── webui/                     # Monitoring dashboard
│   ├── server.py              # FastAPI + WebSocket (426 lines)
│   └── static/index.html      # Single-page dashboard
│
├── heartbeat/                 # Health monitoring
│   └── monitor.py             # Periodic system checks
│
├── helpers/                   # Shared utilities
│   └── utils.py               # Common functions
│
└── data/                      # Runtime data (gitignored)
    ├── users.json             # User registry
    └── memory.db              # SQLite database
```

---

## How the Pieces Connect

### Startup Sequence

```python
# main.py
agent = Agent(config=config)       # 1. Load config, init all subsystems
await agent.startup()              # 2. Connect memory stores, start heartbeat
adapter = DiscordAdapter(agent)    # 3. Create platform adapter
await adapter.start()              # 4. Start listening for messages
start_webui(agent)                 # 5. Launch monitoring dashboard
```

### What happens when you send a message

1. **Adapter** receives the message (e.g., Discord bot gets a `!ask` command)
2. **Adapter** calls `agent.monologue(user_message)`
3. **Agent** builds the system prompt from `prompts/*.md` + memory context
4. **Agent** calls the LLM via `ModelRouter`
5. **LLM** returns a JSON with `tool_name` and `tool_args`
6. **Agent** looks up the tool, runs security scan, executes it
7. **Tool result** goes back into history
8. **Agent** calls LLM again with updated context
9. Eventually, LLM calls the `response` tool
10. **Output Guard** scrubs the response for PII/secrets
11. **Adapter** delivers the sanitized response to the user

### Extension Hook Lifecycle

```
agent_init         --> Agent boots
monologue_start    --> User sends message
system_prompt      --> Building prompt  (can modify it)
message_loop_start --> Inner loop iteration
before_main_llm_call --> About to call LLM
response_stream*   --> LLM streaming tokens
tool_execute_before --> About to run a tool
tool_execute_after  --> Tool just finished
message_loop_end   --> Inner loop iteration done
monologue_end      --> Agent finished reasoning
process_chain_end  --> Everything is done
```

Every hook point is a directory under `extensions/`. Drop a Python file in any of them and it runs automatically. No registration needed.
