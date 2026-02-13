"""
iTaK MCP Server - Expose iTaK as an MCP Tool Server.

Other agents, IDEs (Cursor, VS Code), and automation platforms (n8n)
can call iTaK tools over SSE transport via the Model Context Protocol.

Gameplan §20 - "Connect to Everything"
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("itak.mcp_server")


@dataclass
class ExposedTool:
    """A tool exposed via MCP server."""
    name: str
    description: str
    parameters: dict  # JSON Schema
    handler: Any  # async callable


class ITaKMCPServer:
    """
    Expose iTaK as an MCP-compatible tool server using SSE transport.

    Tools exposed:
      - send_message: Send a message to iTaK and get a response
      - search_memory: Search agent's memory
      - list_tasks: List Mission Control tasks
      - get_task: Get a specific task by ID
      - create_task: Create a new task on the board
      - get_status: Get agent subsystem status

    Auth: Bearer token from config.json → mcp_server.token
    Transport: SSE on /mcp endpoint
    """

    def __init__(self, agent, config: dict | None = None):
        self.agent = agent
        self.config = config or {}
        self.token = self.config.get("mcp_server", {}).get("token", "")
        self.enabled = self.config.get("mcp_server", {}).get("enabled", False)
        self.tools: dict[str, ExposedTool] = {}
        self._running = False

        if self.enabled:
            self._register_default_tools()
            logger.info(f"MCP Server initialized with {len(self.tools)} tools")

    def _register_default_tools(self):
        """Register the default set of exposed tools."""

        self._register("send_message", 
            description="Send a message to iTaK and get a response.",
            parameters={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to send to the agent"
                    }
                },
                "required": ["message"]
            },
            handler=self._handle_send_message
        )

        self._register("search_memory",
            description="Search the agent's long-term memory.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for memory"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
            handler=self._handle_search_memory
        )

        self._register("list_tasks",
            description="List tasks from Mission Control task board.",
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status: inbox, in_progress, review, done, failed",
                        "default": ""
                    }
                }
            },
            handler=self._handle_list_tasks
        )

        self._register("get_task",
            description="Get a specific task by ID.",
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task ID"
                    }
                },
                "required": ["task_id"]
            },
            handler=self._handle_get_task
        )

        self._register("create_task",
            description="Create a new task on the Mission Control board.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Task description",
                        "default": ""
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority: low, medium, high, critical",
                        "default": "medium"
                    }
                },
                "required": ["title"]
            },
            handler=self._handle_create_task
        )

        self._register("get_status",
            description="Get agent subsystem status.",
            parameters={"type": "object", "properties": {}},
            handler=self._handle_get_status
        )

    def _register(self, name: str, description: str,
                  parameters: dict, handler):
        """Register an exposed tool."""
        self.tools[name] = ExposedTool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler
        )

    # ── Tool Handlers ──────────────────────────────────────────

    async def _handle_send_message(self, args: dict) -> str:
        """Process a message through the agent's monologue."""
        message = args.get("message", "")
        if not message:
            return json.dumps({"error": "message is required"})
        try:
            result = await self.agent.monologue(message)
            return json.dumps({"response": result})
        except Exception as e:
            logger.error(f"MCP send_message failed: {e}")
            return json.dumps({"error": str(e)})

    async def _handle_search_memory(self, args: dict) -> str:
        """Search agent memory."""
        query = args.get("query", "")
        limit = args.get("limit", 5)
        if not query:
            return json.dumps({"error": "query is required"})
        try:
            if hasattr(self.agent, 'memory') and self.agent.memory:
                results = await self.agent.memory.search(query, limit=limit)
                return json.dumps({"results": results})
            return json.dumps({"results": [], "note": "Memory not available"})
        except Exception as e:
            logger.error(f"MCP search_memory failed: {e}")
            return json.dumps({"error": str(e)})

    async def _handle_list_tasks(self, args: dict) -> str:
        """List tasks from the task board."""
        status_filter = args.get("status", "")
        try:
            if hasattr(self.agent, 'task_board') and self.agent.task_board:
                tasks = self.agent.task_board.list_tasks(
                    status=status_filter if status_filter else None
                )
                return json.dumps({"tasks": [
                    {"id": t.id, "title": t.title, "status": t.status,
                     "priority": t.priority}
                    for t in tasks
                ]})
            return json.dumps({"tasks": [], "note": "Task board not available"})
        except Exception as e:
            logger.error(f"MCP list_tasks failed: {e}")
            return json.dumps({"error": str(e)})

    async def _handle_get_task(self, args: dict) -> str:
        """Get a specific task."""
        task_id = args.get("task_id", "")
        if not task_id:
            return json.dumps({"error": "task_id is required"})
        try:
            if hasattr(self.agent, 'task_board') and self.agent.task_board:
                task = self.agent.task_board.get(task_id)
                if task:
                    return json.dumps({
                        "id": task.id, "title": task.title,
                        "status": task.status, "priority": task.priority,
                        "steps": task.steps, "deliverables": task.deliverables,
                        "created_at": task.created_at,
                    })
                return json.dumps({"error": f"Task {task_id} not found"})
            return json.dumps({"error": "Task board not available"})
        except Exception as e:
            logger.error(f"MCP get_task failed: {e}")
            return json.dumps({"error": str(e)})

    async def _handle_create_task(self, args: dict) -> str:
        """Create a new task."""
        title = args.get("title", "")
        if not title:
            return json.dumps({"error": "title is required"})
        try:
            if hasattr(self.agent, 'task_board') and self.agent.task_board:
                task = self.agent.task_board.create(
                    title=title,
                    description=args.get("description", ""),
                    priority=args.get("priority", "medium"),
                    source="mcp"
                )
                return json.dumps({
                    "task_id": task.id, "title": task.title,
                    "status": task.status, "priority": task.priority
                })
            return json.dumps({"error": "Task board not available"})
        except Exception as e:
            logger.error(f"MCP create_task failed: {e}")
            return json.dumps({"error": str(e)})

    async def _handle_get_status(self, args: dict) -> str:
        """Get agent subsystem status."""
        try:
            if hasattr(self.agent, 'get_subsystem_status'):
                status = self.agent.get_subsystem_status()
                return json.dumps(status)
            return json.dumps({"status": "running"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    # ── SSE Transport ──────────────────────────────────────────

    def get_tools_list(self) -> list[dict]:
        """Return MCP tools/list response."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.parameters
            }
            for tool in self.tools.values()
        ]

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Execute an MCP tool call and return result."""
        tool = self.tools.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}

        try:
            result = await tool.handler(arguments)
            return {"content": [{"type": "text", "text": result}]}
        except Exception as e:
            logger.error(f"MCP tool {name} failed: {e}")
            return {"error": str(e), "isError": True}

    def verify_token(self, provided_token: str) -> bool:
        """Verify Bearer token for auth."""
        if not self.token:
            return True  # No token configured = open access
        return provided_token == self.token

    def mount_routes(self, app):
        """
        Mount MCP SSE routes onto a FastAPI app.

        Endpoints:
          GET  /mcp/sse          - SSE connection
          POST /mcp/messages     - JSON-RPC message handler
          GET  /mcp/health       - Health check
        """
        from starlette.responses import JSONResponse

        @app.get("/mcp/health")
        async def mcp_health():
            return {"status": "ok", "tools": len(self.tools)}

        @app.post("/mcp/messages")
        async def mcp_messages(request):
            """Handle JSON-RPC 2.0 messages."""
            try:
                body = await request.json()
            except Exception:
                return JSONResponse(
                    {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None},
                    status_code=400
                )

            # Auth check
            auth_header = request.headers.get("authorization", "")
            if self.token:
                if not auth_header.startswith("Bearer "):
                    return JSONResponse(
                        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Unauthorized"}, "id": body.get("id")},
                        status_code=401
                    )
                if not self.verify_token(auth_header[7:]):
                    return JSONResponse(
                        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid token"}, "id": body.get("id")},
                        status_code=401
                    )

            method = body.get("method", "")
            params = body.get("params", {})
            msg_id = body.get("id")

            if method == "initialize":
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "iTaK MCP Server",
                            "version": "1.0.0"
                        }
                    }
                })

            elif method == "tools/list":
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"tools": self.get_tools_list()}
                })

            elif method == "tools/call":
                tool_name = params.get("name", "")
                tool_args = params.get("arguments", {})
                result = await self.call_tool(tool_name, tool_args)
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": result
                })

            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                })

        self._running = True
        logger.info(f"MCP Server routes mounted: /mcp/health, /mcp/messages ({len(self.tools)} tools)")
