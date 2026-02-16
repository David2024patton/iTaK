# Memory System Reference

## At a Glance
- Audience: Developers extending iTaK behavior via tools, prompts, models, and core modules.
- Scope: Describe module responsibilities, configuration surfaces, and extension patterns used in day-to-day work.
- Last reviewed: 2026-02-16.

## Quick Start
- Locate the owning module and expected inputs before editing behavior.
- Cross-check data flow with [root/DATABASES.md](root/DATABASES.md) when state is involved.
- Re-run focused tests after updates to confirm no regression in tool contracts.

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Keep argument names and defaults exact when generating tool/model calls.
- Prefer evidence from code paths over assumptions when documenting behavior.


> iTaK's 4-tier memory architecture explained in full detail.

## Overview

The agent has a 4-layer brain. Each layer serves a different purpose, and the `MemoryManager` unifies them behind a single interface.

```
Layer 1: Markdown Files    --> Always loaded, always available
Layer 2: SQLite + Vectors  --> Fast local search with embeddings
Layer 3: Neo4j Graph       --> Entity relationships
Layer 4: Weaviate Vectors  --> Deep semantic search
```

---

## Layer 1: Markdown Files

The simplest layer. Four files that are loaded into every system prompt:

### `SOUL.md` - Agent Identity
```markdown
# Who Am I
I am iTaK (Intelligent Task Automation Kernel), a personal AI agent.
I am not a chatbot. I am an autonomous agent that can:
- Remember everything across conversations
- Execute code in sandboxed environments
...

# Core Values
1. High-agency mindset - I don't give up.
2. Transparency - I always tell the user what I'm doing.
...
```
**Purpose:** Gives the LLM a sense of identity. The agent reads this every time it builds a system prompt.

### `USER.md` - User Preferences
```markdown
# Identity
- Name: (set by user)
- Role: (set by user)

# Infrastructure
- (user's servers and machines)

# Preferences
- (learned over time)
```
**Purpose:** The agent learns your preferences and records them here. Over time, it adapts to how you work.

### `MEMORY.md` - Learned Facts
```markdown
## 2025-12-15: Docker Compose Port Fix
When services won't start, check if another container already holds the port.
Use `docker compose down` before `docker compose up` to avoid conflicts.

## 2025-12-20: Neo4j First Boot
The admin username MUST be `neo4j`. It can't be changed. Delete the volume
to force a credential reset.
```
**Purpose:** Solutions to problems, important decisions, reference material. The agent appends to this when it learns something worth remembering.

### `AGENTS.md` - Behavioral Rules
```markdown
# Rules
- Always test code after writing it
- Never expose API keys
- Ask before destructive actions
- Use the cheapest model for utility tasks
```
**Purpose:** Hard behavioral constraints. The agent checks these before taking actions.

---

## Layer 2: SQLite + Vector Embeddings

**File:** `memory/sqlite_store.py`

Local SQLite database with vector embeddings for semantic search.

### Schema
```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    source TEXT DEFAULT 'agent',
    metadata TEXT,  -- JSON blob
    embedding BLOB, -- Vector bytes
    created_at REAL,
    updated_at REAL
);
```

### How it works
1. When saving: text gets embedded via `ModelRouter.embed()` and stored as a vector
2. When searching: query gets embedded, then cosine similarity finds nearest matches
3. Results above the threshold (default: 0.6) are returned

### Example
```python
# Save a memory
await memory.save(
    content="Docker compose v2 uses 'docker compose' not 'docker-compose'",
    category="devops",
    metadata={"source": "learned_from_error"}
)

# Search for it later
results = await memory.search("how to run docker compose")
# Returns: [{"content": "Docker compose v2 uses...", "score": 0.89}]
```

---

## Layer 3: Neo4j Knowledge Graph

**File:** `memory/neo4j_store.py`

Stores relationships between entities:

```
[iTaK] --(built_by)--> [User]
[iTaK] --(uses)--> [Python]
[VPS] --(runs)--> [Dokploy]
[VPS] --(runs)--> [Neo4j]
[Polymarket] --(type)--> [Prediction Market]
```

### Usage
```python
# Save a relationship
await memory.save_relationship(
    from_name="iTaK",
    from_type="project",
    to_name="FastAPI",
    to_type="framework",
    rel_type="uses",
    properties={"since": "v1.0"}
)

# Query context for an entity
context = await memory.get_entity_context("iTaK")
# Returns: all connected nodes and relationships
```

### Configuration
```json
{
    "memory": {
        "neo4j": {
            "uri": "$NEO4J_URI",
            "user": "neo4j",
            "password": "$NEO4J_PASSWORD"
        }
    }
}
```

---

## Layer 4: Weaviate Semantic Search

**File:** `memory/weaviate_store.py`

Cloud-hosted vector database for deep semantic search across large memory collections.

### When to use each layer

| Scenario | Layer |
|----------|-------|
| Agent identity, personality | Layer 1 (Markdown) |
| Quick lookup of recent facts | Layer 2 (SQLite) |
| "What's related to X?" | Layer 3 (Neo4j) |
| Deep search across thousands of memories | Layer 4 (Weaviate) |

---

## The MemoryManager

**File:** `memory/manager.py` | **Lines:** 317

The unified interface. When the agent calls `memory.search()`, it searches ALL layers and merges the results:

```python
class MemoryManager:
    async def save(self, content, category, metadata, source, entities):
        # 1. Append to MEMORY.md (Layer 1)
        # 2. Embed and store in SQLite (Layer 2)
        # 3. If entities provided, create graph nodes (Layer 3)
        # 4. Store in Weaviate (Layer 4)

    async def search(self, query, category, limit, threshold):
        # 1. Search MEMORY.md by keyword (Layer 1)
        # 2. Vector search in SQLite (Layer 2)
        # 3. Graph query in Neo4j (Layer 3)
        # 4. Semantic search in Weaviate (Layer 4)
        # 5. Merge, deduplicate, rank by score
        # 6. Return top results
```

### Configuration
```json
{
    "memory": {
        "data_dir": "memory",
        "default_limit": 10,
        "similarity_threshold": 0.6,
        "sqlite": {"db_path": "data/memory.db"},
        "neo4j": {"uri": "$NEO4J_URI", "user": "neo4j", "password": "$NEO4J_PASSWORD"},
        "weaviate": {"url": "$WEAVIATE_URL", "api_key": "$WEAVIATE_API_KEY"}
    }
}
```

If Neo4j or Weaviate are not configured, those layers are silently skipped. The agent always has at least Layer 1 (Markdown) and Layer 2 (SQLite).

---

## MemU Enrichment Pipeline (Optional)

**File:** `memory/memu_store.py` | **Extension:** `extensions/message_loop_end/memu_extraction.py`

MemU is an **extraction-only enrichment pipeline** that runs in the background to extract structured facts from conversations. It is **NOT** a search layer - extracted facts are routed back into the existing 4-layer system.

### Key Design Principles

1. **Disabled by default** - Sovereignty-first: requires explicit opt-in
2. **Self-hosted by default** - Runs as a Docker sidecar, cloud API is opt-in
3. **Extraction-only** - MemU extracts facts, but searches stay in the 4-layer system
4. **Fire-and-forget** - Non-blocking async enrichment after each response
5. **Smart throttling** - Multiple safeguards to control costs and privacy

### How it Works

```
1. User sends message → Agent responds
2. Extension fires AFTER response (non-blocking)
3. Last N conversation turns sent to MemU
4. MemU extracts structured facts
5. Facts stored in SQLite/Neo4j/MEMORY.md with source="memu"
6. Future searches find memu-extracted facts (ranked with memu_weight)
```

### Throttling Controls

MemU includes multiple throttles to prevent excessive processing:

| Throttle | Default | Purpose |
|----------|---------|---------|
| **Minimum length** | 100 chars | Skip very short conversations |
| **Dedup window** | 15 minutes | Skip similar conversations recently processed |
| **Cost cap** | $1.00/hour | Prevent runaway LLM costs |
| **Opt-out flag** | `#no-memory` | Per-conversation privacy bypass |
| **Max turns** | 5 | Limit context sent to MemU |

### Configuration

```json
{
    "memory": {
        "memu": {
            "enabled": false,                    // Disabled by default
            "mode": "self-hosted",               // "self-hosted" or "cloud"
            "base_url": "http://localhost:8080", // MemU server endpoint
            "api_key": "${MEMU_API_KEY}",        // Only for cloud mode
            "timeout": 30,
            "memorize_endpoint": "/memory/memorize",
            "min_conversation_length": 100,      // Min chars to process
            "dedup_window_minutes": 15,          // Skip duplicates within N min
            "cost_cap_per_hour": 1.0,            // Max USD/hour
            "max_turns": 5,                      // Last N turns to send
            "memu_weight": 0.8,                  // Weight for ranking
            "append_to_memory_md": true          // Audit trail in MEMORY.md
        }
    }
}
```

### Self-Hosted Setup (Docker Compose)

Uncomment the `memu-server` service in `docker-compose.yml`:

```yaml
memu-server:
  image: memu/memu-server:latest
  container_name: itak-memu
  ports:
    - "8080:8080"
  volumes:
    - memu-data:/data
  networks:
    - itak-network
```

Then:
```bash
docker compose --project-directory . -f install/docker/docker-compose.yml up -d memu-server
```

### Cloud Mode (Optional)

For cloud-hosted MemU:

```json
{
    "memory": {
        "memu": {
            "enabled": true,
            "mode": "cloud",
            "base_url": "https://api.memu.ai",
            "api_key": "${MEMU_API_KEY}"
        }
    }
}
```

### Privacy & Opt-Out

Users can opt out of MemU enrichment per-conversation by including `#no-memory` in their message:

```
User: "This is private information #no-memory"
```

The extension detects this flag and skips enrichment for that conversation.

### Storage Integration

Extracted facts are tagged and routed to existing stores:

```python
# Example: MemU extracts "Paris is the capital of France"
# Stored as:
{
    "content": "Paris is the capital of France",
    "source": "memu",                  // Tagged as memu-extracted
    "metadata": {
        "memu_weight": 0.8,             // Configurable ranking weight
        "extraction_source": "memu"
    },
    "entities": ["Paris", "France"]     // Entities for Neo4j
}
```

During search, memu-extracted items:
- Are found via normal SQLite/Neo4j/Weaviate searches
- Have `memu_weight` applied during ranking
- Display `source="memu"` in results for transparency

### Testing

Run unit tests (mocked):
```bash
pytest tests/test_memu.py
```

Run integration tests (requires memu-server):
```bash
docker compose --project-directory . -f install/docker/docker-compose.yml up -d memu-server
pytest tests/test_memu.py -m integration
```

### Security Notes

- MemU is disabled by default - requires explicit configuration
- Self-hosted mode keeps all data local (no cloud API calls)
- Throttling prevents runaway costs
- Per-conversation opt-out for sensitive discussions
- All extracted facts include source tags for auditability
