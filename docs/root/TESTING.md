# 🧪 Testing Guide

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


> Comprehensive guide for testing iTaK components, writing tests, and ensuring quality.

## Table of Contents

- [Quick Start](#quick-start)
- [Test Infrastructure](#test-infrastructure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Coverage](#test-coverage)
- [Testing Components](#testing-components)
- [Integration Testing](#integration-testing)
- [Manual Testing](#manual-testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# Install test dependencies
pip install -r install/requirements/requirements.txt

# Set PYTHONPATH to project root (required for imports)
export PYTHONPATH=/path/to/iTaK

# Or run from project root with:
cd /path/to/iTaK
PYTHONPATH=$(pwd) pytest

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_core.py

# Run specific test class
pytest tests/test_core.py::TestLogger

# Run specific test function
pytest tests/test_core.py::TestLogger::test_configure_logger

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

---

## Test Infrastructure

### Pytest Configuration

**`pytest.ini`:**
```ini
[pytest]
testpaths = tests
asyncio_mode = auto
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### Directory Structure

```
iTaK/
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   ├── test_agent.py
│   ├── test_agent_safety.py
│   ├── test_memory.py
│   ├── test_tools.py
│   ├── test_adapters.py
│   ├── test_security.py
│   ├── test_webui.py
│   ├── test_integration.py
│   ├── test_mcp_integration.py
│   ├── test_load.py
│   ├── test_compliance.py
│   ├── test_chaos.py
│   ├── test_performance.py
│   ├── test_installer.py
│   ├── test_memu.py
│   └── test_advanced.py
├── tests/pytest.ini
├── install/requirements/requirements.txt
└── install/requirements/requirements-ci.txt  # Minimal deps for CI
```

### Test Dependencies

**Core:**
- `pytest>=8.0.0` - Test framework
- `pytest-asyncio>=0.24.0` - Async test support

**Optional:**
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `pytest-timeout` - Test timeout enforcement

---

## Running Tests

### Basic Commands

```bash
# Run all tests (from project root)
cd /path/to/iTaK
PYTHONPATH=$(pwd) pytest

# Verbose mode
PYTHONPATH=$(pwd) pytest -v

# Very verbose (show print statements)
PYTHONPATH=$(pwd) pytest -vv -s

# Run tests in parallel (requires pytest-xdist)
PYTHONPATH=$(pwd) pytest -n auto

# Stop on first failure
PYTHONPATH=$(pwd) pytest -x

# Run last failed tests only
PYTHONPATH=$(pwd) pytest --lf

# Run failed tests first, then others
PYTHONPATH=$(pwd) pytest --ff
```

### Coverage Reports

```bash
# Terminal coverage report
PYTHONPATH=$(pwd) pytest --cov=. --cov-report=term

# HTML coverage report
PYTHONPATH=$(pwd) pytest --cov=. --cov-report=html
open htmlcov/index.html

# Generate XML for CI
PYTHONPATH=$(pwd) pytest --cov=. --cov-report=xml

# Show missing lines
PYTHONPATH=$(pwd) pytest --cov=. --cov-report=term-missing
```

### Filtering Tests

```bash
# Run tests by keyword
PYTHONPATH=$(pwd) pytest -k "logger"

# Run tests by marker (requires markers in pytest.ini)
PYTHONPATH=$(pwd) pytest -m "slow"
PYTHONPATH=$(pwd) pytest -m "not slow"

# Run specific directory
PYTHONPATH=$(pwd) pytest tests/

# Run specific file
PYTHONPATH=$(pwd) pytest tests/test_core.py
```

---

## Writing Tests

### Test File Template

```python
"""
Tests for [component name].
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock


class Test[ComponentName]:
    """Test suite for [ComponentName]."""

    def test_basic_functionality(self):
        """Test basic [component] functionality."""
        # Arrange
        component = ComponentName()
        
        # Act
        result = component.do_something()
        
        # Assert
        assert result is not None
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async [component] functionality."""
        # Arrange
        component = ComponentName()
        
        # Act
        result = await component.do_async_something()
        
        # Assert
        assert result is not None


class Test[ComponentName]ErrorHandling:
    """Test error handling for [ComponentName]."""

    def test_invalid_input(self):
        """Test handling of invalid input."""
        component = ComponentName()
        
        with pytest.raises(ValueError):
            component.do_something(invalid_param=True)
```

### Async Test Example

```python
import pytest


class TestAgent:
    """Test Agent functionality."""

    @pytest.mark.asyncio
    async def test_message_processing(self):
        """Test agent processes messages correctly."""
        from core.agent import Agent
        
        # Arrange
        config = {
            "agent": {"name": "TestAgent"},
            "models": {"router": {"default": "mock-model"}}
        }
        agent = Agent(config, user_id="test-user")
        
        # Act
        response = await agent.process_message("Hello, agent!")
        
        # Assert
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
```

### Mocking Example

```python
from unittest.mock import Mock, patch, AsyncMock


class TestToolExecution:
    """Test tool execution."""

    @patch('core.agent.subprocess.run')
    def test_bash_tool_execution(self, mock_run):
        """Test bash tool execution with mocked subprocess."""
        # Arrange
        mock_run.return_value = Mock(
            stdout="Command output",
            stderr="",
            returncode=0
        )
        
        # Act
        from tools.bash import execute_bash
        result = execute_bash("echo 'test'")
        
        # Assert
        assert result.success is True
        assert "Command output" in result.output
        mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch('core.models.litellm.acompletion')
    async def test_llm_call(self, mock_completion):
        """Test LLM call with mocked response."""
        # Arrange
        mock_completion.return_value = AsyncMock(
            choices=[Mock(message=Mock(content="Test response"))]
        )
        
        # Act
        from core.models import ModelRouter
        router = ModelRouter({"default": "mock-model"})
        response = await router.complete("Test prompt")
        
        # Assert
        assert response == "Test response"
        mock_completion.assert_called_once()
```

### Fixture Example

```python
import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def temp_config():
    """Provide a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"agent": {"name": "Test"}, "models": {}}')
        config_path = Path(f.name)
    
    yield config_path
    
    config_path.unlink()


@pytest.fixture
def mock_agent():
    """Provide a mock agent instance."""
    config = {
        "agent": {"name": "TestAgent"},
        "models": {"router": {"default": "mock-model"}}
    }
    from core.agent import Agent
    return Agent(config, user_id="test-user")


class TestWithFixtures:
    """Test using fixtures."""

    def test_with_temp_config(self, temp_config):
        """Test with temporary config file."""
        assert temp_config.exists()
        assert temp_config.suffix == '.json'

    @pytest.mark.asyncio
    async def test_with_mock_agent(self, mock_agent):
        """Test with mock agent."""
        assert mock_agent.name == "TestAgent"
```

---

## Test Coverage

### Current Snapshot

Repository snapshot (2026-02-16):
- **Pytest collected tests:** 396 (`pytest tests --collect-only -q`)
- **Test files:** 17 (`tests/test_*.py`)
- **Coverage:** run `pytest --cov=. --cov-report=term-missing` to calculate for your environment

**Key suites in tree:**
- ✅ Core / Agent: `test_core.py`, `test_agent.py`, `test_agent_safety.py`
- ✅ Memory: `test_memory.py`, `test_memu.py`
- ✅ Tools: `test_tools.py`
- ✅ WebUI: `test_webui.py`
- ✅ Security: `test_security.py`
- ✅ Integration / MCP: `test_integration.py`, `test_mcp_integration.py`
- ✅ Performance / Load / Chaos: `test_performance.py`, `test_load.py`, `test_chaos.py`
- ✅ Compliance scenarios: `test_compliance.py`
- ✅ Installer / advanced flows: `test_installer.py`, `test_advanced.py`

### Smoke Testing (UI + CLI)

After changing settings/options, run smoke checks either from the WebUI (**Settings → External Services → System Smoke Tests**) or via CLI:

```bash
bash tools/check_resource_endpoints.sh
bash tools/check_memory_smoke.sh
bash tools/check_chat_smoke.sh
bash tools/check_system_smoke.sh
```

Optional dynamic target:

```bash
WEBUI_BASE_URL=http://127.0.0.1:43067 bash tools/check_system_smoke.sh
```
  - Tool pipeline, secret lifecycle, crash recovery, multi-user
- ✅ Adapters (adapters/*.py) - 20 tests
  - Discord, Telegram, Slack, CLI, base interface, performance
- ✅ WebUI (webui/*.py) - 23 tests
  - API endpoints, authentication, WebSocket, validation, security
- ✅ Advanced features - 20 tests
  - Swarm, task board, webhooks, media, presence, config watcher
- ✅ **MCP integration (core/mcp_*.py) - 18 tests** ← Phase 4
  - Client connection, tool discovery, remote invocation, error handling
- ✅ **Chaos engineering - 15 tests** ← Phase 4
  - Network failures, DB failures, resource exhaustion, resilience
- ✅ **Load testing - 15 tests** ← Phase 4
  - High concurrency, stability, memory leaks, performance
- ✅ **Compliance - 22 tests** ← Phase 4
  - HIPAA, PCI DSS, SOC2, GDPR, privacy by design

### Coverage Goals

| Phase | Target | Tests | Status |
|-------|--------|-------|--------|
| **Phase 1** | 30% | 40+ | ✅ EXCEEDED (85% achieved with 258 tests) |
| **Phase 2** | 50% | 70+ | ✅ EXCEEDED (85% achieved with 258 tests) |
| **Phase 3** | 70% | 100+ | ✅ EXCEEDED (85% achieved with 258 tests) |
| **Phase 4** | 80% | 150+ | ✅ COMPLETE (85% achieved with 258 tests) |

### Coverage Commands

```bash
# Generate coverage report
pytest --cov=. --cov-report=term-missing

# Exclude specific directories
pytest --cov=. --cov-omit="*/tests/*,*/venv/*" --cov-report=term

# Set minimum coverage threshold (fail if below)
pytest --cov=. --cov-fail-under=30

# Generate badge-friendly output
pytest --cov=. --cov-report=term | grep "TOTAL"
```

---

## Testing Components

### Core Components

#### Agent Loop
```bash
# TODO: Create tests/test_agent.py
pytest tests/test_agent.py
```

**What to test:**
- Message processing
- Monologue loop execution
- Tool execution integration
- Error recovery
- Context management

#### Model Router
```bash
# TODO: Create tests/test_models.py
pytest tests/test_models.py
```

**What to test:**
- Model selection
- Fallback chains
- Token counting
- Cost tracking
- Streaming responses

#### Tools
```bash
# TODO: Create tests/test_tools.py
pytest tests/test_tools.py
```

**What to test:**
- Tool registration
- Tool execution
- Parameter validation
- Error handling
- Security checks

### Memory System

```bash
# TODO: Create tests/test_memory.py
pytest tests/test_memory.py
```

**What to test:**
- Tier management
- CRUD operations
- Search functionality
- Compaction
- Neo4j integration
- Weaviate integration

### Security

```bash
# TODO: Create tests/test_security.py
pytest tests/test_security.py
```

**What to test:**
- SSRF protection
- Path traversal protection
- Secret masking
- Auth token validation
- Rate limiting
- Output guard

### Adapters

```bash
# TODO: Create tests/test_adapters.py
pytest tests/test_adapters.py
```

**What to test:**
- Message handling
- Event processing
- Connection management
- Error recovery
- Rate limiting

### WebUI

```bash
# TODO: Create tests/test_webui.py
pytest tests/test_webui.py
```

**What to test:**
- API endpoints
- Authentication
- WebSocket connections
- File uploads
- Error responses

---

## Integration Testing

### Example Integration Test

```python
"""Integration tests for full workflows."""

import pytest
from pathlib import Path


class TestChatWorkflow:
    """Test complete chat workflow."""

    @pytest.mark.asyncio
    async def test_cli_chat_flow(self):
        """Test CLI adapter chat flow end-to-end."""
        # Arrange
        from core.agent import Agent
        from adapters.cli import CLIAdapter
        
        config = load_config()
        agent = Agent(config, user_id="test-user")
        adapter = CLIAdapter(agent)
        
        # Act
        response = await adapter.process_message("List files in current directory")
        
        # Assert
        assert response is not None
        assert "file" in response.lower() or "directory" in response.lower()

    @pytest.mark.asyncio
    async def test_tool_execution_flow(self):
        """Test tool execution from message to response."""
        # Arrange
        from core.agent import Agent
        
        config = load_config()
        agent = Agent(config, user_id="test-user")
        
        # Act
        response = await agent.process_message("Create a file called test.txt")
        
        # Assert
        assert Path("test.txt").exists()
        
        # Cleanup
        Path("test.txt").unlink(missing_ok=True)
```

---

## Manual Testing

### CLI Testing

```bash
# Start CLI adapter
python -m app.main

# Test commands:
> Hello, what can you do?
> List files in the current directory
> Create a file called test.txt with "Hello World"
> Read the file test.txt
> Delete test.txt
> Search the web for "Python testing best practices"
> Execute Python code: print(2 + 2)
```

### WebUI Testing

```bash
# Start WebUI
python -m app.main --webui

# Open browser to http://localhost:8080

# Test tabs:
1. Monitor - Check stats, send messages
2. Mission Control - Create tasks, move cards
3. Tools - Verify tools load
4. Logs - Check log entries
5. Subsystems - Verify health status
6. Users - Check user management
```

### Adapter Testing

```bash
# Discord
python -m app.main --adapter discord --webui

# Telegram
python -m app.main --adapter telegram --webui

# Slack
python -m app.main --adapter slack --webui

# Test in each platform:
1. Send message to bot
2. Verify response
3. Test tool execution
4. Test file operations
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

**`.github/workflows/ci.yml`:**
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]

    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: pip install -r install/requirements/requirements-ci.txt
      
      - name: Run linter
        run: ruff check .
      
      - name: Run tests
        run: PYTHONPATH=$(pwd) pytest -v
      
      - name: Run doctor checks
        run: python -m app.main --doctor
```

### CI Requirements

**`install/requirements/requirements-ci.txt`** (minimal deps for fast CI):
```
litellm>=1.50.0,<2.0.0
pydantic>=2.0.0,<3.0.0
python-dotenv>=1.0.0,<2.0.0
tiktoken>=0.7.0,<1.0.0
dirtyjson>=1.0.8,<2.0.0
aiosqlite>=0.20.0,<1.0.0
pytest>=8.0.0,<9.0.0
pytest-asyncio>=0.24.0,<1.0.0
```

---

## Troubleshooting

### Common Issues

**"No tests found"**
```bash
# Check pytest configuration
pytest --collect-only

# Verify test file naming
ls tests/test_*.py

# Ensure tests/ has __init__.py
touch tests/__init__.py
```

**"Import errors in tests"**
```bash
# Ensure project root is in PYTHONPATH (REQUIRED)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run tests with PYTHONPATH inline
cd /path/to/iTaK
PYTHONPATH=$(pwd) pytest

# For permanent solution, add to pytest config
# or run tests from project root with PYTHONPATH set
```

**"Async tests hanging"**
```bash
# Verify pytest.ini has asyncio_mode=auto
cat tests/pytest.ini

# Install pytest-asyncio
pip install pytest-asyncio
```

**"Coverage not found"**
```bash
# Install coverage plugin
pip install pytest-cov

# Verify coverage command
pytest --cov=. --cov-report=term
```

**"Test failures due to missing config"**
```bash
# Create minimal test config
cp install/config/config.json.example config.json

# Or use fixture to mock config
@pytest.fixture
def mock_config():
    return {"agent": {}, "models": {}}
```

---

## Best Practices

### DO
✅ Write tests for all new features  
✅ Test edge cases and error conditions  
✅ Use descriptive test names  
✅ Keep tests isolated and independent  
✅ Use fixtures for common setup  
✅ Mock external dependencies  
✅ Test async functions with `@pytest.mark.asyncio`  
✅ Clean up resources in tests (files, DB, etc.)  
✅ Run tests before committing  

### DON'T
❌ Test implementation details  
❌ Write tests that depend on execution order  
❌ Leave hardcoded paths or credentials  
❌ Skip cleanup in tests  
❌ Test multiple things in one test  
❌ Commit failing tests  
❌ Ignore flaky tests  
❌ Mock everything (test real integrations too)  

---

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Python testing best practices](https://docs.python-guide.org/writing/tests/)
- [READY_TO_TEST.md](READY_TO_TEST.md) - Quick readiness guide

---

**Last Updated:** 2024-02-14  
**Version:** 4.0
