# Getting Started

> From zero to running agent in 5 minutes.

## Prerequisites

| Requirement | Minimum | Check |
|-------------|---------|-------|
| Python | 3.11+ | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any | `git --version` |
| Docker | Optional (for sandbox mode) | `docker --version` |

## Quick Setup

### 1. Clone the repo
```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

iTaK auto-checks prerequisites at startup. If anything is missing, it tells you what to install.

### 3. Configure

Copy the example config and add your API keys:

```bash
cp config.json.example config.json
cp .env.example .env
```

Edit `.env` with your keys:
```bash
# Required: at least one LLM provider
GOOGLE_API_KEY=your_key_here
# OR
OPENAI_API_KEY=your_key_here

# Optional: platform adapters
DISCORD_TOKEN=your_token_here
TELEGRAM_TOKEN=your_token_here
```

Edit `config.json` - the default config works out of the box with Google Gemini. See [config.md](config.md) for every option.

### 4. Run

```bash
# CLI mode (default - talk to the agent in your terminal)
python main.py

# With the web dashboard
python main.py --webui

# Discord bot mode
python main.py --adapter discord --webui

# All options
python main.py --help
```

### 5. First conversation

```
[iTaK] Ready. Type your message:
> Hello! What can you do?
[iTaK] I can execute code, search the web, manage files, browse websites,
       delegate tasks, and remember everything across conversations. What
       would you like to work on?
>
```

---

## What You Need by Feature

Not everything requires full setup. Here's what each feature needs:

| Feature | Requirements |
|---------|-------------|
| **Basic chat + code execution** | Python + 1 LLM API key |
| **Web search** | SearXNG instance (local or remote) |
| **Web browsing** | Playwright (`playwright install chromium`) |
| **Discord bot** | Discord bot token |
| **Telegram bot** | Telegram bot token |
| **Slack bot** | Slack app + bot token |
| **Knowledge graph** | Neo4j instance |
| **Semantic search** | Weaviate instance |
| **Sandboxed execution** | Docker |
| **WebUI dashboard** | Nothing extra (built-in) |

### Minimal Setup (just chat + code)
```bash
# .env
GOOGLE_API_KEY=your_key
```
That's it. Memory uses local SQLite, no external services needed.

### Full Setup (everything)
```bash
# .env
GOOGLE_API_KEY=your_key
OPENAI_API_KEY=your_key        # For embeddings
DISCORD_TOKEN=your_token
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your_password
```

---

## Docker Deployment

Run the entire stack with Docker Compose:

```bash
docker compose up -d
```

This starts:
- iTaK agent
- WebUI dashboard on port 48920
- Neo4j (if configured)
- SearXNG (if configured)

---

## Verification

After setup, verify everything is working:

### Run the diagnostic tool
```bash
python main.py --doctor
```

This checks:
- ✅ Python version (3.11+)
- ✅ All required packages
- ✅ Configuration files
- ✅ API keys
- ✅ Security systems
- ✅ Tool availability

Expected output (example):
```
========================================================
   iTaK Doctor - Full System Diagnostic
========================================================

-- Preflight (Python, packages, config) --
  [OK]  Python 3.11+
  [OK]  Package: litellm
  [OK]  Package: pydantic
  ...
  [OK]  config.json found
  [OK]  .env file found

-- Security Hardening --
  [OK]  SSRF Guard functional
  [OK]  Path Guard functional
  ...

========================================================
  XX passed, Y failed (optional services)
========================================================
```

Most failures are optional services (Neo4j, Weaviate, SearXNG) - these don't prevent basic operation.

### Run the test suite
```bash
python -m pytest tests/ -q
```

All tests should pass (example):
```
XX passed in Y.YYs
```

### Test basic functionality
```bash
# Start in CLI mode
python main.py

# In another terminal, check if the agent responds
# Type a simple question like "What's 2+2?"
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `config.json not found` | Copy `config.json.example` to `config.json` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `GOOGLE_API_KEY not set` | Add it to `.env` or set as environment variable |
| `Playwright not installed` | Run `playwright install chromium` |
| `Neo4j connection refused` | Check NEO4J_URI in `.env`, ensure Neo4j is running |
| Port already in use | Change the port in `config.json` under `webui.port` |

---

## Next Steps

- [Architecture Guide](architecture.md) - understand how the system works
- [Models Guide](models.md) - add/swap LLM providers
- [Configuration Reference](config.md) - every config option explained
- [Tools Reference](tools.md) - what the agent can do
