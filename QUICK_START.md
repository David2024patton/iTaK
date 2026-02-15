# iTaK Quick Start Guide

Get iTaK up and running in **2 minutes** with ONE Python script!

## 🎯 Universal Installer (Recommended)

**ONE command works on ALL platforms** — Linux, macOS, Windows (WSL), and WSL directly!

```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
python install.py
```

That's it! The installer will:
- ✅ Auto-detect your OS (Linux, macOS, Windows, WSL)
- ✅ Install prerequisites (Docker, Git) if needed
- ✅ Ask you: Minimal or Full Stack?
- ✅ Configure everything automatically
- ✅ Start iTaK

**Installation Options:**
```bash
python install.py              # Interactive (recommended)
python install.py --full-stack # Full stack with databases
python install.py --minimal    # iTaK only (fastest)
python install.py --help       # Show all options
```

---

## 🖥️ OS Detection & Platform Support

iTaK **automatically detects** your operating system and uses the right installation method.

**Supported Platforms:**
- ✅ **Linux** (Ubuntu, Debian, Fedora, RHEL, CentOS, Arch)
- ✅ **macOS** (Intel and Apple Silicon)
- ✅ **WSL** (Windows Subsystem for Linux - recommended for Windows)
- ✅ **Windows** (via WSL - auto-installs if missing)

**Universal Installer:**
```bash
# Linux/macOS/WSL - One command detects your OS
./installers/install.sh

# Windows - Auto-detects WSL or offers to install it
installers/install.bat
```

---

## ✅ Prerequisites

Before you begin, you need **either**:
- 🐳 **Docker** (recommended - easiest)  
  OR
- 🐍 **Python 3.11+** (alternative)

**Plus:**
- 📦 **Git** (to clone the repository)
- 💾 **4GB RAM** minimum (8GB+ recommended for full stack)
- 💿 **5GB disk space** minimum (10GB+ for full stack)

### Quick Prerequisites Check

```bash
docker --version   # Should be 20.10+
python3 --version  # Should be 3.11+
git --version      # Should be 2.0+
```

### Don't have them?

**Option 1: Auto-install (Recommended)**
```bash
# Linux/macOS/WSL
./installers/install-prerequisites.sh

# Windows (auto-installs WSL if needed)
installers/install-prerequisites.bat
```

> **Windows Users:** iTaK works best in WSL. The installer will automatically detect if WSL is missing and offer to install it for you!

**Option 2: Manual install**
See [PREREQUISITES.md](PREREQUISITES.md) for complete installation guides.

---

## 🚀 Installation Options

Choose the installation that fits your needs:

### Option 1: Minimal Install (iTaK Only) ⚡ FASTEST

**Best for:** Quick testing, demos, learning

**What you get:**
- ✅ iTaK agent (AI assistant)
- ✅ Basic memory (SQLite-based)
- ✅ Web search (via external APIs)
- ⏱️ Time: 2 minutes

```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
./installers/quick-install.sh
# Choose option 1 when prompted
```

### Option 2: Full Stack Install (Production-Ready) 🏢 RECOMMENDED

**Best for:** Production use, full features, knowledge graphs

**What you get:**
- ✅ iTaK agent (AI assistant)
- ✅ **Neo4j** (knowledge graph database)
- ✅ **SearXNG** (private web search engine)
- ✅ **Weaviate** (vector database for memory)
- ✅ 4-tier advanced memory system
- ⏱️ Time: 5 minutes

```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
./installers/install-full-stack.sh
```

Or use the quick installer and choose option 2:
```bash
./installers/quick-install.sh
# Choose option 2 when prompted
```

**That's it!** Visit http://localhost:8000 and start using iTaK.

---

## 📊 What's the Difference?

| Feature | Minimal Install | Full Stack Install |
|---------|----------------|-------------------|
| **iTaK Agent** | ✅ | ✅ |
| **Web UI** | ✅ | ✅ |
| **Basic Memory** | ✅ SQLite | ✅ SQLite |
| **Neo4j (Knowledge Graph)** | ❌ | ✅ |
| **SearXNG (Private Search)** | ❌ | ✅ |
| **Weaviate (Vector DB)** | ❌ | ✅ |
| **4-Tier Memory System** | ⚠️ Limited | ✅ Full |
| **Installation Time** | 2 min | 5 min |
| **Disk Space** | 500MB | 2-3GB |
| **RAM Usage** | 512MB | 2-4GB |
| **Production Ready** | Testing only | ✅ Yes |

---

## ⚡ What Happens Next?

### 1. First Run Screen

When you first access iTaK, you'll see:

```
🧠 iTaK - Intelligent Task Automation Kernel v4
──────────────────────────────────────────────────

⚠️  FIRST TIME SETUP REQUIRED

iTaK needs at least one LLM API key to function.

Choose your provider:
1. Google Gemini (Recommended - Free tier available)
2. OpenAI GPT-4
3. Anthropic Claude
4. Local Ollama (Free, requires Ollama installed)

Visit: http://localhost:8000/setup
```

### 2. Configuration Wizard

The Web UI will guide you through:

- **Step 1:** Choose your LLM provider
- **Step 2:** Enter API key (or skip for Ollama)
- **Step 3:** Test connection
- **Step 4:** Start using iTaK!

### 3. You're Ready!

Once configured, you can:
- Chat with iTaK in the Web UI
- Ask it to execute code
- Search the web
- Manage tasks
- And much more!

---

## 🔧 Configuration (Optional)

### Adding API Keys Later

If you skip the setup wizard, you can add API keys anytime:

1. **Via Web UI:**
   - Go to http://localhost:8000
   - Click "Settings" tab
   - Add your API keys
   - Save and restart

2. **Via .env file (Advanced):**
   ```bash
   # Stop the container
   docker stop itak
   
   # Access container and edit .env
   docker exec -it itak bash
   nano .env  # Add GEMINI_API_KEY=your_key_here
   
   # Restart
   exit
   docker start itak
   ```

### Supported LLM Providers

| Provider | API Key Variable | Get Key From |
|----------|------------------|--------------|
| Google Gemini | `GEMINI_API_KEY` | https://makersuite.google.com/app/apikey |
| OpenAI | `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| Anthropic | `ANTHROPIC_API_KEY` | https://console.anthropic.com/ |
| OpenRouter | `OPENROUTER_API_KEY` | https://openrouter.ai/keys |
| Local Ollama | `OLLAMA_BASE_URL` | http://localhost:11434 (install Ollama) |

**Tip:** Start with Google Gemini — it has a free tier!

---

## 📊 Quick Start vs Full Install

| Feature | Quick Start | Full Install |
|---------|-------------|--------------|
| **Time to Install** | 2 minutes | 10 minutes |
| **Commands** | 1-2 | 5+ |
| **External Services** | None | Neo4j, Weaviate, SearXNG |
| **Memory** | SQLite only | 4-tier (all stores) |
| **Best For** | Testing, demos | Production, full features |

### When to Use Full Install?

Upgrade to full install when you need:
- **Neo4j knowledge graph** (advanced memory)
- **Weaviate vector search** (semantic memory)
- **SearXNG** (private web search)
- **Production deployment** (full stack)

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for full install instructions.

---

## 🎯 First Commands to Try

Once iTaK is running, try these:

### 1. Hello World
```
User: Hello, what can you do?
```

### 2. Code Execution
```
User: Create a Python script that prints "Hello, iTaK!"
```

### 3. Web Search
```
User: Search the web for today's top tech news
```

### 4. Memory
```
User: Remember that I'm learning Python
```

### 5. Task Management
```
User: Create a task to learn Docker
```

---

## 🆚 Comparison with Agent-Zero

| Aspect | iTaK Quick Start | Agent-Zero |
|--------|------------------|------------|
| **Install Time** | 2 minutes | 3 minutes |
| **Commands** | 1-2 | 2 |
| **Configuration** | Via Web UI | Via Web UI |
| **Memory System** | 4-tier | Basic |
| **Test Coverage** | 85% (258 tests) | Unknown |
| **Production Ready** | ✅ Yes | ⚠️ Experimental |

iTaK matches Agent-Zero's ease of installation while providing enterprise-grade features!

---

## 🔍 Troubleshooting

### Issue: "Port 8000 already in use"

```bash
# Use a different port
docker run -p 8080:8000 david2024patton/itak
# Access at http://localhost:8080
```

### Issue: "Cannot connect to Docker"

Make sure Docker Desktop is running:
- **Windows/Mac:** Start Docker Desktop
- **Linux:** `sudo systemctl start docker`

### Issue: "Image not found"

Build locally:
```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
docker build -f Dockerfile.standalone -t itak .
docker run -p 8000:8000 itak
```

### Issue: "LLM API errors"

Check your API key:
1. Go to Settings in Web UI
2. Verify API key is correct
3. Test connection
4. Save and restart

---

## 📚 Next Steps

### Learn More
- [Full Installation Guide](INSTALLATION_GUIDE.md) - Complete setup with all features
- [iTaK vs Agent-Zero](iTAK_VS_AGENT_ZERO.md) - Detailed comparison
- [Testing Documentation](TESTING.md) - 258 tests, 85% coverage
- [Production Deployment](PRODUCTION_TESTING_SUMMARY.md) - Enterprise ready

### Get Help
- GitHub Issues: https://github.com/David2024patton/iTaK/issues
- Documentation: https://github.com/David2024patton/iTaK/tree/main/docs

### Upgrade to Full Install
When you're ready for production features:
```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

This gives you:
- Neo4j knowledge graph
- Weaviate semantic search
- SearXNG private search
- Full 4-tier memory system
- Production-ready stack

---

## ✅ Summary

**Quick Install = Agent-Zero Simplicity + iTaK Power**

- ⚡ **2-minute install** (just like Agent-Zero)
- 🎯 **One command** to get started
- 🌐 **Web UI** for easy configuration
- 🚀 **Production features** when you need them

**Get started now:**
```bash
curl -fsSL https://raw.githubusercontent.com/David2024patton/iTaK/main/installers/quick-install.sh | bash
```

Enjoy! 🎉
