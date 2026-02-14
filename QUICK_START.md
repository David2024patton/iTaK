# iTaK Quick Start Guide

Get iTaK running in **2 minutes** — just like Agent-Zero!

## 🚀 Super Quick Install (Recommended)

### Option 1: One-Command Install (Linux/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/David2024patton/iTaK/main/quick-install.sh | bash
```

Or download and run:
```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
chmod +x quick-install.sh
./quick-install.sh
```

### Option 2: One-Command Install (Windows)

```cmd
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
quick-install.bat
```

### Option 3: Docker Direct (If you have the image)

```bash
docker run -it --rm -p 8000:8000 david2024patton/itak
```

**That's it!** Visit http://localhost:8000 and start using iTaK.

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
curl -fsSL https://raw.githubusercontent.com/David2024patton/iTaK/main/quick-install.sh | bash
```

Enjoy! 🎉
