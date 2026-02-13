"""
iTaK MCP Client — Connect to external MCP tool servers.

§20 of the gameplan — iTaK can use any MCP server (filesystem,
GitHub, postgres, browser, etc.) by managing stdio-based subprocess
connections and auto-discovering provided tools.

Based on Agent Zero's MCP handler pattern but simplified for iTaK.
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from core.agent import Agent


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""
    name: str
    command: str                         # e.g. "npx", "python"
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    init_timeout: float = 10.0
    tool_timeout: float = 120.0


@dataclass
class MCPTool:
    """A tool discovered from an MCP server."""
    name: str
    description: str = ""
    input_schema: dict = field(default_factory=dict)
    server_name: str = ""


class MCPConnection:
    """A live connection to a single MCP server via stdio."""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.tools: list[MCPTool] = []
        self._request_id = 0
        self._connected = False

    async def connect(self) -> bool:
        """Start the MCP server subprocess and initialize."""
        env = {**os.environ, **self.config.env}

        try:
            self.process = await asyncio.create_subprocess_exec(
                self.config.command, *self.config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
        except FileNotFoundError:
            return False
        except Exception:
            return False

        # Send initialize request
        try:
            init_response = await asyncio.wait_for(
                self._send_request("initialize", {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "iTaK",
                        "version": "0.5.0",
                    },
                }),
                timeout=self.config.init_timeout,
            )
            if init_response and "result" in init_response:
                # Send initialized notification
                await self._send_notification("notifications/initialized", {})
                self._connected = True
                # Discover tools
                await self._discover_tools()
                return True
        except asyncio.TimeoutError:
            await self.disconnect()
        except Exception:
            await self.disconnect()

        return False

    async def disconnect(self):
        """Shut down the MCP server process."""
        self._connected = False
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

    async def _send_request(self, method: str, params: dict) -> Optional[dict]:
        """Send a JSON-RPC request and wait for a response."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            return None

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        msg = json.dumps(request) + "\n"
        self.process.stdin.write(msg.encode())
        await self.process.stdin.drain()

        # Read response line
        line = await self.process.stdout.readline()
        if not line:
            return None

        try:
            return json.loads(line.decode())
        except json.JSONDecodeError:
            return None

    async def _send_notification(self, method: str, params: dict):
        """Send a JSON-RPC notification (no response expected)."""
        if not self.process or not self.process.stdin:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        msg = json.dumps(notification) + "\n"
        self.process.stdin.write(msg.encode())
        await self.process.stdin.drain()

    async def _discover_tools(self):
        """Ask the server what tools it provides."""
        response = await asyncio.wait_for(
            self._send_request("tools/list", {}),
            timeout=self.config.init_timeout,
        )
        if response and "result" in response:
            tools_data = response["result"].get("tools", [])
            self.tools = [
                MCPTool(
                    name=t.get("name", ""),
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {}),
                    server_name=self.config.name,
                )
                for t in tools_data
            ]

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool on this MCP server."""
        if not self._connected:
            return {"error": "Not connected"}

        try:
            response = await asyncio.wait_for(
                self._send_request("tools/call", {
                    "name": tool_name,
                    "arguments": arguments,
                }),
                timeout=self.config.tool_timeout,
            )
            if response and "result" in response:
                return response["result"]
            elif response and "error" in response:
                return {"error": response["error"]}
            return {"error": "No response from MCP server"}
        except asyncio.TimeoutError:
            return {"error": f"Tool call timed out after {self.config.tool_timeout}s"}
        except Exception as e:
            return {"error": str(e)}

    @property
    def is_connected(self) -> bool:
        return self._connected


# ---------------------------------------------------------------------------
# MCP Client Manager
# ---------------------------------------------------------------------------

class MCPClient:
    """Manages multiple MCP server connections and provides
    a unified tool discovery interface.

    Usage:
        client = MCPClient(agent)
        await client.connect_all()        # In agent.startup()
        tools = client.list_tools()       # Get all MCP tools
        result = await client.call_tool("server::tool", {...})
        await client.disconnect_all()     # In agent.shutdown()
    """

    def __init__(self, agent: Optional["Agent"] = None):
        self.agent = agent
        self.connections: dict[str, MCPConnection] = {}
        self._configs: list[MCPServerConfig] = []

    def load_config(self, mcp_config: dict):
        """Load MCP server configurations from config.json.

        Expected format:
        {
            "mcp_servers": {
                "mcpServers": {
                    "server_name": {
                        "command": "npx",
                        "args": [...],
                        "env": {...}
                    }
                }
            }
        }
        """
        servers = mcp_config.get("mcp_servers", {}).get("mcpServers", {})
        for name, cfg in servers.items():
            # Resolve secret placeholders in env
            env = {}
            for k, v in cfg.get("env", {}).items():
                if self.agent and hasattr(self.agent, "secrets") and self.agent.secrets:
                    v = self.agent.secrets.resolve(v)
                env[k] = v

            self._configs.append(MCPServerConfig(
                name=name,
                command=cfg.get("command", ""),
                args=cfg.get("args", []),
                env=env,
                init_timeout=mcp_config.get("mcp_client_init_timeout", 10),
                tool_timeout=mcp_config.get("mcp_client_tool_timeout", 120),
            ))

    async def connect_all(self) -> dict[str, bool]:
        """Connect to all configured MCP servers. Returns status per server."""
        results = {}
        for config in self._configs:
            conn = MCPConnection(config)
            success = await conn.connect()
            results[config.name] = success
            if success:
                self.connections[config.name] = conn
        return results

    async def disconnect_all(self):
        """Disconnect from all MCP servers."""
        for conn in self.connections.values():
            await conn.disconnect()
        self.connections.clear()

    def list_tools(self) -> list[MCPTool]:
        """List all tools from all connected MCP servers."""
        tools = []
        for conn in self.connections.values():
            tools.extend(conn.tools)
        return tools

    def get_tool(self, full_name: str) -> Optional[MCPTool]:
        """Get an MCP tool by 'server::tool_name' format."""
        parts = full_name.split("::", 1)
        if len(parts) == 2:
            server_name, tool_name = parts
            conn = self.connections.get(server_name)
            if conn:
                for tool in conn.tools:
                    if tool.name == tool_name:
                        return tool
        else:
            # Search all servers
            for conn in self.connections.values():
                for tool in conn.tools:
                    if tool.name == full_name:
                        return tool
        return None

    async def call_tool(self, full_name: str, arguments: dict) -> dict:
        """Call an MCP tool. Try 'server::tool' format first, then search."""
        parts = full_name.split("::", 1)
        if len(parts) == 2:
            server_name, tool_name = parts
            conn = self.connections.get(server_name)
            if conn:
                return await conn.call_tool(tool_name, arguments)
            return {"error": f"MCP server '{server_name}' not connected"}

        # Search through all connections
        for conn in self.connections.values():
            for tool in conn.tools:
                if tool.name == full_name:
                    return await conn.call_tool(full_name, arguments)

        return {"error": f"MCP tool '{full_name}' not found"}

    def get_status(self) -> dict:
        """Get MCP client status for dashboard."""
        return {
            "configured": len(self._configs),
            "connected": len(self.connections),
            "total_tools": sum(len(c.tools) for c in self.connections.values()),
            "servers": {
                name: {
                    "connected": conn.is_connected,
                    "tools": [t.name for t in conn.tools],
                }
                for name, conn in self.connections.items()
            },
        }
