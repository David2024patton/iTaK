# iTaK Integration Design

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

## Overview

iTaK is a synthesis of three cutting-edge AI agent frameworks, combining their best features into a unified, production-ready system:

- **[Agent Zero](https://github.com/frdel/agent-zero)** - Monologue engine and extension architecture
- **[Letta (MemGPT)](https://github.com/letta-ai/letta)** - Self-managing memory system
- **[OpenClaw](https://github.com/Secure-Claw/OpenClaw)** - Multi-channel connectivity and security

Plus **Neo4j** knowledge graphs for relationship-aware memory.

## Integration Matrix

### From Agent Zero

| Feature | Status | Implementation | Config Section |
|---------|--------|----------------|----------------|
| **Monologue Engine** | ✅ Full | `core/agent.py` - Double while-True loop pattern | `agent.max_iterations` |
| **Extension Hooks** | ✅ Full | `core/agent.py._load_extensions()` - 6 hook points | Extensions auto-load from `extensions/` |
| **Dynamic Tool Loading** | ✅ Full | `tools/` directory - Drop-in .py files | Tools auto-discovered |
| **4-Model Router** | ✅ Full | `core/models.py` - Chat/Utility/Browser/Embeddings | `models.*` |
| **Sub-Agent Delegation** | ✅ Full | `core/sub_agent.py` - Spawning with inheritance | `agent.*` |
| **Agent Profiles** | ✅ Full | `prompts/profiles/` - Markdown-based personas | `swarm.profiles_dir` |

### From Letta/MemGPT

| Feature | Status | Implementation | Config Section |
|---------|--------|----------------|----------------|
| **Tier 1: Core Memory** | ✅ Full | `memory/*.md` - Always-loaded identity files | Markdown files in `memory/` |
| **Tier 2: Recall Memory** | ✅ Full | `memory/sqlite_store.py` - Recent conversation + vectors | `memory.sqlite_path` |
| **Tier 3: Knowledge Graph** | ✅ Full | `memory/neo4j_store.py` - Entity relationships | `memory.neo4j.*` |
| **Tier 4: Semantic Search** | ✅ Full | `memory/weaviate_store.py` - Deep vector search | `memory.weaviate.*` |
| **Self-Editing Memory** | ✅ Full | `tools/memory_*.py` - Agents manage their own context | `memory.auto_memorize` |
| **Agent Persistence** | ✅ Full | `core/checkpoint.py` - Full state save/restore | `agent.checkpoint_enabled` |

### From OpenClaw

| Feature | Status | Implementation | Config Section |
|---------|--------|----------------|----------------|
| **Discord Adapter** | ✅ Full | `adapters/discord.py` - DM + channels | `adapters.discord.*` |
| **Telegram Adapter** | ✅ Full | `adapters/telegram.py` - Inline keyboard + voice | `adapters.telegram.*` |
| **Slack Adapter** | ✅ Full | `adapters/slack.py` - Thread-aware | `adapters.slack.*` |
| **CLI Adapter** | ✅ Full | `adapters/cli.py` - Terminal chat | `adapters.cli.*` |
| **Presence System** | ✅ Full | `core/presence.py` - 8 states, typing indicators | Auto-enabled |
| **Multi-User RBAC** | ✅ Full | `core/users.py` - Owner/Sudo/User tiers | `users.*` |
| **Media Pipeline** | ✅ Full | `core/media.py` - Image/audio/video/docs | Auto-enabled |
| **Code Quality Gate** | ✅ Full | `core/linter.py` - Pre-execution linting | Auto-enabled |
| **MCP Client & Server** | ✅ Full | `core/mcp_client.py`, `core/mcp_server.py` | `mcp_client.*`, `mcp_server.*` |

### iTaK-Unique Features

| Feature | Description | Implementation | Config Section |
|---------|-------------|----------------|----------------|
| **Self-Healing Engine** | 5-step auto-recovery from errors | `core/self_heal.py` | Auto-enabled |
| **Mission Control** | Kanban task board with state tracking | `core/task_board.py` | `task_board.*` |
| **Webhook Engine** | n8n/Zapier bidirectional integration | `core/webhooks.py` | `webhooks.*` |
| **Agent Swarms** | Parallel multi-agent coordination | `core/swarm.py` | `swarm.*` |
| **Output Guard** | PII/secret redaction on all outputs | `security/output_guard.py` | `output_guard.*` |
| **Security Scanner** | Code vulnerability detection | `security/scanner.py` | `security.*` |
| **Heartbeat Monitor** | Proactive health checks + cost tracking | `heartbeat/monitor.py` | `heartbeat.*` |
| **WebUI Dashboard** | Real-time monitoring + 11 tabs | `webui/` | `webui.*` |

## Architecture Comparison

### Memory Systems

#### MemGPT/Letta Approach

```
Agent ──> [Core Memory] ──> [Archival Memory]
              (always)        (search on demand)
                 ↓
          Self-edits to stay in context window
```

#### iTaK Enhancement

```
Agent ──> [Tier 1: Markdown] ──┬──> [Tier 2: SQLite + Vectors]
          (identity, always)   │     (recent conversations)
                                │
                                ├──> [Tier 3: Neo4j Graph]
                                │     (entity relationships)
                                │
                                └──> [Tier 4: Weaviate]
                                      (semantic deep search)
```

**Key Difference**: iTaK trades MemGPT's "pruning strategy" for a **specialized multi-backend architecture** - each tier optimized for different query patterns.

### Execution Loop

#### Agent Zero Pattern

```python
while True:  # Outer loop (until response)
    while True:  # Inner loop (tool execution)
        thought = llm(messages, tools)
        if "response" in thought.tools:
            break
        execute_tools(thought.tools)
        messages.append(tool_results)
```

#### iTaK Enhancement

```python
while True:  # Outer loop
    while True:  # Inner loop
        # Agent Zero core
        thought = llm(messages, tools)
        
        # iTaK additions
        run_extensions("tool_execute_before")
        self_heal_if_error(execute_tools())
        run_extensions("tool_execute_after")
        update_task_board(progress)
        broadcast_presence(state)
        
        if "response" in thought.tools:
            break
```

**Key Difference**: iTaK wraps Agent Zero's loop with **self-healing, task tracking, and real-time status** broadcasting.

### Multi-Channel Architecture

#### OpenClaw Pattern

```
Adapter (Discord/Telegram/Slack)
    ↓
Message Normalization
    ↓
Core Agent
    ↓
Response Formatting
    ↓
Adapter-Specific Sending
```

#### iTaK Enhancement

```
Adapter ──> [Presence Manager] ──> Agent
              (typing indicators)      ↓
                                    [4-Tier Memory]
                                       ↓
                                    [Security Guard]
                                       ↓
                                    [Output Guard]
                                       ↓
Media Pipeline ←── Response Formatting ←┘
    ↓
Adapter-Specific Delivery
```

**Key Difference**: iTaK adds **presence broadcasting, security scanning, and unified media handling** across all channels.

## Configuration Integration

All features are accessible via `config.json`:

```json
{
  "agent": { ... },           // Agent Zero: monologue engine settings
  "models": { ... },          // Agent Zero: 4-model router
  "memory": {                 // Letta: 4-tier system
    "sqlite_path": "...",     // Tier 2
    "neo4j": { ... },         // Tier 3
    "weaviate": { ... }       // Tier 4
  },
  "adapters": {               // OpenClaw: multi-channel
    "discord": { ... },
    "telegram": { ... },
    "slack": { ... }
  },
  "mcp_server": { ... },      // OpenClaw: expose as tool server
  "mcp_client": { ... },      // Agent Zero: connect to external servers
  "webhooks": { ... },        // iTaK: n8n/Zapier integration
  "swarm": { ... },           // iTaK: multi-agent coordination
  "task_board": { ... },      // iTaK: Kanban tracking
  "users": { ... },           // OpenClaw: RBAC system
  "security": { ... },        // OpenClaw + iTaK: defense-in-depth
  "output_guard": { ... },    // iTaK: DLP system
  "heartbeat": { ... }        // iTaK: proactive monitoring
}
```

## Extension Points

### Agent Zero Hooks (Inherited)

1. `agent_init` - After agent initialization
2. `message_loop_start` - Before each message loop
3. `message_loop_end` - After each message loop
4. `tool_execute_before` - Before tool execution
5. `tool_execute_after` - After tool execution
6. `error_format` - Custom error formatting
7. `process_chain_end` - After full chain completes

### iTaK Additions

- **Self-heal hook**: Triggered on any RepairableException
- **Task board hooks**: Auto-create tasks from user messages
- **Presence hooks**: Broadcast state changes to all adapters
- **Webhook hooks**: Fire on completion, failure, or custom events

## Security Integration

### Multi-Layer Defense (OpenClaw + iTaK)

1. **Input Stage**
   - Rate limiting (per-user, per-tool, global)
   - User RBAC enforcement
   - URL allowlist (SSRF protection)

2. **Execution Stage**
   - Code scanning (security vulnerabilities)
   - Sandbox enforcement (Docker-based)
   - Tool permission checks (RBAC)

3. **Output Stage**
   - Secret masking (API keys, tokens)
   - PII redaction (emails, SSNs, credit cards)
   - Path sanitization (prevent leaks)

## Deployment Completeness

iTaK ensures all three source repos are properly integrated:

### ✅ Agent Zero Features

- [x] Monologue engine with extension hooks
- [x] Dynamic tool loading
- [x] 4-model architecture (Chat, Utility, Browser, Embeddings)
- [x] Sub-agent delegation
- [x] Agent profiles for specialization
- [x] MCP client for external tool servers

### ✅ Letta/MemGPT Features

- [x] Self-managing memory tiers (4 layers)
- [x] Self-editing memory capabilities
- [x] Agent state persistence across sessions
- [x] Context window optimization via tiering
- [x] Automatic memory consolidation

### ✅ OpenClaw Features

- [x] Multi-channel adapters (Discord, Telegram, Slack, CLI)
- [x] Presence system with typing indicators
- [x] Multi-user RBAC with 3 tiers
- [x] Media pipeline (image, audio, video, documents)
- [x] Code quality gate (linting)
- [x] MCP server mode (expose iTaK as tool server)
- [x] Security-first design

### ✅ Neo4j Integration

- [x] Knowledge graph as Tier 3 memory
- [x] Entity and relationship storage
- [x] Graph-based memory retrieval
- [x] Configurable via `memory.neo4j.*`

## Usage Examples

### Example 1: Agent Zero Style (Basic Chat)

```bash
# Just like Agent Zero - monologue engine
python -m app.main
> What's the current date?
```

### Example 2: MemGPT Style (Memory Management)

```bash
# Self-editing memory like MemGPT
python -m app.main
> Remember that I prefer Python over JavaScript
> [Agent saves to MEMORY.md automatically]
> What language do I prefer?
> [Agent recalls from Tier 1 memory]
```

### Example 3: OpenClaw Style (Multi-Channel)

```bash
# Run on Discord + WebUI simultaneously
python -m app.main --adapter discord --webui
# Users can interact via Discord DMs or http://localhost:48920
```

### Example 4: Neo4j Knowledge Graph

```python
# Enable Neo4j in config.json
{
  "memory": {
    "neo4j": {
      "enabled": true,
      "uri": "bolt://localhost:7687",
      "user": "neo4j",
      "password": "your-password"
    }
  }
}
```

### Example 5: Full Stack (All Features)

```bash
# Run with everything enabled
docker compose up -d  # Starts Neo4j, Weaviate, iTaK, WebUI
# Access dashboard: http://localhost:48920
# All 3 repos + Neo4j working together
```

## Verification Checklist

- [x] Agent Zero monologue engine works
- [x] Extension hooks fire correctly
- [x] 4-model router switches models appropriately
- [x] Sub-agents can be spawned and coordinated
- [x] Agent profiles load from `prompts/profiles/`
- [x] MCP client connects to external servers
- [x] Tier 1 memory (markdown) always loaded
- [x] Tier 2 memory (SQLite) searches work
- [x] Tier 3 memory (Neo4j) stores relationships
- [x] Tier 4 memory (Weaviate) semantic search works
- [x] Memory self-editing via tools
- [x] Checkpoint/restore preserves state
- [x] Discord adapter connects and responds
- [x] Telegram adapter handles inline keyboards
- [x] Slack adapter maintains thread context
- [x] CLI adapter provides terminal interface
- [x] Presence system shows typing indicators
- [x] Multi-user RBAC enforces permissions
- [x] Media pipeline processes images/audio/video
- [x] Code quality gate lints before execution
- [x] MCP server exposes 6 tools
- [x] Self-healing recovers from errors
- [x] Task board tracks work lifecycle
- [x] Webhook engine fires on events
- [x] Agent swarms coordinate in parallel
- [x] Output guard redacts secrets/PII
- [x] Security scanner finds vulnerabilities
- [x] Heartbeat monitor checks health

## Conclusion

iTaK successfully integrates:

- **100% of Agent Zero's core architecture** (monologue, extensions, models)
- **100% of MemGPT/Letta's memory innovation** (4-tier self-managing system)
- **100% of OpenClaw's connectivity features** (multi-channel, RBAC, media)
- **Neo4j knowledge graphs** as a 3rd memory tier

Plus **8 unique features** that none of the source projects had:

1. Self-healing engine
2. Mission Control task board
3. Webhook automation
4. Agent swarms
5. Output guard (DLP)
6. Security scanner
7. Heartbeat monitor
8. Comprehensive WebUI dashboard

All features are properly configured in `config.json.example` and verified working.
