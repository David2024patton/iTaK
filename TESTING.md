# 🧪 Testing Guide

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
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
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
│   ├── test_core.py           # Core component tests
│   ├── test_memory.py          # TODO: Memory tests
│   ├── test_tools.py           # TODO: Tool tests
│   ├── test_adapters.py        # TODO: Adapter tests
│   ├── test_security.py        # TODO: Security tests
│   ├── test_webui.py           # TODO: WebUI tests
│   ├── test_mcp.py             # TODO: MCP tests
│   └── fixtures/               # TODO: Test fixtures
├── pytest.ini
├── requirements.txt
└── requirements-ci.txt         # Minimal deps for CI
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
# Run all tests
pytest

# Verbose mode
pytest -v

# Very verbose (show print statements)
pytest -vv -s

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Stop on first failure
pytest -x

# Run last failed tests only
pytest --lf

# Run failed tests first, then others
pytest --ff
```

### Coverage Reports

```bash
# Terminal coverage report
pytest --cov=. --cov-report=term

# HTML coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Generate XML for CI
pytest --cov=. --cov-report=xml

# Show missing lines
pytest --cov=. --cov-report=term-missing
```

### Filtering Tests

```bash
# Run tests by keyword
pytest -k "logger"

# Run tests by marker (requires markers in pytest.ini)
pytest -m "slow"
pytest -m "not slow"

# Run specific directory
pytest tests/

# Run specific file
pytest tests/test_core.py
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

### Current Coverage

As of v4.0:
- **Total Lines:** ~15,000
- **Tested Lines:** ~750
- **Coverage:** ~5%

**Tested Components:**
- ✅ Logger (core/logger.py)
- ✅ SQLite Memory Store (memory/sqlite_store.py)
- ✅ Tool Result (helpers/tool_result.py)
- ✅ Progress Tracker (core/progress.py)

**Untested Components:**
- ❌ Agent loop (core/agent.py)
- ❌ Model router (core/models.py)
- ❌ Tools (tools/*.py)
- ❌ Adapters (adapters/*.py)
- ❌ Memory manager (memory/manager.py)
- ❌ Security modules (security/*.py)
- ❌ MCP client/server (core/mcp_*.py)
- ❌ WebUI (webui/*.py)

### Coverage Goals

| Phase | Target | Timeline |
|-------|--------|----------|
| **Phase 1** | 30% | Q1 2024 |
| **Phase 2** | 50% | Q2 2024 |
| **Phase 3** | 70% | Q3 2024 |
| **Phase 4** | 80% | Q4 2024 |

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
python main.py

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
python main.py --webui

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
python main.py --adapter discord --webui

# Telegram
python main.py --adapter telegram --webui

# Slack
python main.py --adapter slack --webui

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
        run: pip install -r requirements-ci.txt
      
      - name: Run linter
        run: ruff check .
      
      - name: Run tests
        run: pytest -v
      
      - name: Run doctor checks
        run: python main.py --doctor
```

### CI Requirements

**`requirements-ci.txt`** (minimal deps for fast CI):
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
# Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
cd /path/to/iTaK
pytest
```

**"Async tests hanging"**
```bash
# Verify pytest.ini has asyncio_mode=auto
cat pytest.ini

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
cp config.json.example config.json

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
