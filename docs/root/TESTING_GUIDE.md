# iTaK Testing Guide

## At a Glance

- Audience: Developers and operators validating quality, readiness, and regression safety.
- Scope: Define practical test flow, readiness criteria, and how to validate changes safely.
- Last reviewed: 2026-02-16.

## Quick Start

- Run focused checks first (`pytest -q` or targeted smoke scripts).
- Use [TESTING.md](TESTING.md) for canonical test commands and order.
- Capture outputs alongside the environment context for reproducibility.

## Deep Dive

The detailed content for this topic starts below.

## AI Notes

- Prefer reproducible commands (`pytest`, smoke scripts) and capture exact outputs.
- Treat numeric metrics as snapshots unless tied to current command output.

## ⚠️ IMPORTANT SECURITY NOTE

**Never share API keys publicly!** API keys should be kept private and secure.

If you've accidentally exposed an API key:

1. **Immediately revoke it** at the provider's dashboard
2. Create a new key
3. Keep the new key private (never commit to git, never share in chat)

For Google Gemini API keys: <https://aistudio.google.com/app/apikey>

---

## Quick Test Overview

iTaK has comprehensive testing at multiple levels:

1. **Unit Tests** (258 tests) - Test individual components
2. **Installer Tests** (7 tests) - Test the installation system
3. **Integration Tests** - Test with real services
4. **System Diagnostics** - Health check all components

---

## Prerequisites for Testing

### Required

- Python 3.11 or higher
- Git
- At least one LLM API key (keep it private!)

### Optional (for full testing)

- Docker (for database services)
- Neo4j, Weaviate, SearXNG (via Docker)

---

## Safe Testing Procedure

### Step 1: Install Dependencies

```bash
# Install required Python packages
pip install -r install/requirements/requirements.txt

# Or use the universal installer
python install.py
```

### Step 2: Configure API Keys (SECURELY)

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
# NEVER commit this file to git!
nano .env
```

Add at least ONE API key to `.env`:

```bash
# Choose one or more providers:
GEMINI_API_KEY=your_private_key_here
# OPENAI_API_KEY=your_private_key_here
# ANTHROPIC_API_KEY=your_private_key_here
```

**Security checklist:**

- ✅ .env is in .gitignore (already configured)
- ✅ Never commit .env to git
- ✅ Never share API keys publicly
- ✅ Use environment variables or .env file only

### Step 3: Run System Diagnostics

```bash
# Check system health (no API calls)
python -m app.main --doctor
```

This will check:

- Python version
- Required packages
- Directory structure
- Configuration files
- API key presence (doesn't expose values)

### Step 4: Run Unit Tests

```bash
# Run all unit tests (no API needed)
PYTHONPATH=$(pwd) python -m pytest tests/ -v

# Run specific test file
PYTHONPATH=$(pwd) python -m pytest tests/test_core.py -v

# Run with coverage
PYTHONPATH=$(pwd) python -m pytest tests/ --cov=. --cov-report=html
```

**Available test suites:**

- `tests/test_core.py` - Core functionality (12 tests)
- `tests/test_security.py` - Security features (28 tests)
- `tests/test_agent.py` - Agent behavior (20 tests)
- `tests/test_tools.py` - Tool execution (28 tests)
- `tests/test_memory.py` - Memory system (19 tests)
- `tests/test_integration.py` - Integration tests (19 tests)
- `tests/test_adapters.py` - Multi-channel adapters (20 tests)
- `tests/test_webui.py` - Web interface (23 tests)
- `tests/test_advanced.py` - Advanced features (20 tests)
- `tests/test_mcp_integration.py` - MCP protocol (18 tests)
- `tests/test_chaos.py` - Chaos engineering (15 tests)
- `tests/test_load.py` - Load testing (15 tests)
- `tests/test_compliance.py` - Compliance (22 tests)

**Total: 258 tests, ~85% coverage**

### Step 5: Test Installer

```bash
# Run installer tests
python test_installer.py
```

Tests:

- Python syntax validation
- Import checks
- Help command
- OS detection
- Version checking
- Argument parsing
- Script structure

### Step 6: Test iTaK (with API key)

```bash
# Terminal mode
python -m app.main

# Web UI mode
python -m app.main --webui
# Visit http://localhost:8000

# CLI mode with specific prompt
python -m app.main --adapter cli
```

### Step 7: Check Database Status (if using full stack)

```bash
# Verify all databases are running
./install/check-databases.sh

# Or check manually
docker compose ps
```

---

## Testing Without Real API Keys

For development/testing without consuming API quota:

### Use Mocked Responses

The test suite includes mocked LLM responses:

```bash
# Unit tests use mocks by default
PYTHONPATH=$(pwd) python -m pytest tests/ -v
```

### Use Ollama (Local, Free)

```bash
# Install Ollama: https://ollama.ai
# Pull a model
ollama pull llama2

# Configure iTaK to use Ollama
# In .env:
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Full Integration Test

To test the complete system with real services:

### 1. Start All Services

```bash
# Full stack installation
python install.py --full-stack

# Or manually
docker compose up -d
```

### 2. Verify Services

```bash
# Check all services are healthy
./install/check-databases.sh

# Should show:
# ✅ Neo4j running
# ✅ Weaviate running
# ✅ SearXNG running
# ✅ SQLite initialized
```

### 3. Run Integration Tests

```bash
# Test with real services
PYTHONPATH=$(pwd) python -m pytest tests/test_integration.py -v

# Test end-to-end workflow
python -m app.main --webui
```

### 4. Test Multi-Channel Adapters

```bash
# Discord (requires DISCORD_TOKEN in .env)
python -m app.main --adapter discord

# Telegram (requires TELEGRAM_TOKEN in .env)
python -m app.main --adapter telegram

# Slack (requires SLACK_TOKEN in .env)
python -m app.main --adapter slack
```

---

## Performance Testing

### Load Testing

```bash
# Run load tests
PYTHONPATH=$(pwd) python -m pytest tests/test_load.py -v

# Test specific load scenarios
# Edit tests/test_load.py to adjust concurrency and duration
```

### Memory Leak Detection

```bash
# Run with memory profiling
python -m memory_profiler main.py
```

---

## Troubleshooting

### Common Issues

**Issue: "No LLM API key found"**

- Solution: Add API key to .env file
- Check: `cat .env | grep API_KEY`

**Issue: "Module not found"**

- Solution: Install dependencies
- Run: `pip install -r install/requirements/requirements.txt`

**Issue: "Docker not found"**

- Solution: Install Docker or use minimal install
- Run: `python install.py --minimal`

**Issue: "Database connection failed"**

- Solution: Start services
- Run: `docker compose up -d`
- Check: `docker compose ps`

**Issue: Tests failing with API errors**

- Solution: Check API key is valid
- Solution: Check internet connection
- Solution: Use mocked tests instead

### Getting Help

1. Check the diagnostics: `python -m app.main --doctor`
2. Check test output: `PYTHONPATH=$(pwd) python -m pytest tests/ -v`
3. Check logs: `tail -f logs/*.log`
4. Read documentation:
   - README.md
   - docs/root/INSTALLATION_GUIDE.md
   - QUICK_START.md
   - docs/root/DATABASES.md

---

## Security Testing

### Verify Security Features

```bash
# Run security tests
PYTHONPATH=$(pwd) python -m pytest tests/test_security.py -v
```

Tests include:

- Secret masking
- PII redaction
- Path traversal prevention
- SSRF protection
- Rate limiting
- Code injection prevention

### Security Scan

```bash
# Check for known vulnerabilities
pip install safety
safety check -r install/requirements/requirements.txt

# Check code quality
pip install bandit
bandit -r . -x ./tests
```

---

## Continuous Testing

### Pre-commit Checks

```bash
# Run before committing
PYTHONPATH=$(pwd) python -m pytest tests/ --maxfail=1

# Quick syntax check
python test_installer.py
```

### Automated Testing

Set up GitHub Actions or similar CI/CD to run tests automatically on:

- Pull requests
- Commits to main branch
- Scheduled intervals

---

## Test Coverage

Current coverage: **~85%** (258 tests)

### View Coverage Report

```bash
# Generate HTML coverage report
PYTHONPATH=$(pwd) python -m pytest tests/ --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html
```

### Coverage by Component

- Security: ~95%
- Core Engine: ~80%
- Memory System: ~80%
- Tools: ~75%
- Adapters: ~65%
- Web UI: ~55%
- Advanced Features: ~60%

---

## Best Practices

### DO

- ✅ Keep API keys in .env (never commit)
- ✅ Run tests before deploying
- ✅ Use --doctor to diagnose issues
- ✅ Test in isolated environment first
- ✅ Review test output carefully
- ✅ Update tests when adding features

### DON'T

- ❌ Commit .env to git
- ❌ Share API keys publicly
- ❌ Skip security tests
- ❌ Test in production first
- ❌ Ignore test failures
- ❌ Hard-code credentials

---

## Summary

iTaK is thoroughly tested with:

- 258 unit/integration tests
- 7 installer tests
- System diagnostics
- Security validation
- Performance testing
- Compliance testing

**All tests verified and passing!** ✅

For questions or issues, see documentation or run diagnostics.
