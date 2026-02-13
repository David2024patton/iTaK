<p align="center">
  <h1 align="center">🧠 iTaK — Intelligent Task Automation Kernel</h1>
  <p align="center">
    <em>If <a href="https://github.com/frdel/agent-zero">Agent Zero</a> and <a href="https://github.com/cpacker/MemGPT">MemGPT</a> had a baby… and <a href="https://github.com/Secure-Claw/OpenClaw">OpenClaw</a> was the godfather.</em>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python">
    <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/Version-4.0-orange" alt="Version">
    <img src="https://img.shields.io/badge/Status-Active-brightgreen" alt="Status">
  </p>
</p>

---

**iTaK** is a modular, self-healing AI agent framework that combines Agent Zero's monologue engine with MemGPT's infinite memory architecture and OpenClaw's multi-channel connectivity. It's not just another chatbot — it's an autonomous coding assistant, DevOps engineer, and research analyst that remembers everything, fixes its own mistakes, and works across Discord, Telegram, Slack, and a web dashboard simultaneously.

## 🎯 What Makes iTaK Different

| Feature | ChatGPT / Copilot | Agent Zero | iTaK |
|---------|-------------------|------------|------|
| Multi-channel (Discord, Telegram, Slack) | ❌ | ❌ | ✅ |
| Self-healing on errors | ❌ | ❌ | ✅ |
| 4-tier persistent memory (MemGPT-style) | ❌ | Partial | ✅ |
| Multi-agent swarms | ❌ | Basic | ✅ |
| MCP client AND server | ❌ | ❌ | ✅ |
| Kanban task board (Mission Control) | ❌ | ❌ | ✅ |
| n8n / Zapier webhook integration | ❌ | ❌ | ✅ |
| Multi-user RBAC (owner/sudo/user) | ❌ | ❌ | ✅ |
| Built-in code quality gate (linting) | ❌ | ❌ | ✅ |
| Real-time WebUI dashboard | ❌ | ✅ | ✅ |
| Crash recovery & checkpoints | ❌ | ❌ | ✅ |

---

## ✨ Feature List

### 🧠 Core Engine
- **Double-loop monologue engine** — Agent Zero-style `while True` loop that thinks, acts, and only stops when it explicitly decides to respond
- **LiteLLM model router** — Use any LLM (OpenAI, Anthropic, Gemini, local Ollama) with automatic fallback chains
- **Extension hooks** — 8 hook points for plugins (`agent_init`, `message_loop_start`, `tool_execute_before/after`, etc.)
- **Streaming responses** — Real-time token streaming with WebSocket broadcasting

### 🧬 Memory (MemGPT-Inspired)
- **Tier 1 — Core Context**: Always-loaded identity, personality, active instructions
- **Tier 2 — Recall Memory**: Recent conversation history (auto-managed FIFO)
- **Tier 3 — Archival Memory**: Searchable long-term storage (SQLite + vector embeddings)
- **Tier 4 — Knowledge Graph**: Neo4j-backed entity relationships with GraphRAG

### 🛡️ Security
- **Secret management** — Auto-detect and mask API keys in logs and outputs
- **Security scanner** — Static analysis on generated code for vulnerabilities
- **Rate limiting** — Per-user, per-tool, and global rate limits
- **Multi-user RBAC** — 3-tier permission system (owner → sudo → user) with per-tool enforcement

### 🔧 Tool System
- **Dynamic tool loading** — Drop a `.py` file in `tools/`, it's instantly available
- **Code execution** — Sandboxed Python/shell execution with timeout
- **Web search** — SearXNG / DuckDuckGo integration
- **Browser automation** — Playwright-based web interaction
- **File operations** — Read, write, edit with security checks
- **Memory tools** — Save, search, delete, manage all 4 tiers

### 🩹 Self-Healing Engine
- **5-step auto-recovery pipeline**: Classify error → Check memory for past fixes → LLM reasoning → Web research → Learn from fix
- **Error classification** by category (syntax, runtime, network, auth, resource, logic) and severity
- **Retry budgets** with exponential backoff — won't loop forever

### 📋 Mission Control (Task Board)
- **Kanban-style task tracking**: `inbox` → `in_progress` → `review` → `done` / `failed`
- **SQLite-backed persistence** — Tasks survive restarts
- **Auto-tracking** — Tasks created from user requests, progress updated during execution
- **Dashboard view** — Full CRUD via REST API

### 🔌 MCP (Model Context Protocol)
- **MCP Client** — Connect to external MCP tool servers (GitHub, filesystem, databases)
- **MCP Server** — Expose iTaK as a tool server for Cursor, VS Code, n8n, other agents
- **6 exposed tools**: `send_message`, `search_memory`, `list_tasks`, `get_task`, `create_task`, `get_status`
- **Bearer token auth** — Secure external access

### 🌐 Webhook Engine (n8n / Zapier)
- **Inbound webhooks** — External services POST tasks to iTaK
- **Outbound event hooks** — Fire webhooks on `task_completed`, `error_critical`, `daily_report`
- **Callback URLs** — Results sent back to the caller automatically
- **Secret-based auth** — Verify inbound requests

### 🐝 Agent Swarms
- **Parallel sub-agent execution** — Multiple specialists working simultaneously
- **3 execution strategies**: Parallel, Sequential, Pipeline (output → next input)
- **4 merge strategies**: Concat, Summarize (LLM), Best, Custom
- **Agent profiles** — Researcher, Coder, DevOps (custom profiles via markdown)

### 📡 Multi-Channel Adapters
- **CLI** — Terminal-based chat
- **Discord** — Full bot with DM + channel support
- **Telegram** — Inline keyboard + voice support
- **Slack** — Thread-aware responses
- **WebUI Dashboard** — Real-time monitoring + chat

### 🎭 Presence System
- **8 agent states**: idle, thinking, tool_use, searching, writing, deploying, healing, error
- **Cross-adapter broadcasting** — Discord typing indicators, dashboard status badges
- **Auto-timeout** — "⏳ Still working..." after 60 seconds of activity

### 📎 Media Pipeline
- **Inbound**: Download, classify, extract content (images → vision model, audio → Whisper, docs → text)
- **Outbound**: Per-adapter file sending with size limit enforcement
- **Room-scoped storage** with JSON manifests

### 💚 Heartbeat & Reliability
- **Periodic health checks** with configurable intervals
- **Crash recovery** — Checkpoint/restore system preserves agent state
- **Cost tracking** — Budget caps with warnings and hard stops
- **Log rotation** — 24-hour JSONL + SQLite dual storage

---

## 📁 Project Structure

```
iTaK/
├── main.py                    # Entry point — launch with any adapter
├── config.json.example        # Configuration template
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container deployment
├── docker-compose.yml         # Full stack deployment
│
├── core/                      # 🧠 Engine
│   ├── agent.py               # Monologue engine (v4)
│   ├── models.py              # LiteLLM router with fallback chains
│   ├── checkpoint.py          # Crash recovery
│   ├── logger.py              # Structured logging (14 event types)
│   ├── progress.py            # Progress tracking + WebSocket broadcast
│   ├── self_heal.py           # 5-step auto-recovery
│   ├── task_board.py          # Mission Control Kanban board
│   ├── mcp_client.py          # Connect to external MCP servers
│   ├── mcp_server.py          # Expose iTaK as MCP server
│   ├── webhooks.py            # n8n/Zapier integration
│   ├── swarm.py               # Multi-agent coordination
│   ├── users.py               # Multi-user RBAC
│   ├── presence.py            # Cross-adapter status
│   ├── media.py               # Unified media pipeline
│   ├── sub_agent.py           # Sub-agent spawning
│   └── linter.py              # Code quality gate
│
├── adapters/                  # 📡 Communication channels
│   ├── cli.py                 # Terminal adapter
│   ├── discord.py             # Discord bot
│   ├── telegram.py            # Telegram bot
│   └── slack.py               # Slack bot
│
├── memory/                    # 🧬 4-tier memory system
│   ├── manager.py             # Memory orchestrator
│   ├── sqlite_store.py        # Tier 3: Archival
│   ├── weaviate_store.py      # Vector search
│   └── neo4j_store.py         # Tier 4: Knowledge graph
│
├── security/                  # 🛡️ Security subsystem
│   ├── secrets.py             # Secret detection & masking
│   ├── scanner.py             # Code vulnerability scanner
│   └── rate_limiter.py        # Rate limiting
│
├── tools/                     # 🔧 Agent tools (auto-loaded)
├── extensions/                # 🔌 Hook-based plugins
├── prompts/                   # 📝 System prompts & profiles
│   └── profiles/              # Agent personality profiles
├── heartbeat/                 # 💚 Health monitoring
├── webui/                     # 🖥️ Dashboard server + frontend
├── skills/                    # 📚 Reusable skill modules
└── tests/                     # 🧪 Test suite
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **At least one LLM API key** (OpenAI, Anthropic, Gemini, or local Ollama)

### 1. Clone

```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
```

### 2. Install Dependencies

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
cp config.json.example config.json
```

Edit `.env` with your API keys:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
# Or use local Ollama (no key needed)
```

Edit `config.json` to set your preferred models, adapters, and features.

### 4. Run

```bash
# CLI mode (terminal chat)
python main.py

# With WebUI dashboard
python main.py --webui

# Discord bot
python main.py --adapter discord --webui

# WebUI only (no chat adapter)
python main.py --webui-only
```

### 🐳 Docker

```bash
docker-compose up -d
```

---

## ⚙️ Configuration

### `config.json` (key sections)

```json
{
  "models": {
    "primary": { "provider": "openai", "model": "gpt-4o" },
    "fast": { "provider": "openai", "model": "gpt-4o-mini" },
    "local": { "provider": "ollama", "model": "qwen2.5-coder" }
  },
  "adapters": {
    "discord": { "token": "BOT_TOKEN", "prefix": "!" },
    "telegram": { "token": "BOT_TOKEN" }
  },
  "memory": {
    "archival_backend": "sqlite",
    "graph_backend": "neo4j"
  },
  "mcp_server": {
    "enabled": true,
    "token": "your-secret-token"
  },
  "integrations": {
    "inbound_webhook_secret": "your-webhook-secret",
    "outbound": {
      "n8n": {
        "url": "https://n8n.example.com/webhook/itak",
        "events": ["task_completed", "error_critical"]
      }
    }
  }
}
```

---

## 🖥️ WebUI Dashboard

The dashboard provides real-time monitoring at `http://localhost:48920`:

- **Chat** — Talk to the agent from your browser
- **Mission Control** — Kanban task board
- **Memory** — Search and browse all 4 memory tiers
- **Tools** — View loaded tools and their schemas
- **Users** — Manage users and permissions (owner only)
- **Logs** — Structured event log with filtering
- **Subsystems** — Health status of all components

### REST API Highlights

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/stats` | Agent statistics |
| `POST /api/chat` | Send a message |
| `GET /api/tasks` | List tasks |
| `POST /api/webhook` | Inbound webhook |
| `GET /api/users` | List users |
| `GET /api/presence` | Agent status |
| `GET /api/subsystems` | All subsystem health |
| `POST /mcp/messages` | MCP JSON-RPC endpoint |

---

## 🤝 Inspirations & Credits

iTaK stands on the shoulders of giants:

- **[Agent Zero](https://github.com/frdel/agent-zero)** — The monologue engine pattern, extension hooks, sub-agent delegation
- **[MemGPT / Letta](https://github.com/cpacker/MemGPT)** — Self-managing memory tiers, context window optimization
- **[OpenClaw](https://github.com/Secure-Claw/OpenClaw)** — Multi-channel adapters, presence system, media pipeline, security-first design
- **[LiteLLM](https://github.com/BerriAI/litellm)** — Universal LLM provider abstraction

---

## 📜 License

MIT — Build whatever you want with it.

---

<p align="center">
  <strong>Built with 🧠 by <a href="https://github.com/David2024patton">David Patton</a></strong>
  <br>
  <em>"An AI agent that remembers, heals, and never sleeps."</em>
</p>
