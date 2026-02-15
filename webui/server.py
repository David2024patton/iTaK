"""
iTaK WebUI - FastAPI backend for the monitoring dashboard.
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

    # Extract WebUI config early (used by CORS, auth, etc.)
    webui_config = agent.config.get("webui", {})

    # CORS: locked to localhost by default, configurable for tunnel exposure
    cors_origins = webui_config.get("cors_origins", [
        "http://localhost:*",
        "http://127.0.0.1:*",
        "https://localhost:*",
    ])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Auth middleware (OpenClaw-inspired) ────────────────────
    # Protects all API endpoints with a Bearer token.
    # Token is set via config.json webui.auth_token or auto-generated.

    auth_token = webui_config.get("auth_token", "")

    # Auto-generate token if not configured
    if not auth_token:
        import secrets as _secrets
        auth_token = _secrets.token_hex(24)
        logger.warning(
            f"WebUI auth token auto-generated: {auth_token}\n"
            f"Add this to config.json: \"webui\": {{ \"auth_token\": \"{auth_token}\" }}"
        )

    # Exempt paths that don't need auth
    AUTH_EXEMPT = {"/api/health", "/docs", "/openapi.json"}

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        path = request.url.path

        # Skip auth for exempt paths and static files
        if path in AUTH_EXEMPT or not path.startswith("/api/"):
            return await call_next(request)

        # Check auth-failure lockout
        client_ip = request.client.host if request.client else "unknown"
        if hasattr(agent, "rate_limiter") and agent.rate_limiter:
            locked, retry_after = agent.rate_limiter.check_auth_lockout(client_ip)
            if locked:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Too many auth failures. Try again later."},
                    headers={"Retry-After": str(retry_after)},
                )

        # Validate Bearer token
        import hmac
        auth_header = request.headers.get("Authorization", "")
        provided = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

        if not provided or not hmac.compare_digest(
            provided.encode("utf-8"),
            auth_token.encode("utf-8"),
        ):
            # Record auth failure for lockout tracking
            if hasattr(agent, "rate_limiter") and agent.rate_limiter:
                agent.rate_limiter.record_auth_failure(client_ip)
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or missing auth token"},
            )

        # Auth success - clear lockout history
        if hasattr(agent, "rate_limiter") and agent.rate_limiter:
            agent.rate_limiter.record_auth_success(client_ip)

        return await call_next(request)

    # WebSocket connections for real-time updates
    ws_clients: list[WebSocket] = []

    # --- REST Endpoints ---

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
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        search = search[:500] if search else ""
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
        limit = max(1, min(limit, 100))
        query = query[:1000]
        category = category[:100] if category else ""
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

    # --- Skills, Tools, and MCPs Management ---

    @app.get("/api/resources/skills")
    async def list_skills():
        """List all skill files."""
        skills_dir = Path(__file__).parent.parent / "skills"
        skills = []
        if skills_dir.exists():
            for skill_file in skills_dir.glob("*.md"):
                if skill_file.name == "SKILL.md":
                    continue
                try:
                    content = skill_file.read_text(encoding="utf-8")
                    # Extract first line as title
                    lines = content.split("\n")
                    title = lines[0].replace("#", "").strip() if lines else skill_file.stem
                    skills.append({
                        "name": skill_file.stem,
                        "filename": skill_file.name,
                        "title": title,
                        "size": skill_file.stat().st_size,
                    })
                except Exception:
                    pass
        return {"skills": skills}

    @app.get("/api/resources/skills/{skill_name}")
    async def get_skill(skill_name: str):
        """Get a specific skill file content."""
        skills_dir = Path(__file__).parent.parent / "skills"
        skill_file = skills_dir / f"{skill_name}.md"
        if not skill_file.exists():
            return JSONResponse({"error": "Skill not found"}, status_code=404)
        try:
            content = skill_file.read_text(encoding="utf-8")
            return {"name": skill_name, "content": content}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.post("/api/resources/skills")
    async def create_skill(payload: dict):
        """Create a new skill file."""
        name = payload.get("name", "").strip()
        content = payload.get("content", "")
        if not name:
            return JSONResponse({"error": "Skill name is required"}, status_code=400)
        # Sanitize filename
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        skills_dir = Path(__file__).parent.parent / "skills"
        skill_file = skills_dir / f"{safe_name}.md"
        if skill_file.exists():
            return JSONResponse({"error": "Skill already exists"}, status_code=400)
        try:
            skill_file.write_text(content, encoding="utf-8")
            return {"name": safe_name, "message": "Skill created successfully"}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.put("/api/resources/skills/{skill_name}")
    async def update_skill(skill_name: str, payload: dict):
        """Update an existing skill file."""
        content = payload.get("content", "")
        skills_dir = Path(__file__).parent.parent / "skills"
        skill_file = skills_dir / f"{skill_name}.md"
        if not skill_file.exists():
            return JSONResponse({"error": "Skill not found"}, status_code=404)
        try:
            skill_file.write_text(content, encoding="utf-8")
            return {"name": skill_name, "message": "Skill updated successfully"}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.delete("/api/resources/skills/{skill_name}")
    async def delete_skill(skill_name: str):
        """Delete a skill file."""
        skills_dir = Path(__file__).parent.parent / "skills"
        skill_file = skills_dir / f"{skill_name}.md"
        if not skill_file.exists():
            return JSONResponse({"error": "Skill not found"}, status_code=404)
        if skill_name == "SKILL":
            return JSONResponse({"error": "Cannot delete template"}, status_code=400)
        try:
            skill_file.unlink()
            return {"message": "Skill deleted successfully"}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/api/resources/tools")
    async def list_tool_files():
        """List all tool files (Python + prompts)."""
        tools_dir = Path(__file__).parent.parent / "tools"
        prompts_dir = Path(__file__).parent.parent / "prompts"
        tools = []
        if tools_dir.exists():
            for tool_file in tools_dir.glob("*.py"):
                if tool_file.name in ["__init__.py", "base.py", "response.py", "TOOL_TEMPLATE.md"]:
                    continue
                tool_name = tool_file.stem
                # Check if corresponding prompt exists
                prompt_file = prompts_dir / f"agent.system.tool.{tool_name}.md"
                has_prompt = prompt_file.exists() if prompts_dir.exists() else False
                try:
                    content = tool_file.read_text(encoding="utf-8")
                    # Extract description from class docstring
                    import re
                    desc_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
                    description = desc_match.group(1).strip().split("\n")[0] if desc_match else ""
                    tools.append({
                        "name": tool_name,
                        "filename": tool_file.name,
                        "description": description[:100],
                        "has_prompt": has_prompt,
                        "size": tool_file.stat().st_size,
                    })
                except Exception:
                    pass
        return {"tools": tools}

    @app.get("/api/resources/tools/{tool_name}")
    async def get_tool(tool_name: str):
        """Get a specific tool file and its prompt."""
        tools_dir = Path(__file__).parent.parent / "tools"
        prompts_dir = Path(__file__).parent.parent / "prompts"
        tool_file = tools_dir / f"{tool_name}.py"
        if not tool_file.exists():
            return JSONResponse({"error": "Tool not found"}, status_code=404)
        try:
            code = tool_file.read_text(encoding="utf-8")
            prompt = ""
            prompt_file = prompts_dir / f"agent.system.tool.{tool_name}.md"
            if prompt_file.exists():
                prompt = prompt_file.read_text(encoding="utf-8")
            return {"name": tool_name, "code": code, "prompt": prompt}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.post("/api/resources/tools")
    async def create_tool(payload: dict):
        """Create a new tool file."""
        name = payload.get("name", "").strip()
        code = payload.get("code", "")
        prompt = payload.get("prompt", "")
        if not name:
            return JSONResponse({"error": "Tool name is required"}, status_code=400)
        # Sanitize filename
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        tools_dir = Path(__file__).parent.parent / "tools"
        prompts_dir = Path(__file__).parent.parent / "prompts"
        tool_file = tools_dir / f"{safe_name}.py"
        if tool_file.exists():
            return JSONResponse({"error": "Tool already exists"}, status_code=400)
        try:
            tool_file.write_text(code, encoding="utf-8")
            if prompt:
                prompt_file = prompts_dir / f"agent.system.tool.{safe_name}.md"
                prompt_file.write_text(prompt, encoding="utf-8")
            return {"name": safe_name, "message": "Tool created successfully"}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.put("/api/resources/tools/{tool_name}")
    async def update_tool(tool_name: str, payload: dict):
        """Update an existing tool file."""
        code = payload.get("code", "")
        prompt = payload.get("prompt", "")
        tools_dir = Path(__file__).parent.parent / "tools"
        prompts_dir = Path(__file__).parent.parent / "prompts"
        tool_file = tools_dir / f"{tool_name}.py"
        if not tool_file.exists():
            return JSONResponse({"error": "Tool not found"}, status_code=404)
        try:
            if code:
                tool_file.write_text(code, encoding="utf-8")
            if prompt:
                prompt_file = prompts_dir / f"agent.system.tool.{tool_name}.md"
                prompt_file.write_text(prompt, encoding="utf-8")
            return {"name": tool_name, "message": "Tool updated successfully"}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.delete("/api/resources/tools/{tool_name}")
    async def delete_tool(tool_name: str):
        """Delete a tool file and its prompt."""
        tools_dir = Path(__file__).parent.parent / "tools"
        prompts_dir = Path(__file__).parent.parent / "prompts"
        tool_file = tools_dir / f"{tool_name}.py"
        if not tool_file.exists():
            return JSONResponse({"error": "Tool not found"}, status_code=404)
        if tool_name in ["base", "response"]:
            return JSONResponse({"error": "Cannot delete core tools"}, status_code=400)
        try:
            tool_file.unlink()
            # Also delete prompt if exists
            prompt_file = prompts_dir / f"agent.system.tool.{tool_name}.md"
            if prompt_file.exists():
                prompt_file.unlink()
            return {"message": "Tool deleted successfully"}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/api/resources/mcps")
    async def list_mcps():
        """List configured MCP servers and their tools."""
        mcps = []
        if hasattr(agent, "mcp_client") and agent.mcp_client:
            status = agent.mcp_client.get_status()
            for server_name, server_info in status.get("servers", {}).items():
                mcps.append({
                    "name": server_name,
                    "connected": server_info.get("connected", False),
                    "tools": server_info.get("tools", []),
                    "tool_count": len(server_info.get("tools", [])),
                })
        return {"mcps": mcps}

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

    _SENSITIVE_KEYS = {"key", "token", "password", "secret"}

    def _is_sensitive_key(name: str) -> bool:
        return any(s in name.lower() for s in _SENSITIVE_KEYS)

    def _redact_dict(d: dict) -> dict:
        safe = {}
        for k, v in d.items():
            if isinstance(v, dict):
                safe[k] = _redact_dict(v)
            elif isinstance(v, str) and _is_sensitive_key(k):
                safe[k] = "***"
            else:
                safe[k] = v
        return safe

    @app.get("/api/config")
    async def get_config():
        """Get safe-to-share config (no secrets)."""
        config = dict(agent.config) if hasattr(agent, "config") else {}
        return _redact_dict(config)

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

    # --- Mission Control Endpoints ---

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

    @app.patch("/api/tasks/{task_id}")
    async def update_task_status(task_id: str, payload: dict):
        """Update a task's status (for Kanban drag-and-drop)."""
        if hasattr(agent, "task_board") and agent.task_board:
            new_status = payload.get("status")
            valid = {"inbox", "in_progress", "review", "done", "failed"}
            if new_status not in valid:
                return JSONResponse(
                    {"error": f"Invalid status. Must be one of: {valid}"},
                    status_code=400,
                )
            # Use built-in transitions where possible
            if new_status == "in_progress":
                task = agent.task_board.start(task_id)
                if not task:
                    # Force status if not in inbox
                    task = agent.task_board.get(task_id)
                    if task:
                        task.status = "in_progress"
                        task.started_at = task.started_at or __import__("time").time()
                        agent.task_board.update(task)
            elif new_status == "review":
                task = agent.task_board.set_review(task_id)
            elif new_status == "done":
                task = agent.task_board.complete(task_id)
            elif new_status == "failed":
                task = agent.task_board.fail(task_id)
            else:
                task = agent.task_board.get(task_id)
                if task:
                    task.status = new_status
                    agent.task_board.update(task)

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

    # --- Phase 5 Status Endpoints ---

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

    # --- Phase 6: Webhook, Swarm, Users, Presence, MCP Server ---

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

    # --- WebSocket for real-time updates ---

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        # Validate token on WebSocket handshake (query param: ?token=xxx)
        import hmac
        ws_token = ws.query_params.get("token", "")
        if not ws_token or not hmac.compare_digest(
            ws_token.encode("utf-8"),
            auth_token.encode("utf-8"),
        ):
            await ws.close(code=4001, reason="Invalid auth token")
            return

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

    # --- Serve Frontend ---

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
