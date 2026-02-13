"""
iTaK WebUI — FastAPI backend for the monitoring dashboard.
Provides REST API + WebSocket for real-time agent monitoring.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.agent import Agent

logger = logging.getLogger(__name__)


def create_app(agent: "Agent"):
    """Create the FastAPI application."""
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="iTaK Dashboard", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # WebSocket connections for real-time updates
    ws_clients: list[WebSocket] = []

    # ——— REST Endpoints ———

    @app.get("/api/health")
    async def health():
        """Health check endpoint."""
        health_data = {"status": "ok", "timestamp": time.time()}
        if hasattr(agent, "heartbeat") and agent.heartbeat:
            health_data["heartbeat"] = await agent.heartbeat.check_health()
        return health_data

    @app.get("/api/stats")
    async def stats():
        """Get agent statistics."""
        data = {
            "uptime_seconds": time.time() - getattr(agent, "_start_time", time.time()),
            "total_iterations": getattr(agent, "total_iterations", 0),
            "tools_loaded": len(getattr(agent, "tools", [])),
        }

        # Memory stats
        if hasattr(agent, "memory") and agent.memory:
            data["memory"] = await agent.memory.get_stats()

        # Rate limiter stats
        if hasattr(agent, "rate_limiter") and agent.rate_limiter:
            data["rate_limiter"] = agent.rate_limiter.get_status()

        # Sub-agent stats
        if hasattr(agent, "sub_agents") and agent.sub_agents:
            data["sub_agents"] = agent.sub_agents.get_status()

        return data

    @app.get("/api/logs")
    async def logs(search: str = "", limit: int = 50, offset: int = 0):
        """Query agent logs."""
        if hasattr(agent, "logger"):
            results = agent.logger.query(
                search=search if search else None,
                limit=limit,
                offset=offset,
            )
            return {"logs": results, "total": len(results)}
        return {"logs": [], "total": 0}

    @app.get("/api/memory/search")
    async def memory_search(query: str, category: str = "", limit: int = 10):
        """Search agent memory."""
        if hasattr(agent, "memory") and agent.memory:
            results = await agent.memory.search(
                query=query,
                category=category if category else None,
                limit=limit,
            )
            return {"results": results, "count": len(results)}
        return {"results": [], "count": 0}

    @app.get("/api/memory/stats")
    async def memory_stats():
        """Get memory layer statistics."""
        if hasattr(agent, "memory") and agent.memory:
            return await agent.memory.get_stats()
        return {}

    @app.get("/api/tools")
    async def list_tools():
        """List all loaded tools."""
        tools = []
        for t in getattr(agent, "tools", []):
            tools.append({
                "name": t.name,
                "description": getattr(t, "description", ""),
            })
        return {"tools": tools}

    @app.get("/api/heartbeat/history")
    async def heartbeat_history(limit: int = 20):
        """Get heartbeat check history."""
        if hasattr(agent, "heartbeat") and agent.heartbeat:
            return {"history": agent.heartbeat.get_history(limit)}
        return {"history": []}

    @app.get("/api/heartbeat/uptime")
    async def heartbeat_uptime():
        """Get uptime statistics."""
        if hasattr(agent, "heartbeat") and agent.heartbeat:
            return agent.heartbeat.get_uptime()
        return {}

    @app.get("/api/config")
    async def get_config():
        """Get safe-to-share config (no secrets)."""
        config = dict(agent.config) if hasattr(agent, "config") else {}
        # Redact sensitive fields
        safe = {}
        for k, v in config.items():
            if isinstance(v, dict):
                safe[k] = {sk: "***" if "key" in sk.lower() or "token" in sk.lower() or "password" in sk.lower() else sv for sk, sv in v.items()}
            elif isinstance(v, str) and any(s in k.lower() for s in ["key", "token", "password", "secret"]):
                safe[k] = "***"
            else:
                safe[k] = v
        return safe

    @app.post("/api/chat")
    async def chat(payload: dict):
        """Send a message to the agent via WebUI."""
        message = payload.get("message", "")
        if not message:
            return JSONResponse({"error": "No message provided"}, status_code=400)

        # Run agent
        try:
            response = await agent.monologue(message)
            return {"response": response}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.post("/api/security/scan")
    async def security_scan(payload: dict):
        """Run a security scan on provided code."""
        from security.scanner import SecurityScanner
        scanner = SecurityScanner()
        code = payload.get("code", "")
        result = scanner.scan_code(code, source="webui")
        return result

    # ——— Mission Control Endpoints ———

    @app.get("/api/tasks")
    async def list_tasks(status: str = "", limit: int = 50):
        """List all tasks, optionally filtered by status."""
        if hasattr(agent, "task_board") and agent.task_board:
            tasks = agent.task_board.list_all(
                status=status if status else None, limit=limit,
            )
            return {"tasks": [t.to_dict() for t in tasks]}
        return {"tasks": []}

    @app.get("/api/tasks/{task_id}")
    async def get_task(task_id: str):
        """Get a single task by ID."""
        if hasattr(agent, "task_board") and agent.task_board:
            task = agent.task_board.get(task_id)
            if task:
                return task.to_dict()
            return JSONResponse({"error": "Task not found"}, status_code=404)
        return JSONResponse({"error": "Task board not available"}, status_code=503)

    @app.post("/api/tasks")
    async def create_task(payload: dict):
        """Create a new task from the dashboard."""
        if hasattr(agent, "task_board") and agent.task_board:
            task = agent.task_board.create(
                title=payload.get("title", "Untitled"),
                description=payload.get("description", ""),
                priority=payload.get("priority", "medium"),
                source="dashboard",
            )
            return task.to_dict()
        return JSONResponse({"error": "Task board not available"}, status_code=503)

    @app.post("/api/tasks/{task_id}/complete")
    async def complete_task(task_id: str):
        """Mark a task as complete."""
        if hasattr(agent, "task_board") and agent.task_board:
            task = agent.task_board.complete(task_id)
            if task:
                return task.to_dict()
            return JSONResponse({"error": "Task not found"}, status_code=404)
        return JSONResponse({"error": "Task board not available"}, status_code=503)

    @app.post("/api/tasks/{task_id}/fail")
    async def fail_task(task_id: str, payload: dict = None):
        """Mark a task as failed."""
        if hasattr(agent, "task_board") and agent.task_board:
            error = (payload or {}).get("error", "")
            task = agent.task_board.fail(task_id, error=error)
            if task:
                return task.to_dict()
            return JSONResponse({"error": "Task not found"}, status_code=404)
        return JSONResponse({"error": "Task board not available"}, status_code=503)

    @app.delete("/api/tasks/{task_id}")
    async def delete_task(task_id: str):
        """Delete a task."""
        if hasattr(agent, "task_board") and agent.task_board:
            deleted = agent.task_board.delete(task_id)
            return {"deleted": deleted}
        return JSONResponse({"error": "Task board not available"}, status_code=503)

    @app.get("/api/tasks/board")
    async def task_board_view():
        """Get formatted Kanban board view."""
        if hasattr(agent, "task_board") and agent.task_board:
            return {
                "board": agent.task_board.format_board(),
                "stats": agent.task_board.get_stats(),
            }
        return {"board": "", "stats": {}}

    # ——— Phase 5 Status Endpoints ———

    @app.get("/api/mcp/status")
    async def mcp_status():
        """Get MCP client status."""
        if hasattr(agent, "mcp_client") and agent.mcp_client:
            return agent.mcp_client.get_status()
        return {"configured": 0, "connected": 0, "total_tools": 0, "servers": {}}

    @app.get("/api/self-heal/stats")
    async def self_heal_stats():
        """Get self-healing engine statistics."""
        if hasattr(agent, "self_heal") and agent.self_heal:
            return agent.self_heal.get_stats()
        return {"session_retries": 0, "total_errors": 0}

    @app.get("/api/subsystems")
    async def subsystem_status():
        """Get status of all subsystems."""
        if hasattr(agent, "get_subsystem_status"):
            return agent.get_subsystem_status()
        return {}

    # ——— Phase 6: Webhook, Swarm, Users, Presence, MCP Server ———

    @app.post("/api/webhook")
    async def webhook_inbound(request: Request):
        """Receive inbound webhook from n8n/Zapier/external."""
        if not agent.webhooks:
            return JSONResponse({"error": "Webhooks not enabled"}, status_code=503)

        # Auth check
        secret = request.headers.get("X-Webhook-Secret", "")
        if not agent.webhooks.verify_secret(secret):
            return JSONResponse({"error": "Invalid webhook secret"}, status_code=401)

        try:
            data = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)

        payload = agent.webhooks.parse_inbound(data)
        result = await agent.webhooks.process_inbound(payload)
        return result

    @app.get("/api/webhooks/stats")
    async def webhook_stats():
        """Get webhook statistics."""
        if agent.webhooks:
            return agent.webhooks.get_stats()
        return {"inbound_received": 0, "outbound_fired": 0, "targets": {}}

    @app.get("/api/swarm/stats")
    async def swarm_stats():
        """Get swarm coordinator stats."""
        if agent.swarm:
            return agent.swarm.get_stats()
        return {"profiles_loaded": 0, "total_swarms": 0}

    @app.get("/api/swarm/profiles")
    async def swarm_profiles():
        """List available agent profiles."""
        if agent.swarm:
            return {"profiles": agent.swarm.list_profiles()}
        return {"profiles": []}

    @app.get("/api/users")
    async def list_users():
        """List all registered users."""
        if agent.user_registry:
            return {"users": agent.user_registry.list_users()}
        return {"users": []}

    @app.post("/api/users")
    async def add_user(payload: dict):
        """Add a new user."""
        if not agent.user_registry:
            return JSONResponse({"error": "User registry not available"}, status_code=503)
        try:
            user = agent.user_registry.add_user(
                user_id=payload["id"],
                name=payload.get("name", payload["id"]),
                role=payload.get("role", "user"),
                platforms=payload.get("platforms", {}),
                rate_limit=payload.get("rate_limit"),
            )
            return {"user": {"id": user.id, "name": user.name, "role": user.role}}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=400)

    @app.delete("/api/users/{user_id}")
    async def remove_user(user_id: str):
        """Remove a user."""
        if not agent.user_registry:
            return JSONResponse({"error": "User registry not available"}, status_code=503)
        success = agent.user_registry.remove_user(user_id)
        return {"removed": success}

    @app.get("/api/users/stats")
    async def user_stats():
        """Get user registry stats."""
        if agent.user_registry:
            return agent.user_registry.get_stats()
        return {"total_users": 0}

    @app.get("/api/presence")
    async def presence_status():
        """Get current agent presence status."""
        if agent.presence:
            return agent.presence.get_status()
        return {"state": "unknown"}

    @app.get("/api/media/stats")
    async def media_stats():
        """Get media pipeline statistics."""
        if agent.media:
            return agent.media.get_stats()
        return {"inbound_processed": 0, "outbound_sent": 0}

    @app.get("/api/mcp-server/health")
    async def mcp_server_health():
        """Get MCP server health."""
        if agent.mcp_server and agent.mcp_server.enabled:
            return {"status": "ok", "tools": len(agent.mcp_server.tools)}
        return {"status": "disabled"}

    # Mount MCP Server routes if enabled
    if hasattr(agent, "mcp_server") and agent.mcp_server and agent.mcp_server.enabled:
        agent.mcp_server.mount_routes(app)

    # ——— WebSocket for real-time updates ———

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await ws.accept()
        ws_clients.append(ws)
        try:
            while True:
                data = await ws.receive_text()
                # Handle incoming WebSocket messages
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await ws.send_json({"type": "pong", "timestamp": time.time()})
                    elif msg.get("type") == "chat":
                        response = await agent.monologue(msg.get("message", ""))
                        await ws.send_json({"type": "response", "content": response})
                except json.JSONDecodeError:
                    pass
        except WebSocketDisconnect:
            ws_clients.remove(ws)

    # Register progress callback to broadcast via WebSocket
    async def ws_broadcast(event_type: str, data: dict):
        for ws in ws_clients[:]:
            try:
                await ws.send_json({
                    "type": "progress",
                    "event": event_type,
                    "data": data,
                    "timestamp": time.time(),
                })
            except Exception:
                ws_clients.remove(ws)

    if hasattr(agent, "progress") and agent.progress:
        agent.progress.register_callback(ws_broadcast)

    # ——— Serve Frontend ———

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True))

    return app


async def start_webui(agent: "Agent", host: str = "0.0.0.0", port: int = 48920):
    """Start the WebUI server."""
    import uvicorn

    app = create_app(agent)
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    logger.info(f"iTaK WebUI starting on http://{host}:{port}")
    await server.serve()
