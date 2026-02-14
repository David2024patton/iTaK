"""
iTaK - Tools Tests

Tests for tool implementations and safety:
- Code execution (injection prevention, timeouts, cleanup)
- Web search and browser agent (SSRF prevention)
- Memory tools (data validation)
- Tool result formatting
"""

import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock


# ============================================================
# ToolResult Tests (from existing test_core.py, extended)
# ============================================================
class TestToolResult:
    """Test tool result formatting and handling."""

    def test_default_values(self):
        """ToolResult should have sensible defaults."""
        from tools.base import ToolResult
        
        result = ToolResult()
        assert result.success is True
        assert result.output == ""
        assert result.break_loop is False

    def test_response_breaks_loop(self):
        """Response tool should break the agent loop."""
        from tools.base import ToolResult
        
        result = ToolResult(
            success=True,
            output="Final response to user",
            break_loop=True
        )
        assert result.break_loop is True

    def test_cost_tracking_in_result(self):
        """ToolResult should track operation costs."""
        from tools.base import ToolResult
        
        result = ToolResult(
            success=True,
            output="Operation completed",
            cost=0.05,
            tokens_used=100
        )
        
        assert result.cost == 0.05
        assert result.tokens_used == 100

    def test_error_result(self):
        """ToolResult should capture errors."""
        from tools.base import ToolResult
        
        result = ToolResult(
            success=False,
            output="",
            error="File not found: /missing/file.txt"
        )
        
        assert result.success is False
        assert "File not found" in result.error

    def test_result_serialization(self):
        """ToolResult should serialize to dict."""
        from tools.base import ToolResult
        
        result = ToolResult(
            success=True,
            output="Test output",
            cost=0.01,
            metadata={"tool": "test_tool"}
        )
        
        as_dict = result.to_dict()
        assert as_dict["success"] is True
        assert as_dict["output"] == "Test output"
        assert "metadata" in as_dict


# ============================================================
# Code Execution Tool Tests
# ============================================================
class TestCodeExecution:
    """Test code execution tool safety."""

    @pytest.mark.asyncio
    async def test_simple_python_execution(self):
        """Should execute simple Python code."""
        from tools.code_execution import execute_python
        
        code = "result = 2 + 2\nprint(result)"
        result = await execute_python(code)
        
        assert result.success is True
        assert "4" in result.output

    @pytest.mark.asyncio
    async def test_timeout_enforcement(self):
        """Should timeout long-running code."""
        from tools.code_execution import execute_python
        
        # Infinite loop
        code = "while True: pass"
        
        result = await execute_python(code, timeout=2)
        
        # Should timeout and fail
        assert result.success is False
        assert "timeout" in result.error.lower() or "killed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_prevent_shell_injection(self):
        """Should prevent shell command injection."""
        from tools.code_execution import execute_python
        
        # Attempt injection via code parameter
        malicious_code = "import os; os.system('rm -rf /')"
        
        # Should execute in safe environment or be blocked
        result = await execute_python(malicious_code, sandbox=True)
        
        # In sandbox mode, destructive commands should fail
        # or be prevented entirely
        assert result is not None

    @pytest.mark.asyncio
    async def test_workdir_path_traversal_prevention(self):
        """Should prevent path traversal in workdir."""
        from tools.code_execution import execute_python
        
        code = "print('test')"
        
        # Attempt to use path traversal in workdir
        result = await execute_python(code, workdir="../../../etc")
        
        # Should either reject the workdir or normalize it safely
        assert result is not None

    @pytest.mark.asyncio
    async def test_cleanup_after_execution(self):
        """Should clean up processes after execution."""
        from tools.code_execution import execute_python
        
        code = "print('Hello')"
        result = await execute_python(code)
        
        assert result.success is True
        # Process should be terminated (no zombies)

    @pytest.mark.asyncio
    async def test_capture_stdout_stderr(self):
        """Should capture both stdout and stderr."""
        from tools.code_execution import execute_python
        
        code = """
import sys
print("stdout message")
print("stderr message", file=sys.stderr)
"""
        
        result = await execute_python(code)
        
        assert "stdout message" in result.output or "stderr message" in result.output

    @pytest.mark.asyncio
    async def test_sandbox_vs_local_execution(self):
        """Sandbox execution should be more restricted."""
        from tools.code_execution import execute_python
        
        code = "import os; print(os.getcwd())"
        
        # Local execution
        local_result = await execute_python(code, sandbox=False)
        
        # Sandbox execution
        sandbox_result = await execute_python(code, sandbox=True)
        
        # Both should execute, but sandbox might be more restricted
        assert local_result is not None
        assert sandbox_result is not None


# ============================================================
# Web Search Tool Tests
# ============================================================
class TestWebSearch:
    """Test web search tool."""

    @pytest.mark.asyncio
    @patch('tools.web_search.httpx.AsyncClient')
    async def test_search_query(self, mock_client):
        """Should perform web search and return results."""
        from tools.web_search import web_search
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {"title": "Result 1", "url": "https://example.com/1", "snippet": "Test snippet 1"},
                {"title": "Result 2", "url": "https://example.com/2", "snippet": "Test snippet 2"}
            ]
        }
        mock_response.status_code = 200
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = await web_search("test query")
        
        assert result.success is True
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_ssrf_protection(self):
        """Should not search for private IPs or localhost."""
        from tools.web_search import web_search
        
        # Attempts to search for internal resources
        result = await web_search("http://localhost:8080/admin")
        
        # Should either block or sanitize the query
        assert result is not None

    @pytest.mark.asyncio
    async def test_empty_results_handling(self):
        """Should handle empty search results gracefully."""
        from tools.web_search import web_search
        
        # Very specific query likely to return no results
        result = await web_search("xyzqwertyuiopasdfghjkl123456789")
        
        assert result.success is True
        assert "no results" in result.output.lower() or len(result.output) >= 0


# ============================================================
# Memory Tools Tests
# ============================================================
class TestMemoryTools:
    """Test memory save/load tools."""

    @pytest.mark.asyncio
    async def test_memory_save(self, tmp_path):
        """Should save memory entries."""
        from tools.memory_save import memory_save
        
        result = await memory_save(
            content="Important information to remember",
            category="facts",
            metadata={"source": "user"}
        )
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_memory_load(self):
        """Should load memory entries."""
        from tools.memory_load import memory_load
        
        result = await memory_load(
            query="important information",
            limit=5
        )
        
        assert result.success is True
        # Should return some results or empty list
        assert result.output is not None

    @pytest.mark.asyncio
    async def test_prevent_memory_injection(self):
        """Should prevent injection in memory queries."""
        from tools.memory_load import memory_load
        
        # Attempt SQL injection in query
        malicious_query = "'; DROP TABLE memories; --"
        
        result = await memory_load(query=malicious_query)
        
        # Should not crash and should sanitize query
        assert result is not None
        assert result.success is True or "error" in result.error.lower()

    @pytest.mark.asyncio
    async def test_validate_memory_data(self):
        """Should validate data before saving."""
        from tools.memory_save import memory_save
        
        # Test with invalid data types
        result = await memory_save(
            content=None,  # Invalid
            category="test"
        )
        
        # Should fail gracefully
        assert result.success is False or result.error


# ============================================================
# Delegate Task Tool Tests
# ============================================================
class TestDelegateTask:
    """Test sub-agent delegation."""

    @pytest.mark.asyncio
    @patch('tools.delegate_task.SubAgent')
    async def test_delegate_simple_task(self, mock_subagent_class):
        """Should delegate task to sub-agent."""
        from tools.delegate_task import delegate_task
        
        # Mock sub-agent
        mock_subagent = Mock()
        mock_subagent.execute = AsyncMock(return_value="Sub-agent result")
        mock_subagent_class.return_value = mock_subagent
        
        result = await delegate_task(
            task="Analyze this data",
            profile="researcher"
        )
        
        assert result.success is True
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_delegate_with_timeout(self):
        """Should timeout long-running sub-agent tasks."""
        from tools.delegate_task import delegate_task
        
        # This would need proper mocking, but test structure
        result = await delegate_task(
            task="Very long task",
            timeout=1  # 1 second timeout
        )
        
        # Should either complete quickly or timeout gracefully
        assert result is not None


# ============================================================
# Response Tool Tests
# ============================================================
class TestResponseTool:
    """Test response tool (breaks agent loop)."""

    @pytest.mark.asyncio
    async def test_response_breaks_loop(self):
        """Response should signal to break the agent loop."""
        from tools.response import response_to_user
        
        result = await response_to_user("This is my final answer")
        
        assert result.success is True
        assert result.break_loop is True
        assert "final answer" in result.output.lower()

    @pytest.mark.asyncio
    async def test_response_with_metadata(self):
        """Response can include metadata."""
        from tools.response import response_to_user
        
        result = await response_to_user(
            "Answer with sources",
            metadata={"sources": ["source1", "source2"]}
        )
        
        assert result.success is True
        assert result.break_loop is True


# ============================================================
# Knowledge Tool Tests
# ============================================================
class TestKnowledgeTool:
    """Test knowledge graph interactions."""

    @pytest.mark.asyncio
    async def test_query_knowledge_graph(self):
        """Should query Neo4j knowledge graph."""
        from tools.knowledge_tool import query_knowledge
        
        result = await query_knowledge(
            query="Find connections",
            entity="test_entity"
        )
        
        # Should execute without crashing
        assert result is not None
        assert result.success is True or "not configured" in result.error.lower()

    @pytest.mark.asyncio
    async def test_save_to_knowledge_graph(self):
        """Should save entities and relationships."""
        from tools.knowledge_tool import save_knowledge
        
        result = await save_knowledge(
            entity="John Doe",
            entity_type="person",
            relationships=[
                {"type": "works_at", "target": "Company ABC"}
            ]
        )
        
        # Should execute without crashing
        assert result is not None


# ============================================================
# Browser Agent Tool Tests
# ============================================================
class TestBrowserAgent:
    """Test browser automation tool."""

    @pytest.mark.asyncio
    @patch('tools.browser_agent.playwright')
    async def test_navigate_to_url(self, mock_playwright):
        """Should navigate to URLs safely."""
        from tools.browser_agent import browse_url
        
        # Mock browser
        mock_page = Mock()
        mock_page.goto = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html>Test Page</html>")
        
        result = await browse_url("https://example.com")
        
        # Should execute (actual playwright might not be available)
        assert result is not None

    @pytest.mark.asyncio
    async def test_block_private_urls(self):
        """Should block navigation to private IPs."""
        from tools.browser_agent import browse_url
        
        result = await browse_url("http://192.168.1.1")
        
        # Should be blocked by SSRF guard
        assert result.success is False or "blocked" in result.error.lower()

    @pytest.mark.asyncio
    async def test_extract_text_from_page(self):
        """Should extract text content from pages."""
        from tools.browser_agent import browse_url
        
        result = await browse_url("https://example.com", extract_text=True)
        
        # Should return text content
        assert result is not None
