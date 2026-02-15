# Configuration Reference

> Every config option in `config.json` explained.

## Overview

iTaK uses a single `config.json` for all configuration. Secrets use `$ENV_VAR` syntax and are resolved at runtime from `.env` or environment variables.

**Never commit `config.json` to git.** Use `config.json.example` as a template.

---

## Complete Config Structure

```json
{
    "agent": {
        "name": "iTaK",
        "version": "0.1.0",
        "max_iterations": 25,
        "timeout_seconds": 300,
        "repeat_detection": true,
        "checkpoint_enabled": true,
        "checkpoint_interval_steps": 3
    },

    "models": {
        "chat": {
            "provider": "litellm",
            "model": "gemini/gemini-2.5-pro-preview-05-06",
            "temperature": 0.7,
            "max_tokens": 8192,
            "context_window": 1000000,
            "api_key": "$GOOGLE_API_KEY"
        },
        "utility": {
            "provider": "litellm",
            "model": "gemini/gemini-2.0-flash",
            "temperature": 0.3,
            "max_tokens": 4096,
            "api_key": "$GOOGLE_API_KEY"
        },
        "browser": {
            "provider": "litellm",
            "model": "gemini/gemini-2.5-pro-preview-05-06",
            "temperature": 0.3,
            "api_key": "$GOOGLE_API_KEY"
        },
        "embeddings": {
            "provider": "litellm",
            "model": "text-embedding-3-small",
            "dimensions": 768,
            "api_key": "$OPENAI_API_KEY"
        }
    },

    "memory": {
        "data_dir": "memory",
        "default_limit": 10,
        "similarity_threshold": 0.6,
        "sqlite": {
            "db_path": "data/memory.db"
        },
        "neo4j": {
            "uri": "$NEO4J_URI",
            "user": "neo4j",
            "password": "$NEO4J_PASSWORD"
        },
        "weaviate": {
            "url": "$WEAVIATE_URL",
            "api_key": "$WEAVIATE_API_KEY"
        },
        "memu": {
            "enabled": false,
            "mode": "self-hosted",
            "base_url": "http://localhost:8080",
            "api_key": "$MEMU_API_KEY",
            "timeout": 30,
            "memorize_endpoint": "/memory/memorize",
            "min_conversation_length": 100,
            "dedup_window_minutes": 15,
            "cost_cap_per_hour": 1.0,
            "max_turns": 5,
            "memu_weight": 0.8,
            "append_to_memory_md": true
        }
    },

    "security": {
        "strict_mode": true,
        "sandbox_enabled": false,
        "rate_limit": {
            "global_rpm": 60,
            "per_user_rpm": 20,
            "per_tool": {
                "code_execution": 10,
                "web_search": 30
            }
        }
    },

    "output_guard": {
        "enabled": true,
        "log_redactions": true,
        "strict_mode": true,
        "skip_categories": []
    },

    "tools": {
        "web_search": {
            "searxng_url": "http://localhost:8080/search",
            "default_results": 5
        }
    },

    "docker": {
        "sandbox_image": "itak-sandbox:latest"
    },

    "heartbeat": {
        "enabled": true,
        "check_interval_seconds": 60,
        "check_memory": true,
        "check_disk": true,
        "check_models": true,
        "disk_warning_threshold_gb": 5
    },

    "adapters": {
        "discord": {
            "enabled": true,
            "prefix": "!",
            "allowed_channels": [],
            "allowed_roles": [],
            "typing_indicator": true,
            "max_message_length": 2000
        },
        "telegram": {
            "enabled": false,
            "allowed_chat_ids": [],
            "typing_indicator": true,
            "parse_mode": "Markdown"
        },
        "slack": {
            "enabled": false,
            "allowed_channels": []
        }
    },

    "webui": {
        "enabled": true,
        "host": "0.0.0.0",
        "port": 48920
    },

    "mcp_servers": {},
    "mcp_server": {
        "enabled": false,
        "host": "0.0.0.0",
        "port": 48921
    },

    "webhooks": {
        "secret": "$WEBHOOK_SECRET",
        "allowed_sources": ["n8n", "zapier"],
        "auto_respond": true
    },

    "users": {
        "registry_path": "data/users.json"
    },

    "logging": {
        "level": "INFO",
        "file": "data/itak.log",
        "max_size_mb": 50,
        "backup_count": 3,
        "mask_secrets": true
    }
}
```

---

## Section-by-Section Explanation

### `agent`
Core agent behavior. `max_iterations` prevents infinite loops. `checkpoint_interval_steps` controls how often state is saved for crash recovery.

### `models`
Four model slots:
- **chat** - Main reasoning (use the smartest model you have)
- **utility** - Cheap tasks like summarization (use a fast/cheap model)
- **browser** - Vision-capable for screenshots (needs multimodal)
- **embeddings** - Vector embeddings for memory search

The `provider` is always `litellm`, which supports 100+ APIs. Model names use the format `provider/model-name`.

### `memory`
Layer-by-layer configuration. Missing stores are silently skipped:
- **sqlite** always works (local file)
- **neo4j** requires a running Neo4j instance
- **weaviate** requires a Weaviate cluster
- **memu** (optional) extraction-only enrichment pipeline:
  - `enabled: false` - Disabled by default (sovereignty-first)
  - `mode: "self-hosted"` - Use local memu-server (or "cloud" for API)
  - `base_url: "http://localhost:8080"` - MemU server endpoint
  - `api_key` - Only needed for cloud mode
  - `timeout: 30` - Request timeout in seconds
  - `memorize_endpoint: "/memory/memorize"` - Custom endpoint path
  - `min_conversation_length: 100` - Skip conversations under N chars
  - `dedup_window_minutes: 15` - Skip similar conversations within N minutes
  - `cost_cap_per_hour: 1.0` - Max USD cost per hour
  - `max_turns: 5` - Number of conversation turns to send
  - `memu_weight: 0.8` - Weight for ranking memu-extracted items
  - `append_to_memory_md: true` - Append extracted facts to MEMORY.md

### `security`
- `sandbox_enabled: true` runs code in Docker containers
- `rate_limit` prevents abuse across users, tools, and global

### `output_guard`
- `skip_categories` lets you allow certain types through (e.g., `["email"]` to let emails pass)
- `log_redactions: true` records what gets redacted for audit

### `adapters`
Enable/disable each platform. `allowed_channels` restricts which channels the bot responds in (empty = all channels).

### `heartbeat`
Periodic system health checks. Monitors disk space, memory stores, and model availability.

---

## Environment Variables (.env)

```bash
# LLM API Keys
GOOGLE_API_KEY=your_google_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENROUTER_API_KEY=your_openrouter_key
GROQ_API_KEY=your_groq_key

# Platform Tokens
DISCORD_TOKEN=your_discord_token
TELEGRAM_TOKEN=your_telegram_token
SLACK_TOKEN=xoxb-your-slack-token
SLACK_APP_TOKEN=xapp-your-app-token

# Memory Stores
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your_neo4j_password
WEAVIATE_URL=http://localhost:8081
WEAVIATE_API_KEY=your_weaviate_key

# Webhooks
WEBHOOK_SECRET=your_webhook_secret

# SearXNG
SEARXNG_URL=http://localhost:8080
```
