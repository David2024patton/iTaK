# Models & LLM Providers Guide

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


> How to add, swap, and configure LLM providers.

## Overview

iTaK uses **LiteLLM** as a universal adapter - one API that talks to 100+ LLM providers. Changing models is just a config change, no code needed.

## The 4 Model Slots

| Slot | Purpose | Best Choice | Budget Choice |
|------|---------|-------------|---------------|
| **chat** | Main reasoning, tool use | Gemini 2.5 Pro, Claude 4 Sonnet, GPT-4.1 | Gemini 2.0 Flash |
| **utility** | Summarization, extraction, classification | Gemini 2.0 Flash, GPT-4.1-mini | Gemini 2.0 Flash |
| **browser** | Screenshot analysis (needs vision) | Gemini 2.5 Pro, Claude 4 Sonnet | Gemini 2.0 Flash |
| **embeddings** | Vector search for memory | text-embedding-3-small | nomic-embed-text (local) |

---

## Provider Setup

### Google Gemini (Recommended)
```bash
# .env
GOOGLE_API_KEY=your_key_here
```
```json
{
    "models": {
        "chat": {"provider": "litellm", "model": "gemini/gemini-2.5-pro-preview-05-06"},
        "utility": {"provider": "litellm", "model": "gemini/gemini-2.0-flash"},
        "browser": {"provider": "litellm", "model": "gemini/gemini-2.5-pro-preview-05-06"},
        "embeddings": {"provider": "litellm", "model": "gemini/text-embedding-004"}
    }
}
```

### OpenAI
```bash
# .env
OPENAI_API_KEY=sk-your_key_here
```
```json
{
    "models": {
        "chat": {"provider": "litellm", "model": "gpt-4.1"},
        "utility": {"provider": "litellm", "model": "gpt-4.1-mini"},
        "browser": {"provider": "litellm", "model": "gpt-4.1"},
        "embeddings": {"provider": "litellm", "model": "text-embedding-3-small"}
    }
}
```

### Anthropic Claude
```bash
# .env
ANTHROPIC_API_KEY=sk-ant-your_key_here
```
```json
{
    "models": {
        "chat": {"provider": "litellm", "model": "anthropic/claude-sonnet-4-20250514"},
        "utility": {"provider": "litellm", "model": "anthropic/claude-haiku-3-5"},
        "browser": {"provider": "litellm", "model": "anthropic/claude-sonnet-4-20250514"}
    }
}
```

### Local Ollama (Free, Self-Hosted)
```bash
# No API key needed - install Ollama and pull models
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```
```json
{
    "models": {
        "chat": {"provider": "litellm", "model": "ollama/llama3.1:8b", "api_base": "http://localhost:11434"},
        "utility": {"provider": "litellm", "model": "ollama/llama3.1:8b", "api_base": "http://localhost:11434"},
        "embeddings": {"provider": "litellm", "model": "ollama/nomic-embed-text", "api_base": "http://localhost:11434"}
    }
}
```

### OpenRouter (100+ Models, One Key)
```bash
# .env
OPENROUTER_API_KEY=sk-or-your_key_here
```
```json
{
    "models": {
        "chat": {"provider": "litellm", "model": "openrouter/google/gemini-2.5-pro"},
        "utility": {"provider": "litellm", "model": "openrouter/google/gemini-2.0-flash-001"}
    }
}
```

### Groq (Fast Inference)
```bash
# .env
GROQ_API_KEY=gsk_your_key_here
```
```json
{
    "models": {
        "chat": {"provider": "litellm", "model": "groq/llama-3.3-70b-versatile"},
        "utility": {"provider": "litellm", "model": "groq/llama-3.1-8b-instant"}
    }
}
```

---

## Mix and Match

You can use different providers for different slots:

```json
{
    "models": {
        "chat": {"provider": "litellm", "model": "anthropic/claude-sonnet-4-20250514"},
        "utility": {"provider": "litellm", "model": "groq/llama-3.1-8b-instant"},
        "browser": {"provider": "litellm", "model": "gemini/gemini-2.5-pro-preview-05-06"},
        "embeddings": {"provider": "litellm", "model": "text-embedding-3-small"}
    }
}
```

This uses Claude for thinking, Groq for cheap tasks, Gemini for vision, and OpenAI for embeddings.

---

## Model Parameters

```json
{
    "models": {
        "chat": {
            "provider": "litellm",
            "model": "gemini/gemini-2.5-pro-preview-05-06",
            "temperature": 0.7,      // 0.0 = deterministic, 1.0 = creative
            "max_tokens": 8192,      // Max response length
            "context_window": 1000000, // How much history to send
            "api_key": "$GOOGLE_API_KEY",  // Resolved from .env
            "api_base": ""           // For custom endpoints (Ollama, vLLM)
        }
    }
}
```

### Parameter Guide
| Parameter | Low Value | High Value | Recommendation |
|-----------|-----------|------------|----------------|
| `temperature` | 0.0 (exact) | 1.0 (creative) | 0.7 for chat, 0.3 for utility |
| `max_tokens` | 1024 | 32768 | 8192 for most tasks |
| `context_window` | 4096 | 1000000+ | Match your model's limit |

---

## Cost Optimization Tips

1. **Use the cheapest model for utility** - Summarization and extraction don't need GPT-4
2. **Use Ollama for embeddings** - Free local embeddings with nomic-embed-text
3. **Use Groq for utility** - Fast and cheap
4. **Monitor via WebUI** - Dashboard shows model usage and token counts
5. **Set budget caps** - Use `agent.max_iterations` to prevent runaway costs

---

## Supported Providers (via LiteLLM)

| Provider | Model Name Prefix | Notes |
|----------|-------------------|-------|
| Google Gemini | `gemini/` | Best value, 1M context |
| OpenAI | (none) | GPT-4.1, o3-mini |
| Anthropic | `anthropic/` | Claude 4 Sonnet/Opus |
| Ollama | `ollama/` | Free, local |
| OpenRouter | `openrouter/` | 100+ models |
| Groq | `groq/` | Fast inference |
| Mistral | `mistral/` | Mistral Large/Small |
| Cohere | `cohere_chat/` | Command R+ |
| DeepSeek | `deepseek/` | DeepSeek V3 |
| Together AI | `together_ai/` | Open models |

Full list: [LiteLLM Providers](https://docs.litellm.ai/docs/providers)
