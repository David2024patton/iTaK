"""
iTaK WebUI - FastAPI backend for the monitoring dashboard.
Provides REST API + WebSocket for real-time agent monitoring.
"""

import asyncio
import json
import logging
import secrets
import time
import uuid
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

    # --- Agent Zero compatibility state (poll-based mode) ---
    csrf_token = secrets.token_hex(16)
    runtime_id = "itak-webui"
    contexts: dict[str, dict] = {}
    context_counter = 0
    notifications: list[dict] = []
    notifications_guid = uuid.uuid4().hex
    notifications_version = 0
    sio_server = None
    sio_runtime_epoch = uuid.uuid4().hex
    sio_sequence = 0
    sio_sid_seqbase: dict[str, int] = {}

    compat_settings = {
        "chat_model_provider": "openai",
        "chat_model_name": "gpt-4o-mini",
        "chat_model_api_base": "",
        "chat_model_ctx_length": 128000,
        "chat_model_ctx_history": 0.7,
        "chat_model_vision": True,
        "chat_model_rl_requests": 60,
        "chat_model_rl_input": 1000000,
        "chat_model_rl_output": 1000000,
        "chat_model_kwargs": "{}",
        "util_model_provider": "openai",
        "util_model_name": "gpt-4o-mini",
        "util_model_api_base": "",
        "util_model_rl_requests": 120,
        "util_model_rl_input": 1000000,
        "util_model_rl_output": 1000000,
        "util_model_kwargs": "{}",
        "browser_model_provider": "openai",
        "browser_model_name": "gpt-4o-mini",
        "browser_model_api_base": "",
        "browser_model_vision": True,
        "browser_model_rl_requests": 60,
        "browser_model_rl_input": 1000000,
        "browser_model_rl_output": 1000000,
        "browser_model_kwargs": "{}",
        "browser_http_headers": "{}",
        "embed_model_provider": "openai",
        "embed_model_name": "text-embedding-3-small",
        "embed_model_api_base": "",
        "embed_model_rl_requests": 120,
        "embed_model_rl_input": 1000000,
        "embed_model_kwargs": "{}",
        "agent_profile": "default",
        "agent_knowledge_subdir": "skills",
        "agent_memory_subdir": "memory",
        "memory_recall_enabled": True,
        "memory_recall_delayed": False,
        "memory_recall_query_prep": True,
        "memory_recall_post_filter": True,
        "memory_recall_interval": 3,
        "memory_recall_history_len": 20,
        "memory_recall_similarity_threshold": 0.75,
        "memory_recall_memories_max_search": 20,
        "memory_recall_memories_max_result": 6,
        "memory_recall_solutions_max_search": 20,
        "memory_recall_solutions_max_result": 6,
        "memory_memorize_enabled": True,
        "memory_memorize_consolidation": True,
        "memory_memorize_replace_threshold": 0.88,
        "stt_model_size": "base",
        "stt_language": "en",
        "stt_silence_threshold": 0.02,
        "stt_silence_duration": 1.2,
        "stt_waiting_timeout": 3,
        "tts_kokoro": False,
        "shell_interface": "bash",
        "websocket_server_restart_enabled": True,
        "uvicorn_access_logs_enabled": False,
        "workdir_path": str(Path.cwd()),
        "workdir_show": True,
        "workdir_max_depth": 3,
        "workdir_max_lines": 400,
        "workdir_max_folders": 200,
        "workdir_max_files": 500,
        "workdir_gitignore": ".git\nnode_modules\n__pycache__",
        "auth_login": "",
        "auth_password": "",
        "root_password": "",
        "api_keys": {},
        "litellm_global_kwargs": "{}",
        "variables": "",
        "secrets": "",
        "mcp_server_enabled": bool(getattr(agent, "mcp_server", None)),
        "mcp_server_token": agent.config.get("mcp_server", {}).get("token", ""),
        "mcp_client_init_timeout": 15,
        "mcp_client_tool_timeout": 90,
        "a2a_server_enabled": False,
        "rfc_url": "",
        "rfc_password": "",
        "rfc_port_http": 80,
        "rfc_port_ssh": 22,
        "update_check_enabled": False,
    }

    compat_additional = {
        "chat_providers": [{"value": "openai", "label": "OpenAI"}, {"value": "google", "label": "Google"}],
        "embedding_providers": [{"value": "openai", "label": "OpenAI"}],
        "agent_subdirs": [{"value": "default", "label": "default"}],
        "knowledge_subdirs": [{"value": "skills", "label": "skills"}],
        "stt_models": [{"value": "tiny", "label": "tiny"}, {"value": "base", "label": "base"}, {"value": "small", "label": "small"}],
        "shell_interfaces": [{"value": "bash", "label": "Bash"}],
        "is_dockerized": True,
        "runtime_settings": {"uvicorn_access_logs_enabled": False},
    }

    def _make_context(name: str | None = None) -> dict:
        nonlocal context_counter
        context_counter += 1
        ctx_id = f"ctx_{secrets.token_hex(4)}"
        return {
            "id": ctx_id,
            "no": context_counter,
            "name": name or f"Chat {context_counter}",
            "created_at": time.time(),
            "running": False,
            "paused": False,
            "log_guid": uuid.uuid4().hex,
            "log_version": 0,
            "next_no": 1,
            "logs": [],
            "message_queue": [],
            "project": None,
        }

    def _ensure_context(ctx_id: str | None = None) -> dict:
        if ctx_id and ctx_id in contexts:
            return contexts[ctx_id]
        new_ctx = _make_context()
        contexts[new_ctx["id"]] = new_ctx
        return new_ctx

    def _push_log(ctx: dict, log_type: str, content: str, heading: str = "", kvps: dict | None = None):
        entry = {
            "no": ctx["next_no"],
            "type": log_type,
            "heading": heading,
            "content": content,
            "kvps": kvps or {},
        }
        ctx["next_no"] += 1
        ctx["logs"].append(entry)
        ctx["log_version"] += 1

    def _list_contexts() -> list[dict]:
        return sorted([
            {
                "id": c["id"],
                "no": c["no"],
                "name": c["name"],
                "created_at": c["created_at"],
                "running": c["running"],
                "project": c.get("project"),
                "message_queue": c.get("message_queue", []),
            }
            for c in contexts.values()
        ], key=lambda x: x.get("created_at", 0), reverse=True)

    def _list_tasks_for_sidebar() -> list[dict]:
        if not (hasattr(agent, "task_board") and agent.task_board):
            return []
        tasks = agent.task_board.list_all(limit=200)
        output = []
        for idx, task in enumerate(tasks, 1):
            data = task.to_dict()
            output.append({
                "id": data.get("id"),
                "no": idx,
                "task_name": data.get("title") or "Task",
                "state": data.get("status", "idle"),
                "running": data.get("status") == "in_progress",
                "created_at": data.get("created_at", 0),
                "project": None,
            })
        return output

    def _build_poll_snapshot(context_id: str | None, log_from: int = 0, notifications_from: int = 0) -> dict:
        ctx = _ensure_context(context_id)
        logs = ctx["logs"] if int(log_from or 0) <= 0 else []
        notifs = [n for n in notifications if n.get("version", 0) > int(notifications_from or 0)]
        return {
            "ok": True,
            "context": ctx["id"],
            "log_guid": ctx["log_guid"],
            "log_version": ctx["log_version"],
            "logs": logs,
            "log_progress": "",
            "log_progress_active": False,
            "paused": bool(ctx.get("paused")),
            "contexts": _list_contexts(),
            "tasks": _list_tasks_for_sidebar(),
            "notifications": notifs,
            "notifications_guid": notifications_guid,
            "notifications_version": notifications_version,
            "deselect_chat": False,
        }

    def _add_notification(message: str, ntype: str = "info", title: str = "Notification", priority: int = 10, group: str = ""):
        nonlocal notifications_version
        notifications_version += 1
        notifications.append({
            "id": uuid.uuid4().hex,
            "version": notifications_version,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "title": title,
            "message": message,
            "type": ntype,
            "priority": priority,
            "display_time": 4,
            "read": False,
            "group": group,
        })

    def _next_sio_envelope(event_name: str, data: dict, correlation_id: str | None = None) -> dict:
        nonlocal sio_sequence
        sio_sequence += 1
        return {
            "handlerId": "itak.state_sync",
            "eventId": f"{event_name}-{uuid.uuid4().hex}",
            "correlationId": correlation_id or f"push-{uuid.uuid4().hex}",
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "data": {
                "runtime_epoch": sio_runtime_epoch,
                "seq": sio_sequence,
                **(data or {}),
            },
        }

    _ensure_context(None)

    # --- REST Endpoints ---

    @app.get("/csrf_token")
    async def csrf_token_endpoint():
        return {"ok": True, "token": csrf_token, "runtime_id": runtime_id}

    @app.get("/logout")
    async def logout_endpoint():
        return {"ok": True}

    @app.post("/banners")
    async def banners(payload: dict | None = None):
        return {"ok": True, "banners": []}

    @app.post("/message_async")
    async def message_async(request: Request):
        payload = {}
        message = ""
        context_id = None
        message_id = None

        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            form = await request.form()
            message = str(form.get("text", "") or "")
            context_id = str(form.get("context", "") or "") or None
            message_id = str(form.get("message_id", "") or "") or None
        else:
            payload = await request.json()
            message = str(payload.get("text", "") or "")
            context_id = payload.get("context")
            message_id = payload.get("message_id")

        ctx = _ensure_context(context_id)
        ctx["running"] = True
        _push_log(ctx, "user", message, kvps={"message_id": message_id} if message_id else {})

        try:
            response = await agent.monologue(message)
        except Exception as e:
            response = f"Error: {e}"
        finally:
            ctx["running"] = False

        _push_log(ctx, "response", str(response), kvps={"finished": True})
        return {"ok": True, "context": ctx["id"]}

    @app.post("/poll")
    async def poll(payload: dict):
        return _build_poll_snapshot(
            context_id=payload.get("context"),
            log_from=payload.get("log_from", 0),
            notifications_from=payload.get("notifications_from", 0),
        )

    @app.post("/chat_create")
    async def chat_create(payload: dict):
        new_ctx = _make_context()
        contexts[new_ctx["id"]] = new_ctx
        return {"ok": True, "ctxid": new_ctx["id"]}

    @app.post("/chat_remove")
    async def chat_remove(payload: dict):
        ctx_id = payload.get("context")
        if ctx_id in contexts:
            del contexts[ctx_id]
        if not contexts:
            _ensure_context(None)
        return {"ok": True}

    @app.post("/chat_reset")
    async def chat_reset(payload: dict):
        ctx = _ensure_context(payload.get("context"))
        ctx["logs"] = []
        ctx["log_version"] = 0
        ctx["next_no"] = 1
        ctx["log_guid"] = uuid.uuid4().hex
        return {"ok": True}

    @app.post("/chat_export")
    async def chat_export(payload: dict):
        ctx = _ensure_context(payload.get("ctxid"))
        return {"ok": True, "ctxid": ctx["id"], "content": json.dumps(ctx, indent=2)}

    @app.post("/chat_load")
    async def chat_load(payload: dict):
        loaded = []
        for raw in payload.get("chats", []):
            try:
                data = json.loads(raw)
                new_ctx = _make_context(name=data.get("name") or "Imported chat")
                logs = data.get("logs", [])
                if isinstance(logs, list):
                    new_ctx["logs"] = logs
                    new_ctx["log_version"] = len(logs)
                    new_ctx["next_no"] = len(logs) + 1
                contexts[new_ctx["id"]] = new_ctx
                loaded.append(new_ctx["id"])
            except Exception:
                continue
        return {"ok": True, "ctxids": loaded}

    @app.post("/pause")
    async def pause(payload: dict):
        ctx = _ensure_context(payload.get("context"))
        ctx["paused"] = bool(payload.get("paused", False))
        return {"ok": True, "paused": ctx["paused"]}

    @app.post("/nudge")
    async def nudge(payload: dict):
        _add_notification("Agent nudged", "info", "Nudge")
        return {"ok": True}

    @app.post("/upload")
    async def upload(request: Request):
        form = await request.form()
        files = []
        for key in form.keys():
            values = form.getlist(key)
            for value in values:
                name = getattr(value, "filename", None)
                if name:
                    files.append(name)
        return {"ok": True, "filenames": files}

    @app.post("/message_queue_add")
    async def message_queue_add(payload: dict):
        ctx = _ensure_context(payload.get("context"))
        item = {
            "id": payload.get("item_id") or uuid.uuid4().hex,
            "text": payload.get("text", ""),
            "attachments": payload.get("attachments", []),
        }
        ctx["message_queue"].append(item)
        return {"ok": True, "item": item}

    @app.post("/message_queue_remove")
    async def message_queue_remove(payload: dict):
        ctx = _ensure_context(payload.get("context"))
        item_id = payload.get("item_id")
        if item_id:
            ctx["message_queue"] = [i for i in ctx["message_queue"] if i.get("id") != item_id]
        else:
            ctx["message_queue"] = []
        return {"ok": True}

    @app.post("/message_queue_send")
    async def message_queue_send(payload: dict):
        ctx = _ensure_context(payload.get("context"))
        send_all = bool(payload.get("send_all"))
        item_id = payload.get("item_id")
        to_send = []
        if send_all:
            to_send = list(ctx["message_queue"])
            ctx["message_queue"] = []
        elif item_id:
            for item in ctx["message_queue"]:
                if item.get("id") == item_id:
                    to_send = [item]
            ctx["message_queue"] = [i for i in ctx["message_queue"] if i.get("id") != item_id]
        for item in to_send:
            _push_log(ctx, "user", item.get("text", ""), kvps={"queued": True})
        return {"ok": True}

    @app.post("/notification_create")
    async def notification_create(payload: dict):
        _add_notification(
            message=payload.get("message", ""),
            ntype=payload.get("type", "info"),
            title=payload.get("title", "Notification"),
            priority=int(payload.get("priority", 10) or 10),
            group=payload.get("group", ""),
        )
        return {"ok": True}

    @app.post("/notifications_mark_read")
    async def notifications_mark_read(payload: dict):
        ids = set(payload.get("notification_ids", []) or [])
        mark_all = bool(payload.get("mark_all", False))
        for notification in notifications:
            if mark_all or notification.get("id") in ids:
                notification["read"] = True
        return {"ok": True}

    @app.post("/notifications_clear")
    async def notifications_clear(payload: dict | None = None):
        notifications.clear()
        return {"ok": True}

    @app.post("/settings_get")
    async def settings_get(request: Request):
        return {"ok": True, "settings": compat_settings, "additional": compat_additional}

    @app.post("/settings_set")
    async def settings_set(payload: dict):
        incoming = payload.get("settings", {}) if isinstance(payload, dict) else {}
        if isinstance(incoming, dict):
            compat_settings.update(incoming)
        return {"ok": True, "settings": compat_settings, "additional": compat_additional}

    @app.post("/settings_workdir_file_structure")
    async def settings_workdir_file_structure(payload: dict):
        workdir = Path(payload.get("workdir_path") or Path.cwd())
        max_depth = int(payload.get("workdir_max_depth") or 2)
        if not workdir.exists():
            return {"ok": False, "data": f"Path does not exist: {workdir}"}

        lines: list[str] = []

        def walk(path: Path, depth: int, prefix: str = ""):
            if depth > max_depth:
                return
            try:
                entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except Exception:
                return
            for item in entries[:50]:
                lines.append(f"{prefix}{item.name}{'/' if item.is_dir() else ''}")
                if item.is_dir():
                    walk(item, depth + 1, prefix + "  ")

        walk(workdir, 0)
        return {"ok": True, "data": "\n".join(lines)}

    @app.post("/projects")
    async def projects(payload: dict):
        action = payload.get("action", "list") if isinstance(payload, dict) else "list"
        if action in {"list", "list_options"}:
            return {"ok": True, "data": []}
        return {"ok": True, "data": None}

    @app.post("/agents")
    async def agents(payload: dict):
        return {"ok": True, "data": [{"key": "default", "label": "Default", "name": "default"}]}

    @app.post("/skills")
    async def skills(payload: dict):
        action = payload.get("action", "list") if isinstance(payload, dict) else "list"
        if action == "list":
            return {"ok": True, "data": []}
        return {"ok": True}

    @app.post("/skills_import_preview")
    async def skills_import_preview(request: Request):
        return {"ok": True, "data": {"items": []}}

    @app.post("/skills_import")
    async def skills_import(request: Request):
        return {"ok": True, "data": {"imported": 0}}

    @app.post("/memory_dashboard")
    async def memory_dashboard(payload: dict | None = None):
        return {"ok": True, "data": {"rows": [], "summary": {}}}

    @app.post("/mcp_servers_status")
    async def mcp_servers_status(payload: dict | None = None):
        if hasattr(agent, "mcp_client") and agent.mcp_client:
            status = agent.mcp_client.get_status()
            return {"ok": True, "data": status}
        return {"ok": True, "data": {"servers": {}}}

    @app.post("/mcp_servers_apply")
    async def mcp_servers_apply(payload: dict):
        return {"ok": True}

    @app.post("/mcp_server_get_detail")
    async def mcp_server_get_detail(payload: dict):
        return {"ok": True, "data": {}}

    @app.post("/mcp_server_get_log")
    async def mcp_server_get_log(payload: dict):
        return {"ok": True, "data": []}

    @app.post("/tunnel_proxy")
    async def tunnel_proxy(payload: dict):
        action = (payload or {}).get("action", "")
        if action == "status":
            return {"success": True, "status": "stopped", "notifications": []}
        if action == "create":
            return {
                "success": True,
                "tunnel_url": "https://example-tunnel.invalid",
                "notifications": [{"message": "Tunnel mode not configured in iTaK backend; using placeholder URL.", "type": "warning"}],
            }
        return {"success": True, "notifications": []}

    @app.post("/scheduler_tasks_list")
    async def scheduler_tasks_list(payload: dict | None = None):
        return {"ok": True, "tasks": []}

    @app.post("/scheduler_task_create")
    async def scheduler_task_create(payload: dict):
        return {"ok": True}

    @app.post("/scheduler_task_update")
    async def scheduler_task_update(payload: dict):
        return {"ok": True}

    @app.post("/scheduler_task_run")
    async def scheduler_task_run(payload: dict):
        return {"ok": True}

    @app.post("/scheduler_task_delete")
    async def scheduler_task_delete(payload: dict):
        return {"ok": True}

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

        if sio_server:
            try:
                snapshot = _build_poll_snapshot(context_id=None, log_from=0, notifications_from=0)
                envelope = _next_sio_envelope("state_push", {"snapshot": snapshot})
                await sio_server.emit("state_push", envelope, namespace="/state_sync")
            except Exception:
                pass

    if hasattr(agent, "progress") and agent.progress:
        agent.progress.register_callback(ws_broadcast)

    # --- Serve Frontend ---

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True))

    try:
        import socketio

        sio_server = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False,
        )

        @sio_server.on("connect", namespace="/state_sync")
        async def state_sync_connect(sid, environ, auth):
            provided_csrf = ""
            if isinstance(auth, dict):
                provided_csrf = str(auth.get("csrf_token", "") or "")
            if provided_csrf and provided_csrf != csrf_token:
                return False
            sio_sid_seqbase[sid] = sio_sequence
            return True

        @sio_server.on("disconnect", namespace="/state_sync")
        async def state_sync_disconnect(sid):
            sio_sid_seqbase.pop(sid, None)

        @sio_server.on("state_request", namespace="/state_sync")
        async def state_sync_request(sid, payload):
            payload = payload or {}
            request_data = payload.get("data", {}) if isinstance(payload, dict) else {}
            if not isinstance(request_data, dict):
                request_data = {}
            correlation_id = payload.get("correlationId") if isinstance(payload, dict) else None
            context_id = request_data.get("context")
            log_from = request_data.get("log_from", 0)
            notifications_from = request_data.get("notifications_from", 0)

            snapshot = _build_poll_snapshot(
                context_id=context_id,
                log_from=log_from,
                notifications_from=notifications_from,
            )

            seq_base = sio_sid_seqbase.get(sid, sio_sequence)
            sio_sid_seqbase[sid] = sio_sequence
            return {
                "correlationId": correlation_id,
                "results": [{
                    "ok": True,
                    "data": {
                        "runtime_epoch": sio_runtime_epoch,
                        "seq_base": seq_base,
                        "snapshot": snapshot,
                    },
                }],
            }

        @sio_server.on("connect", namespace="/")
        async def default_connect(sid, environ, auth):
            return True

        wrapped_app = socketio.ASGIApp(
            sio_server,
            other_asgi_app=app,
            socketio_path="socket.io",
        )
        return wrapped_app
    except Exception as e:
        logger.warning(f"Socket.IO compatibility disabled: {e}")

    return app


async def start_webui(agent: "Agent", host: str = "0.0.0.0", port: int = 48920):
    """Start the WebUI server."""
    import uvicorn

    app = create_app(agent)
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    logger.info(f"iTaK WebUI starting on http://{host}:{port}")
    await server.serve()
