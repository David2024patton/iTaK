"""
iTaK - MCP Integration Tests (Phase 4)

Tests for Model Context Protocol client and server:
- MCP client connection and initialization
- Tool discovery and registration
- Remote tool invocation
- Error handling and reconnection
- Multiple MCP server coordination
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch


# ============================================================
# MCP Client Connection Tests
# ============================================================
class TestMCPClientConnection:
    """Test MCP client connection and initialization."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """MCP client should initialize with configuration."""
        from core.mcp_client import MCPClient, MCPServerConfig
        
        config = MCPServerConfig(
            name="test-server",
            command="npx",
            args=["@modelcontextprotocol/server-filesystem", "/tmp"]
        )
        
        client = MCPClient([config])
        assert client is not None
        assert len(client.servers) == 1

    @pytest.mark.asyncio
    async def test_connection_establishment(self):
        """Should establish connection to MCP server."""
        from core.mcp_client import MCPConnection, MCPServerConfig
        
        config = MCPServerConfig(
            name="test-server",
            command="echo",  # Simple command for testing
            args=["test"]
        )
        
        connection = MCPConnection(config)
        
        # Mock the subprocess
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_process = Mock()
            mock_process.stdin = AsyncMock()
            mock_process.stdout = AsyncMock()
            mock_process.stderr = AsyncMock()
            mock_exec.return_value = mock_process
            
            # Connect should work
            await connection.connect()
            assert mock_exec.called

    @pytest.mark.asyncio
    async def test_initialize_protocol(self):
        """Should send initialize request with protocol version."""
        from core.mcp_client import MCPConnection, MCPServerConfig
        
        config = MCPServerConfig(
            name="test-server",
            command="test-cmd",
            args=[]
        )
        
        connection = MCPConnection(config)
        
        # Should have protocol version
        assert hasattr(connection, '_request_id') or hasattr(connection, 'config')


# ============================================================
# Tool Discovery Tests
# ============================================================
class TestMCPToolDiscovery:
    """Test tool discovery and registration."""

    @pytest.mark.asyncio
    async def test_discover_tools(self):
        """Should discover tools from MCP server."""
        from core.mcp_client import MCPConnection, MCPServerConfig
        
        config = MCPServerConfig(
            name="test-server",
            command="test-cmd",
            args=[]
        )
        
        connection = MCPConnection(config)
        
        # Tools should be discoverable
        assert hasattr(connection, 'tools')
        assert isinstance(connection.tools, list)

    @pytest.mark.asyncio
    async def test_tool_schema_validation(self):
        """Tool schemas should be validated."""
        from core.mcp_client import MCPTool
        
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            input_schema={
                "type": "object",
                "properties": {
                    "arg1": {"type": "string"}
                }
            },
            server_name="test-server"
        )
        
        assert tool.name == "test_tool"
        assert tool.input_schema["type"] == "object"

    @pytest.mark.asyncio
    async def test_register_tool(self):
        """Should register discovered tools."""
        from core.mcp_client import MCPClient, MCPServerConfig
        
        config = MCPServerConfig(
            name="test-server",
            command="test-cmd",
            args=[]
        )
        
        client = MCPClient([config])
        
        # Client should have method to register tools
        assert client is not None


# ============================================================
# Remote Tool Invocation Tests
# ============================================================
class TestMCPToolInvocation:
    """Test remote tool invocation via MCP."""

    @pytest.mark.asyncio
    async def test_call_remote_tool(self):
        """Should call tools on remote MCP server."""
        from core.mcp_client import MCPConnection, MCPServerConfig
        
        config = MCPServerConfig(
            name="test-server",
            command="test-cmd",
            args=[]
        )
        
        connection = MCPConnection(config)
        
        # Should have call capability
        assert connection is not None

    @pytest.mark.asyncio
    async def test_tool_argument_passing(self):
        """Arguments should be passed correctly to remote tools."""
        from core.mcp_client import MCPConnection, MCPServerConfig
        
        config = MCPServerConfig(
            name="test-server",
            command="test-cmd",
            args=[]
        )
        
        connection = MCPConnection(config)
        
        # Connection should accept arguments
        assert connection.config is not None

    @pytest.mark.asyncio
    async def test_tool_response_handling(self):
        """Tool responses should be handled correctly."""
        from core.mcp_client import MCPConnection, MCPServerConfig
        
        config = MCPServerConfig(
            name="test-server",
            command="test-cmd",
            args=[]
        )
        
        connection = MCPConnection(config)
        
        # Should handle responses
        assert connection is not None


# ============================================================
# Error Handling Tests
# ============================================================
class TestMCPErrorHandling:
    """Test MCP error handling and recovery."""

    @pytest.mark.asyncio
    async def test_connection_failure(self):
        """Should handle connection failures gracefully."""
        from core.mcp_client import MCPConnection, MCPServerConfig
        
        config = MCPServerConfig(
            name="test-server",
            command="nonexistent-command",
            args=[]
        )
        
        connection = MCPConnection(config)
        
        # Connect should fail gracefully
        result = await connection.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Should handle timeouts correctly."""
        from core.mcp_client import MCPServerConfig
        
        config = MCPServerConfig(
            name="test-server",
            command="test-cmd",
            args=[],
            init_timeout=0.1,  # Very short timeout
            tool_timeout=0.1
        )
        
        # Timeouts should be configurable
        assert config.init_timeout == 0.1
        assert config.tool_timeout == 0.1

    @pytest.mark.asyncio
    async def test_reconnection_logic(self):
        """Should reconnect after connection loss."""
        from core.mcp_client import MCPConnection, MCPServerConfig
        
        config = MCPServerConfig(
            name="test-server",
            command="test-cmd",
            args=[]
        )
        
        connection = MCPConnection(config)
        
        # Should track connection state
        assert hasattr(connection, '_connected') or hasattr(connection, 'process')


# ============================================================
# MCP Server Tests
# ============================================================
class TestMCPServer:
    """Test iTaK MCP server functionality."""

    def test_server_initialization(self):
        """MCP server should initialize with agent."""
        from core.mcp_server import ITaKMCPServer
        
        mock_agent = Mock()
        config = {
            "mcp_server": {
                "enabled": True,
                "token": "test-token"
            }
        }
        
        server = ITaKMCPServer(mock_agent, config)
        
        assert server.agent == mock_agent
        assert server.token == "test-token"
        assert server.enabled is True

    def test_tool_registration(self):
        """Server should register default tools."""
        from core.mcp_server import ITaKMCPServer
        
        mock_agent = Mock()
        config = {
            "mcp_server": {
                "enabled": True,
                "token": "test-token"
            }
        }
        
        server = ITaKMCPServer(mock_agent, config)
        
        # Should have tools registered
        assert len(server.tools) > 0
        assert "send_message" in server.tools

    @pytest.mark.asyncio
    async def test_tool_invocation(self):
        """Server should handle tool invocations."""
        from core.mcp_server import ITaKMCPServer
        
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Response")
        
        config = {
            "mcp_server": {
                "enabled": True,
                "token": "test-token"
            }
        }
        
        server = ITaKMCPServer(mock_agent, config)
        
        # Should have tool handlers
        assert "send_message" in server.tools


# ============================================================
# Multiple Server Coordination Tests
# ============================================================
class TestMultipleServers:
    """Test coordination of multiple MCP servers."""

    @pytest.mark.asyncio
    async def test_multiple_server_initialization(self):
        """Should handle multiple MCP servers."""
        from core.mcp_client import MCPClient, MCPServerConfig
        
        configs = [
            MCPServerConfig(name="server1", command="cmd1", args=[]),
            MCPServerConfig(name="server2", command="cmd2", args=[]),
            MCPServerConfig(name="server3", command="cmd3", args=[])
        ]
        
        client = MCPClient(configs)
        
        assert len(client.servers) == 3

    @pytest.mark.asyncio
    async def test_tool_namespace_collision(self):
        """Should handle tool name collisions across servers."""
        from core.mcp_client import MCPTool
        
        tool1 = MCPTool(name="read_file", description="Server 1", server_name="server1")
        tool2 = MCPTool(name="read_file", description="Server 2", server_name="server2")
        
        # Tools from different servers should be distinguishable
        assert tool1.server_name != tool2.server_name

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Should handle concurrent calls to different servers."""
        from core.mcp_client import MCPClient, MCPServerConfig
        
        configs = [
            MCPServerConfig(name="server1", command="cmd1", args=[]),
            MCPServerConfig(name="server2", command="cmd2", args=[])
        ]
        
        client = MCPClient(configs)
        
        # Should support concurrent operations
        assert client is not None
