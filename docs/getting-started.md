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

## Hosted Platforms (Pick Yours)

Open the dropdown for your platform and follow the exact UI fields.

<details>
<summary>Dokploy (Docker Compose app)</summary>

Steps:

1. Apps -> New App -> Docker Compose.
2. Connect GitHub repo and branch.
3. Compose file: [docker-compose.yml](docker-compose.yml); working directory: repo root.
4. Optional: manifest [dokploy.yml](dokploy.yml).
5. Environment: paste values from [.env.example](.env.example).
6. Expose `WEBUI_PORT` to your domain and deploy.

</details>

<details>
<summary>Coolify (Docker Compose resource)</summary>

Steps:

1. New Resource -> Docker Compose.
2. Connect repo and select branch.
3. Base directory: repo root; compose file: [docker-compose.yml](docker-compose.yml).
4. Environment: paste values from [.env.example](.env.example).
5. Add domain mapping to `WEBUI_PORT` and deploy.

</details>

<details>
<summary>Fly.io / Render / Railway (single-container mode)</summary>

These platforms do not run a full multi-service compose stack by default.
Deploy the app container and use managed services for Neo4j/Weaviate/SearXNG:

Steps:

1. Create a new app/service from the repo.
2. Build path: [install/docker/Dockerfile](install/docker/Dockerfile).
3. Environment: paste values from [.env.example](.env.example).
4. Set `NEO4J_URI`, `WEAVIATE_URL`, and `SEARXNG_URL` to managed endpoints.
5. Set service port to `48920` or set `ITAK_SET_webui__port=8080`.

</details>

<details>
<summary>CapRover (Docker Compose or Dockerfile)</summary>

Steps:

1. Apps -> Create New App.
2. Deploy method: Dockerfile or Docker Compose.
3. If Compose: use [docker-compose.yml](docker-compose.yml) at repo root.
4. Environment: paste values from [.env.example](.env.example).
5. Expose `WEBUI_PORT` in HTTP settings and deploy.

</details>

<details>
<summary>Portainer (Stack)</summary>

Steps:

1. Stacks -> Add Stack.
2. Paste or upload [docker-compose.yml](docker-compose.yml).
3. Environment: paste values from [.env.example](.env.example).
4. Deploy the stack and map `WEBUI_PORT` to your host.

</details>

<details>
<summary>Dokku (single-container mode)</summary>

Steps:

1. Create app in Dokku.
2. Enable Dockerfile deploy using [install/docker/Dockerfile](install/docker/Dockerfile).
3. Set env vars from [.env.example](.env.example).
4. Use managed services for Neo4j/Weaviate/SearXNG.
5. Set `ITAK_SET_webui__port` if you need a custom port.

</details>

<details>
<summary>Heroku (container)</summary>

Steps:

1. Create app -> Deploy -> Container Registry.
2. Build from [install/docker/Dockerfile](install/docker/Dockerfile).
3. Config Vars: paste values from [.env.example](.env.example).
4. Set `ITAK_SET_webui__port=$PORT`.
5. Deploy and open the app URL.

</details>

<details>
<summary>DigitalOcean App Platform (container)</summary>

Steps:

1. Create app -> Web Service from repo.
2. Build from [install/docker/Dockerfile](install/docker/Dockerfile).
3. HTTP port: `48920` (or set `ITAK_SET_webui__port=8080` and use `8080`).
4. Environment: paste values from [.env.example](.env.example).
5. Deploy and open the app URL.

</details>

<details>
<summary>AWS ECS/Fargate (container)</summary>

Steps:

1. Build/push image to ECR.
2. Create task definition (Fargate) with port `48920`.
3. Add env vars from [.env.example](.env.example).
4. Create service with load balancer target `48920`.
5. Deploy and open the service URL.

</details>

<details>
<summary>GCP Cloud Run (container)</summary>

Steps:

1. Build/push image to Artifact Registry.
2. Create Cloud Run service with port `48920`.
3. Add env vars from [.env.example](.env.example).
4. Allow unauthenticated if public.
5. Deploy and open the service URL.

</details>

<details>
<summary>Azure Container Apps (container)</summary>

Steps:

1. Create Container App from your registry image.
2. Enable External ingress; target port `48920`.
3. Add env vars from [.env.example](.env.example).
4. Deploy and open the app URL.

</details>

<details>
<summary>Vercel / Netlify (not supported)</summary>

Steps:

1. Not supported for full stack.
2. Use Dokploy/Coolify or a container platform instead.

</details>

### Port + Adapter Notes

- Random 5-digit ports: keep `ITAK_RANDOM_PORTS=true` in your env and run
  `python install.py --skip-deps --minimal` once before deploying, or set
  `WEBUI_PORT`, `NEO4J_HTTP_PORT`, `NEO4J_BOLT_PORT`, `WEAVIATE_PORT`, and
  `SEARXNG_PORT` directly in the platform UI.
- Choose adapter: set `ITAK_ARGS` (example: `--adapter discord --webui`).

### Security Note

We do not run Docker-in-Docker or mount the host Docker socket inside the app
container. Use Docker Compose for the full stack to avoid elevated host access.

### Common Pitfalls

- Wrong working directory (must be repo root)
- `.env` not created from [.env.example](.env.example)
- `WEBUI_PORT` not exposed to your domain

### Quick Validate

```bash
docker compose ps
```

Open: `http://<host>:<WEBUI_PORT>`

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
