# iTaK Installation Guide - New User Walkthrough

## At a Glance

- Audience: New users, operators, and developers setting up iTaK environments.
- Scope: Guide environment setup from prerequisites to first successful launch with validation checkpoints.
- Last reviewed: 2026-02-16.

## Quick Start

- Verify prerequisites and environment variables before running setup scripts.
- Execute installation steps in order from [INSTALL.md](INSTALL.md).
- Confirm service readiness with [QUICK_START.md](QUICK_START.md).

## Deep Dive

The detailed content for this topic starts below.

## AI Notes

- Use commands as ordered steps; verify prerequisites before launching services.
- Re-validate service ports and env/config files after any setup change.

> **Quick Summary:** Get iTaK running in minutes. Choose Docker (fastest) or Python (most control). This guide walks you through both methods and explains what iTaK does once running.

---

## 📋 Table of Contents

1. [What is iTaK?](#what-is-itak)
2. [Installation Methods](#installation-methods)
   - [Docker Quick Start (Recommended)](#docker-quick-start-recommended)
   - [Python Installation (Full Control)](#python-installation-full-control)
3. [What iTaK Does Once Installed](#what-itak-does-once-installed)
4. [Common Use Cases](#common-use-cases)
5. [Troubleshooting](#troubleshooting)
6. [Next Steps](#next-steps)

---

## 🤔 What is iTaK?

**iTaK (Intelligent Task Automation Kernel)** is an AI-powered assistant that can:

- 💬 **Chat with you** via terminal, Discord, Telegram, Slack, or web dashboard
- 🔧 **Execute code** to solve problems, automate tasks, and build projects
- 🧠 **Remember everything** using a 4-tier memory system (Recall/Archival/Episodic/Knowledge)
- 🩹 **Fix its own errors** automatically using self-healing AI
- 🌐 **Search the web** and interact with websites
- 📊 **Manage tasks** on a Kanban board (Mission Control)
- 🤖 **Control multiple sub-agents** working in parallel (swarms)
- 🔌 **Integrate with tools** via webhooks and MCP protocol
- 🔒 **Production-ready** with 85% test coverage and compliance certifications

Think of it as **ChatGPT + GitHub Copilot + n8n automation** - all in one self-hosted package.

**Coming from Agent-Zero?** See our [comparison guide](iTAK_VS_AGENT_ZERO.md) to understand the differences.

---

## 🐳 Installation Methods

Choose your installation method:

| Method | Time | Best For | Pros | Cons |
|--------|------|----------|------|------|
| **Docker** | 5 min | Quick start, production | Isolated, reproducible, full stack | Requires Docker |
| **Python** | 10 min | Development, customization | Full control, easy debugging | Manual setup |

---

## 🚢 Docker Quick Start (Recommended)

**Perfect for:** Quick testing, production deployments, users familiar with Docker

### Prerequisites

- Docker Desktop installed ([Windows](https://docs.docker.com/desktop/install/windows-install/) \| [macOS](https://docs.docker.com/desktop/install/mac-install/) \| [Linux](https://docs.docker.com/desktop/install/linux-install/))
- At least one AI API key (see [API Keys](#api-keys-setup) below)

> **Note:** Unlike Agent-Zero (which lets you configure API keys AFTER running via Web UI), iTaK requires API keys configured in `.env` BEFORE first run. See [comparison below](#api-key-configuration-agent-zero-vs-itak).

### Installation (2 Commands)

```bash
# 1. Clone the repository
git clone https://github.com/David2024patton/iTaK.git
cd iTaK

# 2. Start with Docker Compose (includes Neo4j, Weaviate, SearXNG)
cp install/config/.env.example .env
# Edit .env and add your API keys (see below)
docker compose --project-directory . -f install/docker/docker-compose.yml up -d
```

### What This Starts

The `install/docker/docker-compose.yml` starts a full stack:

- **iTaK Agent** - Main AI agent (port 8000 for WebUI)
- **Neo4j** - Knowledge graph database (port 47474)
- **Weaviate** - Vector database (port 48080)
- **SearXNG** - Private web search (port 48888)

### Access iTaK

```bash
# Web Dashboard
http://localhost:8000

# Check logs
docker compose --project-directory . -f install/docker/docker-compose.yml logs -f itak

# Stop all services
docker compose --project-directory . -f install/docker/docker-compose.yml down
```

### Docker-Only Mode (Minimal)

Don't need the full stack? Run just iTaK:

```bash
# Build and run iTaK only
docker build -f install/docker/Dockerfile -t itak .
docker run -p 8000:8000 --env-file .env itak --webui
```

---

## 🐍 Python Installation (Full Control)

**Perfect for:** Developers, customization, debugging, contributing

### Step 1: Prerequisites

Make sure you have:

```bash
# Python 3.11 or higher
python --version
# Should show: Python 3.11.x or higher

# pip (Python package manager)
pip --version

# Git (to clone the repository)
git --version
```

**Don't have Python 3.11+?** Download from [python.org](https://www.python.org/downloads/)

---

### Step 2: Clone the Repository

```bash
# Clone iTaK
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
```

---

### Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r install/requirements/requirements.txt

# This takes 2-3 minutes and installs:
# - LiteLLM (AI model router)
# - FastAPI (web dashboard)
# - Discord/Telegram/Slack libraries
# - Database drivers
# - Security tools
# - And ~30 more packages
```

**Tip:** Use a virtual environment to keep things clean:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r install/requirements/requirements.txt
```

---

### Step 4: Configure iTaK

### Step 1: Prerequisites

Make sure you have:

```bash
# Python 3.11 or higher
python --version
# Should show: Python 3.11.x or higher

# pip (Python package manager)
pip --version

# Git (to clone the repository)
git --version
```

**Don't have Python 3.11+?** Download from [python.org](https://www.python.org/downloads/)

---

### Step 2: Clone the Repository

```bash
# Clone iTaK
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
```

---

### Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r install/requirements/requirements.txt

# This takes 2-3 minutes and installs:
# - LiteLLM (AI model router)
# - FastAPI (web dashboard)
# - Discord/Telegram/Slack libraries
# - Database drivers
# - Security tools
# - And ~30 more packages
```

**Tip:** Use a virtual environment to keep things clean:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r install/requirements/requirements.txt
```

---

### Step 4: Configure iTaK

```bash
# Copy example configuration files
cp install/config/config.json.example config.json
cp install/config/.env.example .env

# Edit .env and add AT LEAST ONE API key
nano .env  # or use your favorite editor
```

**Minimum Configuration (.env file):**

```bash
# Add ONE of these (iTaK supports multiple LLM providers):

# Option 1: Google Gemini (recommended - has free tier)
GEMINI_API_KEY=your_gemini_key_here

# Option 2: OpenAI
OPENAI_API_KEY=your_openai_key_here

# Option 3: Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_key_here

# Option 4: Local Ollama (free, runs on your machine)
OLLAMA_BASE_URL=http://localhost:11434
```

**Where to get API keys:**

- **Gemini**: [aistudio.google.com](https://aistudio.google.com/) (Free tier available)
- **OpenAI**: [platform.openai.com](https://platform.openai.com/)
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com/)
- **Ollama**: [ollama.com](https://ollama.com/) (Run LLMs locally)

---

### API Keys Setup

<details>
<summary><b>📘 Click here for detailed API key instructions</b></summary>

#### Google Gemini (Recommended for Beginners)

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with Google account
3. Click "Get API Key" → "Create API key"
4. Copy the key and add to `.env`:

   ```
   GEMINI_API_KEY=AIza...
   ```

#### OpenAI

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create account and add payment method
3. Navigate to API Keys section
4. Create new key and copy to `.env`:

   ```
   OPENAI_API_KEY=sk-...
   ```

#### Anthropic Claude

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up for account
3. Add payment method
4. Generate API key in settings
5. Add to `.env`:

   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

#### Ollama (Local, Free)

1. Install Ollama from [ollama.com](https://ollama.com/)
2. Pull a model: `ollama pull llama2`
3. Add to `.env`:

   ```
   OLLAMA_BASE_URL=http://localhost:11434
   ```

4. Set in `config.json`:

   ```json
   {
     "agent": {
       "default_model": "ollama/llama2"
     }
   }
   ```

</details>

---

## ⚠️ Security Warning

> **IMPORTANT:** iTaK can execute code on your computer by design. Always:
>
> - ✅ Run in an isolated environment (Docker recommended for production)
> - ✅ Use a separate, limited-privilege user account
> - ✅ Never give iTaK admin/root access in production
> - ✅ Review code before allowing execution in sensitive environments
> - ✅ Keep API keys secure (never commit `.env` to git)
> - ✅ Enable output guards in production (redacts PII, secrets)
>
> **For production deployments**, see [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for security hardening.

---

### API Key Configuration: Agent-Zero vs iTaK

**Question:** "Does Agent-Zero make you put in an API key before install?"

**Answer:** No! This is a key difference in user experience:

| Step | Agent-Zero | iTaK |
|------|------------|------|
| **1. Install** | `docker pull` + `docker run` | `git clone` + `pip install` OR `docker compose --project-directory . -f install/docker/docker-compose.yml up -d` |
| **2. First Run** | ✅ Runs immediately (no API key needed) | ⚠️ Requires API key in `.env` first |
| **3. Configure API** | Via Web UI Settings panel AFTER running | Via `.env` file BEFORE running |
| **4. Restart** | Yes (to apply settings) | No (already configured) |

**Agent-Zero's Approach (configure after):**

```bash
docker run -p 50080:80 agent0ai/agent-zero
# Visit http://localhost:50080
# Click Settings → Add API keys → Save → Restart
```

**iTaK's Approach (configure before):**

```bash
cp install/config/.env.example .env
nano .env  # Add API keys
python -m app.main --webui  # Runs with keys already configured
```

**Which is better?**

- **Agent-Zero's approach:** ✅ Faster to see the UI, better for first-time users
- **iTaK's approach:** ✅ Clearer for production, prevents running without proper config

**Can iTaK match Agent-Zero's UX?**  
Yes! iTaK can run without API keys for testing. If you skip the API key configuration, iTaK will:

- ✅ Start up successfully
- ✅ Show the Web UI
- ⚠️ Display friendly error messages suggesting you configure API keys
- 📝 Guide you to add keys and restart

For the smoothest experience, we recommend configuring API keys before first run (iTaK's current default).

---

**Optional Settings (you can skip these for now):**

- `DISCORD_TOKEN` - To use iTaK as a Discord bot
- `TELEGRAM_TOKEN` - To use iTaK as a Telegram bot
- `SLACK_TOKEN` - To use iTaK as a Slack bot
- `NEO4J_URI` - For knowledge graph memory (advanced)

---

### Step 5: Run iTaK

```bash
# Option 1: Terminal Chat (simplest)
python -m app.main

# Option 2: With Web Dashboard
python -m app.main --webui

# Option 3: Run System Diagnostics (recommended first time)
python -m app.main --doctor
```

**First Run - What to Expect:**

```
🧠 iTaK - Intelligent Task Automation Kernel v4
──────────────────────────────────────────────────

🔍 Running preflight checks...
  ✓ Python version: 3.11.5
  ✓ Configuration loaded
  ✓ Memory database initialized
  ✓ LLM connection verified (Gemini)
  ✓ Security modules loaded
  ✓ Tools loaded: 15 tools
  ⚠ Neo4j not connected (optional)
  ⚠ Discord adapter disabled (no token)

🚀 iTaK is ready!

> 
```

You can now start chatting! Try asking:

- "Hello, what can you do?"
- "Search the web for latest Python news"
- "Create a Python script that generates fibonacci numbers"
- "Remember that my favorite color is blue"

---

## 🎯 What iTaK Does Once Installed

Once running, iTaK becomes your AI-powered assistant with these capabilities:

### 1. 💬 **Natural Conversation**

```
You: Write me a Python script to sort a list
iTaK: I'll create that for you. Let me write the code...
     [executes code tool]
     Done! I've created sort_list.py with quicksort implementation.
     Would you like me to test it?
```

### 2. 🔧 **Code Execution**

iTaK can:

- Write and run Python/Bash scripts
- Install packages (`pip install requests`)
- Read and edit files
- Run tests and fix bugs
- Deploy code

**Example:**

```
You: Install Flask and create a hello world web app
iTaK: [Executes: pip install flask]
     [Creates: app.py with Flask code]
     [Runs: python app.py]
     Web server started on http://localhost:5000
```

### 3. 🧠 **4-Tier Memory System**

iTaK remembers everything across sessions:

**Tier 1 - Core Context**: Your name, preferences, active projects  
**Tier 2 - Recall**: Recent conversation (last 20 messages)  
**Tier 3 - Archival**: Searchable long-term storage (all past conversations)  
**Tier 4 - Knowledge Graph**: Entity relationships (if Neo4j configured)

**Example:**

```
Day 1:
You: Remember that I'm working on a FastAPI project called "TaskMaster"
iTaK: Saved to memory. I'll remember your TaskMaster project.

Day 3:
You: What was I working on?
iTaK: You're working on a FastAPI project called "TaskMaster"
```

### 4. 🩹 **Self-Healing**

When iTaK encounters errors, it automatically:

1. Classifies the error type
2. Checks memory for past fixes
3. Reasons about the solution
4. Researches if needed
5. Learns from the fix

**Example:**

```
iTaK: [Runs code with missing import]
     ❌ Error: ModuleNotFoundError: No module named 'requests'
     
     [Self-healing activates]
     🔧 Installing missing package...
     [Executes: pip install requests]
     ✓ Fixed! Retrying...
     [Code runs successfully]
```

### 5. 🌐 **Web Search & Interaction**

```
You: What's the current Python version?
iTaK: [Searches web]
     The latest Python version is 3.12.1, released on December 8, 2024.
     
You: Go to python.org and download it
iTaK: [Opens browser automation]
     [Navigates to python.org]
     Here's the download link: [URL]
```

### 6. 📊 **Mission Control (Task Board)**

iTaK automatically tracks tasks:

```
You: I need to build a REST API and write tests
iTaK: [Creates task: "Build REST API" → inbox]
     [Creates task: "Write tests" → inbox]
     I've added these to the task board. Starting with the API...
     [Moves "Build REST API" → in_progress]
```

View tasks in the web dashboard (`python -m app.main --webui`)

### 7. 🐝 **Multi-Agent Swarms**

Delegate to specialist sub-agents:

```
You: Research Python web frameworks, compare them, and write a report
iTaK: [Spawns 3 agents in parallel]
     - Research Agent: Gathering framework data
     - Analysis Agent: Comparing features
     - Writer Agent: Drafting report
     
     [Merges results]
     Here's your comprehensive comparison report...
```

### 8. 🔌 **Multi-Channel Access**

Run iTaK on multiple channels simultaneously:

**Terminal:**

```bash
python -m app.main
```

**Web Dashboard:**

```bash
python -m app.main --webui
# Open http://localhost:8080
```

**Discord Bot:**

```bash
# Add DISCORD_TOKEN to .env
python -m app.main --adapter discord
```

**Telegram Bot:**

```bash
# Add TELEGRAM_TOKEN to .env
python -m app.main --adapter telegram
```

**All at once:**

```bash
python -m app.main --adapter discord --webui
# Discord bot + web dashboard running together
```

### 9. 🔒 **Security Features**

- **Secret detection**: Automatically masks API keys in logs
- **Output guard**: Redacts PII (emails, SSNs, credit cards)
- **Rate limiting**: Prevents abuse
- **Multi-user RBAC**: Owner → Sudo → User permissions
- **Code scanning**: Checks generated code for vulnerabilities

### 10. 🔗 **Integration Capabilities**

**Webhooks (n8n/Zapier):**

```json
POST /webhooks/inbound
{
  "task": "Generate daily report",
  "callback_url": "https://your-webhook.com/result"
}
```

**MCP (Model Context Protocol):**

- iTaK can connect to MCP servers (GitHub, databases)
- iTaK can BE an MCP server for other tools

---

## 📚 Common Use Cases

### Use Case 1: Code Development Assistant

```
You: Create a FastAPI CRUD app for managing books
iTaK: I'll build that for you:
     1. Installing FastAPI and dependencies...
     2. Creating project structure...
     3. Writing models.py, routes.py, main.py...
     4. Creating database schema...
     5. Writing tests...
     Done! Run with: python -m app.main
     
You: The POST endpoint isn't working
iTaK: [Debugs code]
     Found the issue - missing request body validation.
     [Fixes code]
     Fixed! Try again.
```

### Use Case 2: Research & Analysis

```
You: Research the top 5 JavaScript frameworks in 2024 and create a comparison table
iTaK: [Web search: "top javascript frameworks 2024"]
     [Gathers data on React, Vue, Angular, Svelte, Next.js]
     [Creates markdown table with features, pros, cons]
     Here's your comparison table...
```

### Use Case 3: DevOps Automation

```
You: Check server disk space and send alert if > 80%
iTaK: [Executes: df -h]
     Current usage: 45%
     [Saves monitoring script]
     I've created monitor_disk.sh and scheduled it with cron.
     You'll get alerts if disk exceeds 80%.
```

### Use Case 4: Documentation Generator

```
You: Generate API documentation for all Python files in /src
iTaK: [Scans /src directory]
     [Analyzes 15 Python files]
     [Extracts docstrings and function signatures]
     [Generates markdown documentation]
     Created API_DOCS.md with documentation for all modules.
```

### Use Case 5: Multi-Agent Project

```
You: Build a blog platform - one agent for backend, one for frontend, one for database
iTaK: [Spawns parallel swarm]
     Backend Agent: Creating Flask API...
     Frontend Agent: Building React app...
     Database Agent: Setting up PostgreSQL schema...
     
     [30 seconds later]
     All agents complete! Integrating components...
     Blog platform ready at http://localhost:3000
```

### Use Case 6: Discord/Telegram Bot

```bash
# In Discord:
@iTaK Write me a Python function to calculate prime numbers
[iTaK responds with code in Discord]

# In Telegram:
/ask Deploy my project to AWS
[iTaK executes deployment steps and reports progress]
```

### Use Case 7: Scheduled Tasks

```
You: Every Monday at 9am, search for "Python news" and save a summary
iTaK: [Creates scheduled task]
     [Sets up weekly webhook]
     Done! I'll research Python news every Monday and save summaries to /reports
```

---

## 🔧 Troubleshooting

### Problem: "config.json not found"

```bash
# Solution:
cp install/config/config.json.example config.json
```

### Problem: "No LLM API key configured"

```bash
# Solution: Edit .env and add at least ONE key:
GEMINI_API_KEY=your_key_here
# OR
OPENAI_API_KEY=your_key_here
```

### Problem: "ModuleNotFoundError: No module named 'X'"

```bash
# Solution: Reinstall dependencies
pip install -r install/requirements/requirements.txt
```

### Problem: "Permission denied" when running code

```bash
# Solution: Enable code execution in config.json
{
  "security": {
    "sandbox_enabled": true,  # Allows code execution
    ...
  }
}
```

### Problem: Tests fail with import errors

```bash
# Solution: Set PYTHONPATH
PYTHONPATH=$(pwd) python3 -m pytest tests/
```

### Problem: iTaK responses are slow

```bash
# Solution 1: Use faster models
# Edit config.json:
{
  "models": {
    "chat": {
      "model": "gemini/gemini-2.0-flash"  # Faster than gemini-pro
    }
  }
}

# Solution 2: Use local Ollama
ollama run llama2
# Then set OLLAMA_BASE_URL in .env
```

### Problem: "WebUI won't start"

```bash
# Check if port 8080 is in use:
lsof -i :8080

# Change port in config.json:
{
  "webui": {
    "port": 8081  # Use different port
  }
}
```

### Problem: Memory/database errors

```bash
# Reset databases:
rm -rf data/db/*.db
# iTaK will recreate them on next run
```

---

## 🎓 Next Steps

### 1. **Explore the Web Dashboard**

```bash
python -m app.main --webui
# Open http://localhost:8080
```

**Dashboard Features:**

- 📊 Monitor tab: Real-time logs and stats
- 🎯 Mission Control: Task board (Kanban)
- 🔧 Tools: See all loaded tools
- 📚 Memory: Browse saved memories
- 👥 Users: Manage RBAC permissions

### 2. **Run System Diagnostics**

```bash
python -m app.main --doctor
```

This checks:

- Python version
- Dependencies
- Configuration
- Security modules
- Database connections
- API key validity

### 3. **Explore Advanced Features**

**Neo4j Knowledge Graph:**

```bash
# Install Neo4j (Docker):
docker run -p 7687:7687 -p 7474:7474 neo4j:latest

# Add to .env:
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your_password

# iTaK will now build knowledge graphs of entities and relationships
```

**Discord Bot:**

```bash
# 1. Create Discord bot at: https://discord.com/developers/applications
# 2. Copy bot token
# 3. Add to .env:
DISCORD_TOKEN=your_token_here

# 4. Run:
python -m app.main --adapter discord
```

**MCP Integration:**

```bash
# Connect to GitHub MCP server:
# Edit config.json mcp.clients section
# iTaK can now access your GitHub repos as a tool
```

### 4. **Read More Documentation**

- **[TESTING.md](TESTING.md)** - How to run the 258 tests (85% coverage)
- **[READY_TO_TEST.md](READY_TO_TEST.md)** - Quick reference for testing
- **[PHASE_4_COMPLETE.md](PHASE_4_COMPLETE.md)** - Production readiness details
- **[README.md](../../README.md)** - Full feature list and architecture

### 5. **Join the Community**

- **GitHub Issues**: Report bugs or request features
- **Discord**: [Link to Discord community]
- **Documentation**: [Link to full docs]

### 6. **Customize iTaK**

**Create custom tools:**

```python
# tools/my_tool.py
from tools.base import BaseTool

class MyTool(BaseTool):
    name = "my_custom_tool"
    description = "Does something awesome"
    
    def execute(self, **kwargs):
        return {"result": "awesome"}
```

**Create agent profiles:**

```markdown
# agents/profiles/expert.md
You are an expert Python developer with 10 years experience.
You write clean, well-documented code following PEP 8.
```

**Add extensions:**

```python
# extensions/my_extension.py
def on_message_loop_start(agent, message):
    print(f"New message: {message}")
    # Your custom logic here
```

---

## 🎉 You're Ready

You now have iTaK installed and understand what it does. Start experimenting:

```bash
# Start chatting
python -m app.main

# Or with web dashboard
python -m app.main --webui
```

**First Commands to Try:**

1. `Hello! What can you do?`
2. `Create a Python script that prints "Hello, World!"`
3. `Search the web for today's top tech news`
4. `Remember that I'm learning Python`
5. `Show me what tasks are on the board`

**Happy automating! 🚀**

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/David2024patton/iTaK/issues)
- **Documentation**: See docs/ folder
- **Diagnostics**: Run `python -m app.main --doctor` for health check

---

**Last Updated**: February 2026  
**iTaK Version**: 4.0  
**Test Coverage**: 85% (258 tests)  
**Production Ready**: ✅ Yes (Mission-Critical)
