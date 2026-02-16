# Getting Started

## At a Glance
- Audience: New users, operators, and developers setting up iTaK environments.
- Scope: Guide environment setup from prerequisites to first successful launch with validation checkpoints.
- Last reviewed: 2026-02-16.

## Quick Start
- Verify prerequisites and environment variables before running setup scripts.
- Execute installation steps in order from [root/INSTALL.md](root/INSTALL.md).
- Confirm service readiness with [root/QUICK_START.md](root/QUICK_START.md).

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Use commands as ordered steps; verify prerequisites before launching services.
- Re-validate service ports and env/config files after any setup change.


> From zero to running agent in 5 minutes.

## Choose Your Path

- Beginner walkthrough: [NOOBS_FIRST_DAY.md](NOOBS_FIRST_DAY.md)
- Wiki navigation hub: [WIKI.md](WIKI.md)
- AI-friendly structured context: [AI_CONTEXT.md](AI_CONTEXT.md)

## Prerequisites

| Requirement | Minimum | Check |
|-------------|---------|-------|
| Python | 3.11+ | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any | `git --version` |
| Docker | Optional (for sandbox mode) | `docker --version` |

## Quick Setup

### Option A: Universal Installer (Recommended)

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/David2024patton/iTaK.git
cd iTaK

# Run the universal installer
python install.py

# The installer will:
# - Detect your OS (Linux, macOS, Windows, WSL)
# - Check prerequisites (Python, pip, Git, Docker)
# - Install all dependencies
# - Set up configuration files (.env, config.json)
# - Create necessary data directories
```

**Installation options:**

```bash
python install.py              # Full installation (recommended)
python install.py --minimal    # Skip Playwright browsers and Docker components
python install.py --skip-deps  # Only setup config files (skip dependency install)
python install.py --help       # Show all options
```

After installation, edit `.env` with your API keys and run `python -m app.main`.

### Option B: Manual Setup

### 1. Clone the repo
```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
```

### 2. Install dependencies
```bash
pip install -r install/requirements/requirements.txt
```

iTaK auto-checks prerequisites at startup. If anything is missing, it tells you what to install.

### 3. Configure

**Option A: Interactive Setup (Recommended)**

Run the interactive setup script to configure iTaK, including Neo4j memory:

```bash
python installers/setup.py
```

This will guide you through:
- Creating config.json and .env files
- Configuring Neo4j (use your own or install via Docker)
- Configuring Weaviate (optional)

**Option B: Manual Setup**

Copy the example config and add your API keys:

```bash
cp install/config/config.json.example config.json
cp install/config/.env.example .env
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

# Optional: Neo4j knowledge graph
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your_password_here
```

Edit `config.json` - the default config works out of the box with Google Gemini. See [config.md](config.md) for every option.

### 4. Run

```bash
# CLI mode (default - talk to the agent in your terminal)
python -m app.main

# With the web dashboard
python -m app.main --webui

# Discord bot mode
python -m app.main --adapter discord --webui

# All options
python -m app.main --help
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
python -m app.main --doctor
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
  N passed, M failed (optional services)
========================================================
```

Most failures are optional services (Neo4j, Weaviate, SearXNG) - these don't prevent basic operation.

### Run the test suite
```bash
python -m pytest tests/ -q
```

All tests should pass (example):
```
N passed in X.XXs
```

### Test basic functionality
```bash
# Start in CLI mode
python -m app.main

# The agent will display a prompt:
# [iTaK] Ready. Type your message:
# > 

# Type a simple question at the prompt and press Enter:
# > What's 2+2?
```

The agent should respond with a calculation or explanation.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `config.json not found` | Copy `install/config/config.json.example` to `config.json` |
| `ModuleNotFoundError` | Run `pip install -r install/requirements/requirements.txt` |
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
