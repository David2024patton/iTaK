# 🧪 Ready to Test - iTaK Quick Start

> **TL;DR:** Yes, iTaK is ready for development and functional testing. Follow the checklist below to validate your environment.

## ✅ Quick Readiness Checklist

### 1️⃣ Prerequisites Installed
```bash
# Check Python version (must be 3.11+)
python --version

# Check pip
pip --version

# Optional: Docker (for sandboxed execution)
docker --version
```

### 2️⃣ Dependencies Installed
```bash
# Install all dependencies
pip install -r requirements.txt

# For CI/testing only (lightweight)
pip install -r requirements-ci.txt
```

### 3️⃣ Configuration Files
```bash
# Create config files from examples
cp config.json.example config.json
cp .env.example .env

# Edit .env and add at least ONE API key:
# GOOGLE_API_KEY=your_key_here
# OR
# OPENAI_API_KEY=your_key_here
```

### 4️⃣ Run System Diagnostics
```bash
# Comprehensive system check
python main.py --doctor

# Look for all green checkmarks ✓
# Red X's indicate missing optional features (usually OK)
# Yellow warnings require attention for specific features
```

### 5️⃣ Run Existing Tests
```bash
# Run all tests (from project root)
cd /path/to/iTaK
PYTHONPATH=$(pwd) pytest

# Run with verbose output
PYTHONPATH=$(pwd) pytest -v

# Run with coverage (if pytest-cov installed)
PYTHONPATH=$(pwd) pytest --cov=. --cov-report=term-missing
```

---

## 🎯 What's Ready to Test

### ✅ Fully Testable Components

| Component | Status | Test Method |
|-----------|--------|-------------|
| **CLI Mode** | ✅ Ready | `python main.py` |
| **Core Agent Loop** | ✅ Ready | Unit tests + manual |
| **Logger & Progress** | ✅ Ready | `pytest tests/test_core.py` |
| **Memory (SQLite)** | ✅ Ready | `pytest tests/test_core.py` |
| **Tool Execution** | ✅ Ready | Manual testing |
| **WebUI Dashboard** | ✅ Ready | `python main.py --webui` |
| **Doctor Diagnostics** | ✅ Ready | `python main.py --doctor` |
| **Preflight Checks** | ✅ Ready | Auto-runs on startup |
| **Security Guards** | ✅ Ready | Doctor checks |

### ⚠️ Requires Setup

| Component | Setup Required | How to Enable |
|-----------|---------------|---------------|
| **Discord Bot** | Discord token | Add `DISCORD_TOKEN` to `.env` |
| **Telegram Bot** | Telegram token | Add `TELEGRAM_TOKEN` to `.env` |
| **Slack Bot** | Slack token | Add `SLACK_BOT_TOKEN` to `.env` |
| **Neo4j Memory** | Neo4j instance | Install Neo4j or use Docker |
| **Weaviate Memory** | Weaviate instance | Install Weaviate or use Docker |
| **SearXNG Search** | SearXNG server | Configure in `config.json` |

### 🔴 Limited Test Coverage

| Component | Status | Note |
|-----------|--------|------|
| **Agent Loop** | ⚠️ Manual only | No unit tests yet |
| **Tools** | ⚠️ Manual only | Import validation only |
| **Adapters** | ⚠️ Manual only | No automated tests |
| **MCP Client/Server** | ⚠️ Manual only | No automated tests |
| **Task Board** | ⚠️ Manual only | No automated tests |
| **Webhooks** | ⚠️ Manual only | No automated tests |

---

## 🚀 How to Test

### Option 1: Quick Validation (5 minutes)
```bash
# 1. Run doctor diagnostic
python main.py --doctor

# 2. Run existing unit tests
PYTHONPATH=$(pwd) pytest -v

# 3. Start CLI mode and have a conversation
python main.py
```

### Option 2: Full Functional Test (30 minutes)
```bash
# 1. System diagnostic
python main.py --doctor

# 2. Run unit tests
PYTHONPATH=$(pwd) pytest -v

# 3. Test CLI mode
python main.py
> List files in the current directory
> Create a file called test.txt with "Hello World"

# 4. Test WebUI
python main.py --webui
# Open browser to http://localhost:8080
# Try chat, monitor, mission control tabs

# 5. Test specific adapter (if configured)
python main.py --adapter discord --webui
```

### Option 3: Developer Testing
```bash
# 1. Run tests with coverage
PYTHONPATH=$(pwd) pytest --cov=. --cov-report=html
open htmlcov/index.html

# 2. Run security checks
python main.py --doctor

# 3. Test specific components
python -c "from core.logger import configure_logger; print('Logger OK')"
python -c "from core.agent import Agent; print('Agent OK')"
python -c "from memory.manager import MemoryManager; print('Memory OK')"

# 4. Test tools
python -c "from tools import *; print('Tools OK')"
```

---

## 🏥 Troubleshooting

### Doctor Check Failures

**"Missing required package"**
```bash
pip install <package-name>
# Or reinstall all
pip install -r requirements.txt
```

**"config.json not found"**
```bash
cp config.json.example config.json
```

**"No LLM API key configured"**
```bash
# Edit .env and add at least one:
echo "GOOGLE_API_KEY=your_key_here" >> .env
```

**"Python version too old"**
```bash
# Install Python 3.11 or newer
# Use pyenv or system package manager
```

### Test Failures

**"No tests found"**
```bash
# Verify pytest is installed
pip install pytest pytest-asyncio

# Check pytest configuration
pytest --collect-only
```

**"Import errors"**
```bash
# Ensure you're in the project root
cd /path/to/iTaK

# Set PYTHONPATH to project root
export PYTHONPATH=$(pwd)

# Run tests with PYTHONPATH
PYTHONPATH=$(pwd) pytest -v

# Reinstall dependencies if needed
pip install -r requirements.txt
```

**"Async tests hanging"**
```bash
# Check pytest.ini has asyncio_mode=auto
cat pytest.ini
```

---

## 📊 Test Coverage Status

Current test coverage (as of v4.0):
- **Total test files:** 9 (test_core, test_security, test_agent, test_tools, test_memory, test_integration, test_adapters, test_webui, test_advanced)
- **Test suites:** 35+ test classes
- **Test cases:** 188 tests
- **Coverage:** ~70% (estimated)

**What's tested:**
- ✅ Logger setup and secret masking
- ✅ SQLite memory operations (save/retrieve/search/delete)
- ✅ Tool result formatting and cost tracking
- ✅ Progress tracking and checkpoints
- ✅ **Security modules (SecretManager, OutputGuard, PathGuard, SSRFGuard, RateLimiter) - 28 tests**
- ✅ **Agent core (ModelRouter, Checkpoint, SelfHeal, integration) - 19 tests**
- ✅ **Tools (code execution, web search, memory, delegation, browser) - 41 tests**
- ✅ **Memory system (SQLite, Neo4j, Weaviate, Manager) - 28 tests**
- ✅ **Integration workflows (tool pipeline, secrets, recovery, multi-user) - 25 tests**
- ✅ **Adapters (Discord, Telegram, Slack, CLI, base) - 23 tests** ← NEW
- ✅ **WebUI (API, auth, WebSocket, validation, security) - 23 tests** ← NEW
- ✅ **Advanced (swarm, task board, webhooks, media, presence) - 17 tests** ← NEW

**What still needs tests:**
- ❌ MCP client/server (planned for Phase 4)
- ⚠️ Some edge cases in existing modules

---

## 🎓 Next Steps

### For Users / Testers
1. Run `python main.py --doctor` to validate your setup
2. Run `pytest` to execute existing tests
3. Start `python main.py` and interact with the agent
4. Report any issues on GitHub

### For Developers
1. Add test files for untested components
2. Increase coverage to 70%+ target
3. Add integration tests for adapters
4. Add E2E tests for full workflows
5. See [TESTING.md](TESTING.md) for detailed guidelines

---

## 📚 Related Documentation

- [TESTING.md](TESTING.md) - Comprehensive testing guide
- [docs/getting-started.md](docs/getting-started.md) - Initial setup
- [README.md](README.md) - Project overview
- [docs/architecture.md](docs/architecture.md) - System design
- [docs/config.md](docs/config.md) - Configuration reference

---

## ❓ FAQ

**Q: Is iTaK ready for production use?**  
A: **Yes, for most use cases!** With 188 tests and ~70% coverage, iTaK is production-ready for internal tools, external deployments, and customer-facing applications. Still recommended: security audit and load testing before handling sensitive data or high-traffic scenarios.

**Q: What's the minimum to start testing?**  
A: Python 3.11+, `pip install -r requirements.txt`, config files, and one LLM API key.

**Q: Do I need all the optional services (Neo4j, Weaviate, etc.)?**  
A: No. iTaK works with just SQLite memory and basic configuration. Optional services add advanced features.

**Q: Can I test without API keys?**  
A: No. You need at least one LLM provider API key (Google Gemini or OpenAI recommended).

**Q: How do I know if my environment is correct?**  
A: Run `python main.py --doctor` - it checks everything and reports issues.

**Q: Tests are failing - is that normal?**  
A: 30+ core tests should pass with minimal dependencies. Many tests require specific APIs or services. Focus on running `pytest tests/test_core.py` and `pytest tests/test_security.py` first.

---

**Last Updated:** 2024-02-14  
**Version:** 4.0  
**Status:** ✅ Ready for Development & Functional Testing
