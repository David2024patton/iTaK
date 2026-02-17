"""
iTaK WebUI - FastAPI backend for the monitoring dashboard.
Provides REST API + WebSocket for real-time agent monitoring.
"""

import asyncio
import base64
import json
import logging
import mimetypes
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import uuid
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest, urlopen

if TYPE_CHECKING:
    from core.agent import Agent

logger = logging.getLogger(__name__)


def create_app(agent: "Agent"):
    """Create the FastAPI application."""
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
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

    @app.middleware("http")
    async def no_cache_static(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.endswith((".js", ".html", ".css")):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

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

    def _to_title(value: str) -> str:
        return str(value or "").replace("_", " ").replace("-", " ").strip().title()

    def _read_catalog_payload() -> dict:
        root = Path(__file__).parent.parent
        catalog_path = root / "data" / "catalog" / "cherry_catalog.json"

        if not catalog_path.exists():
            return {}

        try:
            payload = json.loads(catalog_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except Exception as e:
            logger.warning(f"Failed to read catalog payload: {e}")
            return {}

    def _catalog_summary(payload: dict | None) -> dict:
        data = payload or {}
        provider_count = int(data.get("provider_count") or len(data.get("providers") or []))
        model_count = int(data.get("model_count") or len(data.get("all_model_ids") or []))
        return {
            "source": str(data.get("source") or ""),
            "provider_count": provider_count,
            "model_count": model_count,
        }

    def _load_catalog(payload: dict | None = None) -> tuple[list[dict], list[dict], list[dict]]:

        default_chat = [
            {"value": "openai", "label": "OpenAI"},
            {"value": "google", "label": "Google"},
            {"value": "anthropic", "label": "Anthropic"},
            {"value": "nvidia", "label": "NVIDIA"},
            {"value": "openrouter", "label": "OpenRouter"},
            {"value": "groq", "label": "Groq"},
            {"value": "ollama", "label": "Ollama"},
            {"value": "mistral", "label": "Mistral"},
            {"value": "deepseek", "label": "DeepSeek"},
        ]
        default_embed = [
            {"value": "openai", "label": "OpenAI"},
            {"value": "ollama", "label": "Ollama"},
            {"value": "fastembed", "label": "FastEmbed (Local)"},
        ]
        default_agents = [{"key": "default", "label": "Default", "name": "default"}]

        if payload is None:
            payload = _read_catalog_payload()
        if not payload:
            return default_chat, default_embed, default_agents

        try:
            providers_raw = payload.get("providers") or []
            models_raw = payload.get("all_model_ids") or []
            minapps_raw = payload.get("minapps") or []

            providers = [str(p).strip() for p in providers_raw if str(p).strip()]
            models = [str(m).strip() for m in models_raw if str(m).strip()]
            minapps = [m for m in minapps_raw if isinstance(m, dict) and str(m.get("id") or "").strip()]

            chat_providers = [{"value": p, "label": _to_title(p)} for p in sorted(set(providers), key=str.lower)]
            embedding_providers = list(chat_providers) if chat_providers else default_embed

            agents: list[dict] = [{"key": "default", "label": "Default", "name": "default"}]
            for provider in sorted(set(providers), key=str.lower):
                key = f"provider__{provider}"
                agents.append({
                    "key": key,
                    "label": f"{_to_title(provider)} Specialist",
                    "name": key,
                })
            for model_id in sorted(set(models), key=str.lower):
                key = f"model__{model_id}"
                agents.append({
                    "key": key,
                    "label": f"{model_id} Assistant",
                    "name": key,
                })
            for minapp in sorted(minapps, key=lambda x: str(x.get("name") or "").lower()):
                minapp_id = str(minapp.get("id") or "").strip()
                minapp_name = str(minapp.get("name") or minapp_id).strip()
                if not minapp_id:
                    continue
                key = f"minapp__{minapp_id}"
                agents.append({
                    "key": key,
                    "label": f"{minapp_name} Agent",
                    "name": key,
                })

            return (
                chat_providers or default_chat,
                embedding_providers or default_embed,
                agents or default_agents,
            )
        except Exception as e:
            logger.warning(f"Failed to load provider/assistant catalog: {e}")
            return default_chat, default_embed, default_agents

    def _fetch_text(url: str, timeout: int = 30) -> str:
        req = UrlRequest(url, headers={"User-Agent": "iTaK/1.0 (+catalog-sync)"})
        with urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")

    def _extract_provider_ids(providers_source: str) -> list[str]:
        providers: set[str] = set()
        key_pattern = re.compile(r"^\s*['\"]?([A-Za-z0-9_-]+)['\"]?\s*:\s*\{\s*$")
        lines = providers_source.splitlines()
        for idx, line in enumerate(lines):
            match = key_pattern.match(line)
            if not match:
                continue
            key = match.group(1)
            window = "\n".join(lines[idx + 1: idx + 24])
            if "api:" in window and "websites:" in window:
                providers.add(key)
        return sorted(providers, key=str.lower)

    def _extract_models_by_provider(models_source: str) -> dict[str, list[str]]:
        provider_pattern = re.compile(r"^\s*['\"]?([A-Za-z0-9_-]+)['\"]?\s*:\s*\[\s*$")
        model_pattern = re.compile(r"\bid\s*:\s*['\"]([^'\"]+)['\"]")

        models_by_provider: dict[str, set[str]] = {}
        current_provider: str | None = None
        bracket_depth = 0

        for line in models_source.splitlines():
            if current_provider is None:
                provider_match = provider_pattern.match(line)
                if provider_match:
                    current_provider = provider_match.group(1)
                    models_by_provider.setdefault(current_provider, set())
                    bracket_depth = line.count("[") - line.count("]")
                continue

            bracket_depth += line.count("[") - line.count("]")
            model_match = model_pattern.search(line)
            if model_match:
                models_by_provider[current_provider].add(model_match.group(1))

            if bracket_depth <= 0:
                current_provider = None
                bracket_depth = 0

        return {
            provider: sorted(values, key=str.lower)
            for provider, values in models_by_provider.items()
            if values
        }

    def _extract_minapps(minapps_source: str) -> list[dict]:
        start_idx = -1
        for marker in ["ORIGIN_DEFAULT_MIN_APPS", "DEFAULT_MIN_APPS", "minApps"]:
            start_idx = minapps_source.find(marker)
            if start_idx >= 0:
                break
        if start_idx < 0:
            return []

        assign_idx = minapps_source.find("=", start_idx)
        block_start = minapps_source.find("[", assign_idx if assign_idx >= 0 else start_idx)
        if block_start < 0:
            return []

        depth = 0
        block_end = -1
        for idx in range(block_start, len(minapps_source)):
            char = minapps_source[idx]
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    block_end = idx
                    break
        if block_end < 0:
            return []

        window = minapps_source[block_start:block_end + 1]
        id_pattern = re.compile(r"\bid\s*:\s*['\"]([^'\"]+)['\"]")
        name_pattern = re.compile(r"\bname\s*:\s*['\"]([^'\"]+)['\"]")
        url_pattern = re.compile(r"\burl\s*:\s*['\"]([^'\"]+)['\"]")

        minapps: list[dict] = []
        current_lines: list[str] = []
        brace_depth = 0
        for line in window.splitlines():
            opens = line.count("{")
            closes = line.count("}")

            if opens > 0 and brace_depth == 0:
                current_lines = []

            if brace_depth > 0 or opens > 0:
                current_lines.append(line)

            brace_depth += opens - closes
            if brace_depth != 0:
                continue
            if not current_lines:
                continue

            object_block = "\n".join(current_lines)
            id_match = id_pattern.search(object_block)
            name_match = name_pattern.search(object_block)
            url_match = url_pattern.search(object_block)
            if not (id_match and name_match and url_match):
                current_lines = []
                continue
            minapps.append({
                "id": id_match.group(1),
                "name": name_match.group(1),
                "url": url_match.group(1),
            })
            current_lines = []

        by_id: dict[str, dict] = {}
        for item in minapps:
            by_id[item["id"]] = item
        return sorted(by_id.values(), key=lambda x: x.get("name", "").lower())

    def _build_catalog_from_cherry(owner: str, repo: str, branch: str) -> dict:
        base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}"
        providers_url = f"{base}/src/renderer/src/config/providers.ts"
        models_url = f"{base}/src/renderer/src/config/models/default.ts"
        minapps_url = f"{base}/src/renderer/src/config/minapps.ts"

        providers_source = _fetch_text(providers_url)
        models_source = _fetch_text(models_url)
        minapps_source = _fetch_text(minapps_url)

        providers = _extract_provider_ids(providers_source)
        models_by_provider = _extract_models_by_provider(models_source)
        minapps = _extract_minapps(minapps_source)
        model_ids = sorted({m for models in models_by_provider.values() for m in models}, key=str.lower)

        provider_union = sorted(set(providers) | set(models_by_provider.keys()), key=str.lower)
        return {
            "source": f"Cherry Studio upstream: {owner}/{repo}@{branch}",
            "provider_count": len(provider_union),
            "model_count": len(model_ids),
            "providers": provider_union,
            "models_by_provider": {
                provider: models_by_provider.get(provider, [])
                for provider in provider_union
            },
            "all_model_ids": model_ids,
            "minapp_count": len(minapps),
            "minapps": minapps,
        }

    def _sync_catalog_from_cherry(owner: str = "David2024patton", repo: str = "cherry-studio", branch: str = "main") -> dict:
        payload = _build_catalog_from_cherry(owner=owner, repo=repo, branch=branch)
        root = Path(__file__).parent.parent
        catalog_dir = root / "data" / "catalog"
        catalog_dir.mkdir(parents=True, exist_ok=True)
        catalog_path = catalog_dir / "cherry_catalog.json"
        catalog_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    catalog_payload = _read_catalog_payload()
    catalog_minapps = catalog_payload.get("minapps", []) if isinstance(catalog_payload.get("minapps"), list) else []
    catalog_chat_providers, catalog_embedding_providers, catalog_agents = _load_catalog(catalog_payload)
    catalog_summary = _catalog_summary(catalog_payload)

    def _refresh_catalog() -> dict:
        nonlocal catalog_payload, catalog_summary, catalog_minapps, catalog_chat_providers, catalog_embedding_providers, catalog_agents
        catalog_payload = _read_catalog_payload()
        catalog_minapps = catalog_payload.get("minapps", []) if isinstance(catalog_payload.get("minapps"), list) else []
        catalog_summary = _catalog_summary(catalog_payload)
        catalog_chat_providers, catalog_embedding_providers, catalog_agents = _load_catalog(catalog_payload)
        compat_additional["chat_providers"] = catalog_chat_providers
        compat_additional["embedding_providers"] = catalog_embedding_providers
        compat_additional["catalog_source"] = catalog_summary.get("source", "")
        compat_additional["catalog_provider_count"] = catalog_summary.get("provider_count", 0)
        compat_additional["catalog_model_count"] = catalog_summary.get("model_count", 0)
        compat_additional["catalog_models_by_provider"] = catalog_payload.get("models_by_provider", {})
        compat_additional["catalog_minapp_count"] = len(catalog_minapps)
        return {
            "chat_providers": len(catalog_chat_providers),
            "embedding_providers": len(catalog_embedding_providers),
            "agents": len(catalog_agents),
            "minapps": len(catalog_minapps),
        }

    def _workdir_root() -> Path:
        raw = str(compat_settings.get("workdir_path") or Path.cwd())
        try:
            return Path(raw).expanduser().resolve()
        except Exception:
            return Path.cwd().resolve()

    def _resolve_workdir_path(raw_path: str | None) -> Path:
        root = _workdir_root()
        value = str(raw_path or "").strip()

        if value in {"", "$WORK_DIR", "/$WORK_DIR"}:
            candidate = root
        else:
            if value.startswith("file://"):
                value = value[7:]

            # Preserve compatibility with paths rooted at $WORK_DIR while
            # allowing absolute paths produced by the browser flow.
            if value.startswith("$WORK_DIR"):
                suffix = value[len("$WORK_DIR"):].lstrip("/")
                candidate = root / suffix
            elif value.startswith("/"):
                candidate = Path(value)
            else:
                candidate = root / value

        resolved = candidate.expanduser().resolve(strict=False)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError("Path is outside of workdir") from exc
        return resolved

    def _workdir_error(action: str, error: Exception) -> dict:
        message = str(error)
        if isinstance(error, ValueError) and "outside of workdir" in message:
            return {
                "ok": False,
                "error": f"{action} blocked: path is outside configured workdir",
            }
        if isinstance(error, PermissionError):
            return {
                "ok": False,
                "error": f"{action} blocked: permission denied",
            }
        return {"ok": False, "error": f"{action} failed: {message}"}

    def _entry_payload(path: Path) -> dict:
        stat = path.stat()
        return {
            "name": path.name,
            "path": str(path),
            "is_dir": path.is_dir(),
            "size": 0 if path.is_dir() else int(stat.st_size),
            "modified": int(stat.st_mtime),
        }

    def _list_workdir_entries(path: Path) -> list[dict]:
        entries: list[dict] = []
        try:
            children = sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
        except Exception:
            return entries

        for child in children:
            if child.name.startswith("."):
                continue
            try:
                entries.append(_entry_payload(child))
            except Exception:
                continue
        return entries

    def _workdir_browser_payload(path: Path) -> dict:
        root = _workdir_root()
        parent_path = str(path.parent) if path != root else ""
        return {
            "entries": _list_workdir_entries(path),
            "current_path": str(path),
            "parent_path": parent_path,
        }

    # --- Read initial model settings from agent's actual config ---
    _models_cfg = agent.config.get("models", {})
    _chat_cfg = _models_cfg.get("chat", {})
    _util_cfg = _models_cfg.get("utility", {})
    _browser_cfg = _models_cfg.get("browser", {})
    _embed_cfg = _models_cfg.get("embeddings", {})

    def _provider_from_model(model_str: str, cfg_provider: str = "") -> str:
        """Extract a provider label from a litellm model string or config."""
        if cfg_provider and cfg_provider != "litellm":
            return cfg_provider
        if "/" in model_str:
            return model_str.split("/", 1)[0]  # e.g. 'gemini' from 'gemini/gemini-2.5-pro'
        return cfg_provider or "openai"

    compat_settings = {
        "chat_model_provider": _provider_from_model(_chat_cfg.get("model", ""), _chat_cfg.get("provider", "")),
        "chat_model_name": _chat_cfg.get("model", ""),
        "chat_model_api_base": _chat_cfg.get("api_base", ""),
        "chat_model_ctx_length": int(_chat_cfg.get("context_window", 128000)),
        "chat_model_ctx_history": 0.7,
        "chat_model_vision": bool(_chat_cfg.get("use_vision", True)),
        "chat_model_rl_requests": 60,
        "chat_model_rl_input": 1000000,
        "chat_model_rl_output": 1000000,
        "chat_model_kwargs": "{}",
        "util_model_provider": _provider_from_model(_util_cfg.get("model", ""), _util_cfg.get("provider", "")),
        "util_model_name": _util_cfg.get("model", ""),
        "util_model_api_base": _util_cfg.get("api_base", ""),
        "util_model_rl_requests": 120,
        "util_model_rl_input": 1000000,
        "util_model_rl_output": 1000000,
        "util_model_kwargs": "{}",
        "browser_model_provider": _provider_from_model(_browser_cfg.get("model", ""), _browser_cfg.get("provider", "")),
        "browser_model_name": _browser_cfg.get("model", ""),
        "browser_model_api_base": _browser_cfg.get("api_base", ""),
        "browser_model_vision": bool(_browser_cfg.get("use_vision", True)),
        "browser_model_rl_requests": 60,
        "browser_model_rl_input": 1000000,
        "browser_model_rl_output": 1000000,
        "browser_model_kwargs": "{}",
        "browser_http_headers": "{}",
        "embed_model_provider": _provider_from_model(_embed_cfg.get("model", ""), _embed_cfg.get("provider", "")),
        "embed_model_name": _embed_cfg.get("model", ""),
        "embed_model_api_base": _embed_cfg.get("api_base", ""),
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
        "api_keys": agent.config.get("api_keys", {}),
        "litellm_global_kwargs": "{}",
        "variables": "",
        "secrets": "",
        "mcp_server_enabled": bool(getattr(agent, "mcp_server", None)),
        "mcp_server_token": agent.config.get("mcp_server", {}).get("token", ""),
        "mcp_servers": "{\n  \"mcpServers\": {}\n}",
        "mcpServers": "{\n  \"mcpServers\": {}\n}",
        "mcp_client_init_timeout": 15,
        "mcp_client_tool_timeout": 90,
        "gogcli_binary": agent.config.get("gogcli", {}).get("binary", "gog"),
        "gogcli_timeout_seconds": int(agent.config.get("gogcli", {}).get("timeout_seconds", 60)),
        "a2a_server_enabled": False,
        "rfc_url": "",
        "rfc_password": "",
        "rfc_port_http": 80,
        "rfc_port_ssh": 22,
        "update_check_enabled": False,
        "skills_trusted_sources": "",
        "skills_allow_untrusted_import": True,
        "skills_require_review_summary": True,
    }

    # --- Propagate API keys at startup (same logic as settings_set) ---
    import litellm as _litellm_init
    _startup_keys = compat_settings.get("api_keys", {})
    if isinstance(_startup_keys, dict):
        _key_env_map_startup = {
            "openai": "OPENAI_API_KEY",
            "google": "GEMINI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "groq": "GROQ_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "nvidia": "NVIDIA_NIM_API_KEY",
        }
        for _p_label, _k_value in _startup_keys.items():
            if not _k_value:
                continue
            _env_name = _key_env_map_startup.get(_p_label.lower())
            if _env_name:
                os.environ[_env_name] = str(_k_value)
                setattr(_litellm_init, _env_name.lower(), str(_k_value))
            else:
                os.environ[f"{_p_label.upper()}_API_KEY"] = str(_k_value)
        logger.info(f"Startup: propagated {len(_startup_keys)} API key(s) to environment")

    # --- Settings persistence helper ---
    def _persist_config_settings():
        """Write current model settings and API keys back to config.json."""
        try:
            config_path = Path(__file__).parent.parent / "config.json"
            existing = {}
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)

            # Update models section
            models = existing.setdefault("models", {})
            _role_persist_map = {
                "chat": ("chat_model_provider", "chat_model_name", "chat_model_api_base"),
                "utility": ("util_model_provider", "util_model_name", "util_model_api_base"),
                "browser": ("browser_model_provider", "browser_model_name", "browser_model_api_base"),
            }
            for role, (prov_key, name_key, base_key) in _role_persist_map.items():
                cfg = models.setdefault(role, {})
                cfg["provider"] = compat_settings.get(prov_key, "")
                cfg["model"] = compat_settings.get(name_key, "")
                cfg["api_base"] = compat_settings.get(base_key, "")

            # Update API keys
            if compat_settings.get("api_keys"):
                existing["api_keys"] = dict(compat_settings["api_keys"])

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
            logger.info("Settings persisted to config.json")
        except Exception as e:
            logger.warning(f"Failed to persist settings to config.json: {e}")


    # Provider -> default API base URL map
    _provider_endpoints = {
        "openai": "",
        "google": "",
        "gemini": "",
        "anthropic": "",
        "nvidia": "https://integrate.api.nvidia.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "groq": "https://api.groq.com/openai/v1",
        "ollama": "http://localhost:11434/v1",
        "mistral": "https://api.mistral.ai/v1",
        "deepseek": "https://api.deepseek.com/v1",
    }

    compat_additional = {
        "chat_providers": catalog_chat_providers,
        "embedding_providers": catalog_embedding_providers,
        "catalog_source": catalog_summary.get("source", ""),
        "catalog_provider_count": catalog_summary.get("provider_count", 0),
        "catalog_model_count": catalog_summary.get("model_count", 0),
        "catalog_models_by_provider": catalog_payload.get("models_by_provider", {}),
        "catalog_minapp_count": len(catalog_minapps),
        "provider_endpoints": _provider_endpoints,
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

    @app.post("/chat_files_path_get")
    async def chat_files_path_get(payload: dict | None = None):
        return {"ok": True, "path": "$WORK_DIR"}

    @app.get("/get_work_dir_files")
    async def get_work_dir_files(path: str = ""):
        try:
            target = _resolve_workdir_path(path)
            if not target.exists():
                return {"ok": False, "error": f"Path does not exist: {target}"}
            if not target.is_dir():
                return {"ok": False, "error": "Path is not a directory"}
            return {"ok": True, "data": _workdir_browser_payload(target)}
        except Exception as e:
            return {"ok": False, "error": f"Error fetching files: {e}"}

    @app.post("/rename_work_dir_file")
    async def rename_work_dir_file(payload: dict | None = None):
        data = payload or {}
        action = str(data.get("action") or "rename")
        new_name = str(data.get("newName") or "").strip()

        if not new_name:
            return {"ok": False, "error": "Name is required"}
        if new_name in {".", ".."} or "/" in new_name or "\\" in new_name:
            return {"ok": False, "error": "Invalid name"}

        try:
            if action == "create-folder":
                parent = _resolve_workdir_path(data.get("parentPath") or data.get("currentPath"))
                if not parent.exists() or not parent.is_dir():
                    return {"ok": False, "error": "Parent directory not found"}
                target = parent / new_name
                if target.exists():
                    return {"ok": False, "error": f"An item named '{new_name}' already exists."}
                target.mkdir(parents=False, exist_ok=False)
                current = _resolve_workdir_path(data.get("currentPath") or parent)
                return {"ok": True, "data": _workdir_browser_payload(current)}

            source = _resolve_workdir_path(data.get("path"))
            if not source.exists():
                return {"ok": False, "error": "File or folder not found"}
            if source == _workdir_root():
                return {"ok": False, "error": "Rename blocked: cannot rename workdir root"}
            destination = source.with_name(new_name)
            if destination.exists() and destination != source:
                return {"ok": False, "error": f"An item named '{new_name}' already exists."}
            source.rename(destination)
            current = _resolve_workdir_path(data.get("currentPath") or destination.parent)
            return {"ok": True, "data": _workdir_browser_payload(current)}
        except Exception as e:
            return _workdir_error("Rename", e)

    @app.post("/delete_work_dir_file")
    async def delete_work_dir_file(payload: dict | None = None):
        data = payload or {}
        try:
            target = _resolve_workdir_path(data.get("path"))
            if not target.exists():
                return {"ok": False, "error": "File or folder not found"}
            if target == _workdir_root():
                return {"ok": False, "error": "Delete blocked: cannot delete workdir root"}

            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

            current = _resolve_workdir_path(data.get("currentPath") or target.parent)
            if not current.exists() or not current.is_dir():
                current = _workdir_root()
            return {"ok": True, "data": _workdir_browser_payload(current)}
        except Exception as e:
            return _workdir_error("Delete", e)

    @app.get("/edit_work_dir_file")
    async def edit_work_dir_file_get(path: str):
        try:
            target = _resolve_workdir_path(path)
            if not target.exists():
                return {"ok": False, "error": "File not found"}
            if target.is_dir():
                return {"ok": False, "error": "Cannot edit a directory"}

            content = target.read_text(encoding="utf-8", errors="replace")
            mime_type = mimetypes.guess_type(target.name)[0] or "text/plain"
            return {
                "ok": True,
                "data": {
                    "name": target.name,
                    "path": str(target),
                    "content": content,
                    "mime_type": mime_type,
                },
            }
        except Exception as e:
            return _workdir_error("Edit", e)

    @app.post("/edit_work_dir_file")
    async def edit_work_dir_file_set(payload: dict | None = None):
        data = payload or {}
        raw_path = data.get("path")
        content = data.get("content", "")
        if raw_path is None:
            return {"ok": False, "error": "Path is required"}
        if not isinstance(content, str):
            return {"ok": False, "error": "Content must be a string"}

        try:
            target = _resolve_workdir_path(raw_path)
            if target.exists() and target.is_dir():
                return {"ok": False, "error": "Cannot edit a directory"}

            parent = target.parent
            if not parent.exists() or not parent.is_dir():
                return {"ok": False, "error": "Parent directory not found"}

            target.write_text(content, encoding="utf-8")
            return {"ok": True, "data": {"path": str(target), "name": target.name}}
        except Exception as e:
            return _workdir_error("Save", e)

    @app.post("/upload_work_dir_files")
    async def upload_work_dir_files(request: Request):
        failed: list[dict] = []
        try:
            form = await request.form()
            current = _resolve_workdir_path(form.get("path"))
            if not current.exists() or not current.is_dir():
                return {"ok": False, "error": "Upload path not found"}

            uploads = []
            uploads.extend(form.getlist("files[]"))
            uploads.extend(form.getlist("files"))

            for file_obj in uploads:
                filename = str(getattr(file_obj, "filename", "") or "").strip()
                if not filename:
                    continue
                safe_name = Path(filename).name
                destination = current / safe_name
                try:
                    content = await file_obj.read()
                    destination.write_bytes(content)
                except Exception as file_error:
                    failed.append({"name": safe_name, "error": str(file_error)})

            payload = {"ok": True, "data": _workdir_browser_payload(current)}
            if failed:
                payload["failed"] = failed
            return payload
        except Exception as e:
            return _workdir_error("Upload", e)

    @app.get("/download_work_dir_file")
    async def download_work_dir_file(path: str):
        try:
            target = _resolve_workdir_path(path)
            if not target.exists() or not target.is_file():
                return JSONResponse(status_code=404, content={"ok": False, "error": "File not found"})
            return FileResponse(path=str(target), filename=target.name)
        except Exception as e:
            return JSONResponse(status_code=400, content=_workdir_error("Download", e))

    @app.post("/file_info")
    async def file_info(payload: dict | None = None):
        data = payload or {}
        raw_path = data.get("path")
        try:
            target = _resolve_workdir_path(raw_path)
        except Exception:
            return {
                "exists": False,
                "is_dir": False,
                "abs_path": "",
                "file_name": "",
            }

        exists = target.exists()
        return {
            "exists": exists,
            "is_dir": bool(target.is_dir()) if exists else False,
            "abs_path": str(target),
            "file_name": target.name,
        }

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
        item_id = payload.get("item_id") or uuid.uuid4().hex
        for existing in ctx["message_queue"]:
            if existing.get("id") == item_id:
                return {"ok": True, "item": existing, "deduplicated": True}

        item = {
            "id": item_id,
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
            for idx, item in enumerate(ctx["message_queue"]):
                if item.get("id") == item_id:
                    to_send = [item]
                    del ctx["message_queue"][idx]
                    break
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

            # --- Propagate model settings to agent.model_router ---
            import litellm as _litellm

            # Helper: build a litellm model string from provider + model name
            def _litellm_model(provider: str, model_name: str, api_base: str = "") -> str:
                """Convert WebUI provider/model fields into a litellm model identifier."""
                if not model_name:
                    return ""
                # Map common WebUI provider labels to litellm prefixes
                prefix_map = {
                    "openai": "openai",
                    "google": "gemini",
                    "gemini": "gemini",
                    "anthropic": "anthropic",
                    "openrouter": "openrouter",
                    "groq": "groq",
                    "ollama": "ollama",
                    "mistral": "mistral",
                    "deepseek": "deepseek",
                    "nvidia": "nvidia_nim",
                }
                # Known litellm provider prefixes (superset of prefix_map values)
                _known_prefixes = set(prefix_map.values()) | {
                    "nvidia_nim", "azure", "bedrock", "vertex_ai", "huggingface",
                    "together_ai", "replicate", "cohere", "sagemaker", "fireworks_ai",
                }
                # If the model already has a known litellm provider prefix, use as-is
                if "/" in model_name:
                    maybe_prefix = model_name.split("/", 1)[0]
                    if maybe_prefix in _known_prefixes:
                        return model_name
                # Otherwise, prepend the mapped prefix
                prefix = prefix_map.get(provider.lower(), provider.lower()) if provider else ""
                if prefix:
                    return f"{prefix}/{model_name}"
                return model_name

            # Map of (provider_key, model_key, base_key) -> router role
            _role_map = {
                "chat": ("chat_model_provider", "chat_model_name", "chat_model_api_base"),
                "utility": ("util_model_provider", "util_model_name", "util_model_api_base"),
                "browser": ("browser_model_provider", "browser_model_name", "browser_model_api_base"),
            }

            for role, (prov_key, name_key, base_key) in _role_map.items():
                if prov_key in incoming or name_key in incoming or base_key in incoming:
                    provider = compat_settings.get(prov_key, "")
                    model_name = compat_settings.get(name_key, "")
                    api_base = compat_settings.get(base_key, "")
                    litellm_model = _litellm_model(provider, model_name, api_base)
                    if litellm_model:
                        agent.model_router.set_model(role, litellm_model)
                        # Also update api_base in the router's internal config
                        role_cfg_map = {
                            "chat": agent.model_router._chat_config,
                            "utility": agent.model_router._utility_config,
                            "browser": agent.model_router._browser_config,
                        }
                        if api_base:
                            role_cfg_map[role]["api_base"] = api_base
                        elif "api_base" in role_cfg_map[role]:
                            del role_cfg_map[role]["api_base"]
                        logger.info(f"Model router updated: {role} -> {litellm_model}" + (f" (base: {api_base})" if api_base else ""))

            # Propagate API keys to litellm
            api_keys = incoming.get("api_keys") or compat_settings.get("api_keys", {})
            if isinstance(api_keys, dict):
                _key_env_map = {
                    "openai": "OPENAI_API_KEY",
                    "google": "GEMINI_API_KEY",
                    "gemini": "GEMINI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY",
                    "groq": "GROQ_API_KEY",
                    "mistral": "MISTRAL_API_KEY",
                    "deepseek": "DEEPSEEK_API_KEY",
                    "nvidia": "NVIDIA_NIM_API_KEY",
                }
                for provider_label, key_value in api_keys.items():
                    if not key_value:
                        continue
                    env_name = _key_env_map.get(provider_label.lower())
                    if env_name:
                        os.environ[env_name] = str(key_value)
                        setattr(_litellm, env_name.lower(), str(key_value))
                    else:
                        # Generic: set as env var for litellm to pick up
                        generic_env = f"{provider_label.upper()}_API_KEY"
                        os.environ[generic_env] = str(key_value)

            # Propagate gogcli settings
            gogcli_cfg = agent.config.setdefault("gogcli", {})
            if "gogcli_binary" in incoming:
                gogcli_cfg["binary"] = str(incoming.get("gogcli_binary") or "gog")
            if "gogcli_timeout_seconds" in incoming:
                try:
                    gogcli_cfg["timeout_seconds"] = max(1, int(incoming.get("gogcli_timeout_seconds") or 60))
                except Exception:
                    gogcli_cfg["timeout_seconds"] = 60

            # Persist settings to disk so they survive container restarts
            _persist_config_settings()

        return {"ok": True, "settings": compat_settings, "additional": compat_additional}

    @app.post("/catalog_refresh")
    async def catalog_refresh(payload: dict | None = None):
        counts = _refresh_catalog()
        return {"ok": True, "counts": counts, "summary": catalog_summary, "additional": compat_additional}

    @app.post("/catalog_status")
    async def catalog_status(payload: dict | None = None):
        return {
            "ok": True,
            "summary": catalog_summary,
            "counts": {
                "chat_providers": len(catalog_chat_providers),
                "embedding_providers": len(catalog_embedding_providers),
                "agents": len(catalog_agents),
                "minapps": len(catalog_minapps),
            },
            "additional": compat_additional,
        }

    @app.post("/minapps")
    async def minapps(payload: dict | None = None):
        return {"ok": True, "data": catalog_minapps, "count": len(catalog_minapps), "source": catalog_summary.get("source", "")}

    @app.post("/launchpad_apps")
    async def launchpad_apps(payload: dict | None = None):
        return {"ok": True, "data": catalog_minapps, "count": len(catalog_minapps), "source": catalog_summary.get("source", "")}

    @app.post("/models_list")
    async def models_list(payload: dict):
        """Fetch available models from a provider's API endpoint."""
        provider = str(payload.get("provider", "")).strip().lower()
        api_key = str(payload.get("api_key", "")).strip()
        api_base = str(payload.get("api_base", "")).strip()

        # Use default endpoint if not provided
        if not api_base:
            api_base = _provider_endpoints.get(provider, "")

        if not api_base:
            # For providers with default SDK endpoints, try standard ones
            _fallback_bases = {
                "openai": "https://api.openai.com/v1",
                "anthropic": "https://api.anthropic.com/v1",
                "google": "https://generativelanguage.googleapis.com/v1beta",
                "gemini": "https://generativelanguage.googleapis.com/v1beta",
            }
            api_base = _fallback_bases.get(provider, "")

        if not api_base:
            return {"ok": False, "error": f"No API endpoint known for provider '{provider}'. Please enter an API base URL.", "models": []}

        # Normalize URL
        api_base = api_base.rstrip("/")

        # Special handling for Google/Gemini
        if provider in ("google", "gemini"):
            models_url = f"{api_base}/models?key={api_key}" if api_key else f"{api_base}/models"
            try:
                import urllib.request
                req = urllib.request.Request(models_url, headers={"User-Agent": "iTaK/1.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                models_list = []
                for m in data.get("models", []):
                    model_name = m.get("name", "")
                    display_name = m.get("displayName", model_name)
                    # name is like 'models/gemini-2.5-pro' -> extract 'gemini-2.5-pro'
                    model_id = model_name.split("/")[-1] if "/" in model_name else model_name
                    if model_id and "generateContent" in str(m.get("supportedGenerationMethods", [])):
                        models_list.append({"id": model_id, "name": display_name})
                return {"ok": True, "models": sorted(models_list, key=lambda x: x["name"]), "provider": provider}
            except Exception as e:
                return {"ok": False, "error": f"Failed to fetch models from Google: {e}", "models": []}

        # Standard OpenAI-compatible /models endpoint
        models_url = f"{api_base}/models"
        try:
            import urllib.request
            headers = {"User-Agent": "iTaK/1.0"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            req = urllib.request.Request(models_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))

            models_list = []
            raw_models = data.get("data", []) if isinstance(data.get("data"), list) else []
            if not raw_models and isinstance(data.get("models"), list):
                raw_models = data["models"]

            for m in raw_models:
                if isinstance(m, dict):
                    mid = m.get("id", "")
                    mname = m.get("name") or m.get("id", "")
                    if mid:
                        models_list.append({"id": mid, "name": mname})
                elif isinstance(m, str):
                    models_list.append({"id": m, "name": m})

            return {"ok": True, "models": sorted(models_list, key=lambda x: x["name"]), "provider": provider}
        except Exception as e:
            return {"ok": False, "error": f"Failed to fetch models: {e}", "models": []}

    @app.post("/logs_get")
    async def logs_get(payload: dict | None = None):
        """Return recent agent logs for the logs viewer."""
        max_lines = int((payload or {}).get("max_lines", 200))
        log_lines = []

        # Try reading from agent log file
        log_paths = [
            Path(__file__).parent.parent / "logs" / "agent.log",
            Path(__file__).parent.parent / "log" / "agent.log",
            Path(__file__).parent.parent / "agent.log",
        ]

        log_file = None
        for lp in log_paths:
            if lp.exists():
                log_file = lp
                break

        if log_file:
            try:
                with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                    all_lines = f.readlines()
                    log_lines = all_lines[-max_lines:]
            except Exception as e:
                log_lines = [f"Error reading log file: {e}\n"]

        # Also collect recent context logs from all chat contexts
        context_logs = []
        for ctx_id, ctx in contexts.items():
            for entry in ctx.get("logs", [])[-50:]:
                context_logs.append({
                    "context": ctx.get("name", ctx_id),
                    "type": entry.get("type", ""),
                    "content": entry.get("content", ""),
                    "heading": entry.get("heading", ""),
                })

        # Include Python logging records if available
        import logging
        root_logger = logging.getLogger()
        handler_logs = []
        for handler in root_logger.handlers:
            if hasattr(handler, "buffer"):
                for record in handler.buffer[-max_lines:]:
                    handler_logs.append(handler.format(record))

        return {
            "ok": True,
            "file_logs": "".join(log_lines),
            "context_logs": context_logs[-max_lines:],
            "handler_logs": handler_logs[-max_lines:],
            "timestamp": time.time(),
        }

    @app.post("/agents_catalog")
    async def agents_catalog(payload: dict | None = None):
        provider_agents = [a for a in catalog_agents if str(a.get("key", "")).startswith("provider__")]
        model_agents = [a for a in catalog_agents if str(a.get("key", "")).startswith("model__")]
        minapp_agents = [a for a in catalog_agents if str(a.get("key", "")).startswith("minapp__")]
        return {
            "ok": True,
            "source": catalog_summary.get("source", ""),
            "counts": {
                "provider_agents": len(provider_agents),
                "model_agents": len(model_agents),
                "minapp_agents": len(minapp_agents),
                "total_catalog_agents": len(catalog_agents),
            },
            "data": {
                "provider_agents": provider_agents,
                "model_agents": model_agents,
                "minapp_agents": minapp_agents,
            },
        }

    @app.post("/catalog_sync_from_cherry")
    async def catalog_sync_from_cherry(payload: dict | None = None):
        data = payload or {}
        owner = str(data.get("owner") or "David2024patton")
        repo = str(data.get("repo") or "cherry-studio")
        branch = str(data.get("branch") or "main")

        try:
            catalog = _sync_catalog_from_cherry(owner=owner, repo=repo, branch=branch)
            counts = _refresh_catalog()
            return {
                "ok": True,
                "counts": counts,
                "summary": catalog_summary,
                "source": catalog_summary.get("source", ""),
                "providers": catalog_summary.get("provider_count", 0),
                "models": catalog_summary.get("model_count", 0),
                "minapps": len(catalog_minapps),
                "additional": compat_additional,
            }
        except (HTTPError, URLError, TimeoutError) as e:
            return {"ok": False, "error": f"Catalog sync failed: {e}"}
        except Exception as e:
            return {"ok": False, "error": f"Catalog sync failed: {e}"}

    @app.post("/system_test_run")
    async def system_test_run(request: Request, payload: dict | None = None):
        data = payload or {}
        test_name = str(data.get("test") or "all").strip().lower()

        repo_root = Path(__file__).parent.parent
        script_map = {
            "resources": "tools/check_resource_endpoints.sh",
            "memory": "tools/check_memory_smoke.sh",
            "chat": "tools/check_chat_smoke.sh",
            "all": "tools/check_system_smoke.sh",
        }

        rel_script = script_map.get(test_name)
        if not rel_script:
            return {
                "ok": False,
                "error": "Unknown test. Use one of: resources, memory, chat, all",
                "test": test_name,
            }

        script_path = repo_root / rel_script
        if not script_path.exists():
            return {
                "ok": False,
                "error": f"Script not found: {rel_script}",
                "test": test_name,
            }

        command = ["bash", str(script_path)]
        env = os.environ.copy()
        env["WEBUI_BASE_URL"] = str(request.base_url).rstrip("/")

        try:
            completed = await asyncio.to_thread(
                subprocess.run,
                command,
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=300,
                env=env,
            )
            output = (completed.stdout or "").strip()
            error_output = (completed.stderr or "").strip()
            merged_output = "\n".join([part for part in [output, error_output] if part]).strip()

            return {
                "ok": completed.returncode == 0,
                "test": test_name,
                "command": f"bash {rel_script}",
                "exit_code": completed.returncode,
                "output": merged_output,
            }
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "test": test_name,
                "command": f"bash {rel_script}",
                "exit_code": -1,
                "error": "Test timed out after 300 seconds",
            }
        except Exception as exc:
            return {
                "ok": False,
                "test": test_name,
                "command": f"bash {rel_script}",
                "exit_code": -1,
                "error": str(exc),
            }

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
        from security.scanner import SecurityScanner

        projects_root = Path(__file__).parent.parent / "data" / "projects"
        projects_root.mkdir(parents=True, exist_ok=True)
        state_file = projects_root / "projects.json"

        def _load_state() -> list[dict]:
            if not state_file.exists():
                return []
            try:
                raw = json.loads(state_file.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    return raw
            except Exception:
                pass
            return []

        def _save_state(data: list[dict]) -> None:
            state_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        def _project_path(name: str) -> Path:
            return (projects_root / name).resolve()

        def _ensure_project_layout(path: Path) -> None:
            (path / ".a0proj" / "instructions").mkdir(parents=True, exist_ok=True)
            (path / ".a0proj" / "knowledge").mkdir(parents=True, exist_ok=True)
            (path / ".a0proj" / "skills").mkdir(parents=True, exist_ok=True)
            (path / ".a0proj" / "secrets").mkdir(parents=True, exist_ok=True)

        def _get_project(name: str) -> tuple[dict | None, list[dict], int]:
            state = _load_state()
            for idx, item in enumerate(state):
                if item.get("name") == name:
                    return item, state, idx
            return None, state, -1

        def _git_status_for(path: Path) -> dict:
            if not (path / ".git").exists():
                return {
                    "is_git_repo": False,
                    "remote_url": "",
                    "current_branch": "",
                    "is_dirty": False,
                    "untracked_count": 0,
                    "last_commit": None,
                }

            def _run(args: list[str]) -> str:
                try:
                    result = subprocess.run(
                        args,
                        cwd=str(path),
                        capture_output=True,
                        text=True,
                        timeout=8,
                        check=False,
                    )
                    return (result.stdout or "").strip()
                except Exception:
                    return ""

            remote_url = _run(["git", "config", "--get", "remote.origin.url"])
            branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            porcelain = _run(["git", "status", "--porcelain"]) or ""
            lines = [line for line in porcelain.splitlines() if line.strip()]
            untracked_count = sum(1 for line in lines if line.startswith("??"))
            commit_hash = _run(["git", "log", "-1", "--pretty=%h"])
            commit_message = _run(["git", "log", "-1", "--pretty=%s"])
            commit_author = _run(["git", "log", "-1", "--pretty=%an"])
            commit_date = _run(["git", "log", "-1", "--pretty=%ad", "--date=short"])
            return {
                "is_git_repo": True,
                "remote_url": remote_url,
                "current_branch": branch,
                "is_dirty": bool(lines),
                "untracked_count": untracked_count,
                "last_commit": {
                    "hash": commit_hash,
                    "message": commit_message,
                    "author": commit_author,
                    "date": commit_date,
                }
                if commit_hash
                else None,
            }

        def _project_counts(path: Path) -> tuple[int, int]:
            instructions_count = len(list((path / ".a0proj" / "instructions").glob("*.md")))
            knowledge_count = len(list((path / ".a0proj" / "knowledge").glob("**/*")))
            return instructions_count, knowledge_count

        def _normalize_project(data: dict) -> dict:
            now = int(time.time())
            name = str(data.get("name") or "").strip()
            title = str(data.get("title") or name or "Project")
            description = str(data.get("description") or "")
            memory_mode = str(data.get("memory") or "own")
            color = str(data.get("color") or "")
            return {
                "name": name,
                "title": title,
                "description": description,
                "memory": memory_mode,
                "color": color,
                "file_structure": data.get("file_structure") or {},
                "secrets": data.get("secrets") or {},
                "git_url": str(data.get("git_url") or ""),
                "created_at": int(data.get("created_at") or now),
                "updated_at": now,
            }

        action = payload.get("action", "list") if isinstance(payload, dict) else "list"
        if action == "list":
            state = sorted(_load_state(), key=lambda p: (p.get("title") or p.get("name") or "").lower())
            return {"ok": True, "data": state}

        if action == "list_options":
            options = [
                {
                    "key": str(project.get("name") or ""),
                    "label": str(project.get("title") or project.get("name") or ""),
                }
                for project in _load_state()
                if project.get("name")
            ]
            options.sort(key=lambda item: (item.get("label") or "").lower())
            return {"ok": True, "data": options}

        if action == "create":
            project_in = payload.get("project") if isinstance(payload, dict) else {}
            project = _normalize_project(project_in or {})
            name = project.get("name", "")
            if not name or not re.match(r"^[a-zA-Z0-9._-]+$", name):
                return {"ok": False, "error": "Invalid project name"}

            existing, state, _ = _get_project(name)
            if existing:
                return {"ok": False, "error": "Project already exists"}

            path = _project_path(name)
            path.mkdir(parents=True, exist_ok=False)
            _ensure_project_layout(path)
            instructions_count, knowledge_count = _project_counts(path)
            project["instruction_files_count"] = instructions_count
            project["knowledge_files_count"] = knowledge_count
            state.append(project)
            _save_state(state)
            return {"ok": True, "data": project}

        if action == "clone":
            project_in = payload.get("project") if isinstance(payload, dict) else {}
            project = _normalize_project(project_in or {})
            name = project.get("name", "")
            git_url = str((project_in or {}).get("git_url") or "").strip()
            git_token = str((project_in or {}).get("git_token") or "").strip()

            if not name or not re.match(r"^[a-zA-Z0-9._-]+$", name):
                return {"ok": False, "error": "Invalid project name"}
            if not git_url:
                return {"ok": False, "error": "Git URL is required"}

            existing, state, _ = _get_project(name)
            if existing:
                return {"ok": False, "error": "Project already exists"}

            clone_url = git_url
            if git_token and git_url.startswith("https://"):
                parsed = urlsplit(git_url)
                safe_netloc = f"{quote(git_token, safe='')}@{parsed.netloc}"
                clone_url = urlunsplit((parsed.scheme, safe_netloc, parsed.path, parsed.query, parsed.fragment))

            scanner = SecurityScanner()
            scan = scanner.scan_code(clone_url, source="project_clone_url")
            if scan.get("blocked"):
                return {"ok": False, "error": "Clone blocked by security policy"}

            path = _project_path(name)
            try:
                result = subprocess.run(
                    ["git", "clone", clone_url, str(path)],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                if result.returncode != 0:
                    return {"ok": False, "error": (result.stderr or "Clone failed").strip()}
            except Exception as exc:
                return {"ok": False, "error": f"Clone failed: {exc}"}

            _ensure_project_layout(path)
            instructions_count, knowledge_count = _project_counts(path)
            project["instruction_files_count"] = instructions_count
            project["knowledge_files_count"] = knowledge_count
            project["git_url"] = git_url
            state.append(project)
            _save_state(state)
            loaded = dict(project)
            loaded["git_status"] = _git_status_for(path)
            return {"ok": True, "data": loaded}

        if action == "load":
            name = str(payload.get("name") or "")
            project, _, _ = _get_project(name)
            if not project:
                return {"ok": False, "error": "Project not found"}

            path = _project_path(name)
            instructions_count, knowledge_count = _project_counts(path)
            loaded = dict(project)
            loaded["instruction_files_count"] = instructions_count
            loaded["knowledge_files_count"] = knowledge_count
            loaded["git_status"] = _git_status_for(path)
            return {"ok": True, "data": loaded}

        if action == "update":
            project_in = payload.get("project") if isinstance(payload, dict) else {}
            name = str((project_in or {}).get("name") or "")
            current, state, idx = _get_project(name)
            if not current:
                return {"ok": False, "error": "Project not found"}

            merged = dict(current)
            merged.update(_normalize_project(project_in or {}))
            merged["created_at"] = current.get("created_at", merged.get("created_at"))
            path = _project_path(name)
            instructions_count, knowledge_count = _project_counts(path)
            merged["instruction_files_count"] = instructions_count
            merged["knowledge_files_count"] = knowledge_count
            state[idx] = merged
            _save_state(state)
            return {"ok": True, "data": merged}

        if action == "delete":
            name = str(payload.get("name") or "")
            project, state, idx = _get_project(name)
            if not project:
                return {"ok": False, "error": "Project not found"}

            path = _project_path(name)
            if path.exists():
                shutil.rmtree(path)
            del state[idx]
            _save_state(state)
            return {"ok": True}

        if action == "activate":
            ctx = _ensure_context(payload.get("context_id"))
            name = str(payload.get("name") or "")
            project, _, _ = _get_project(name)
            if not project:
                return {"ok": False, "error": "Project not found"}
            ctx["project"] = {
                "name": project.get("name"),
                "title": project.get("title"),
                "color": project.get("color", ""),
            }
            return {"ok": True, "data": ctx["project"]}

        if action == "deactivate":
            ctx = _ensure_context(payload.get("context_id"))
            ctx["project"] = None
            return {"ok": True}

        if action == "file_structure":
            name = str(payload.get("name") or "")
            path = _project_path(name)
            if not path.exists():
                return {"ok": False, "error": "Project not found"}
            settings = payload.get("settings") if isinstance(payload, dict) else {}
            max_depth = int((settings or {}).get("max_depth") or 2)
            max_files = int((settings or {}).get("max_files") or 100)
            lines: list[str] = []

            def walk(folder: Path, depth: int, prefix: str = ""):
                if depth > max_depth or len(lines) >= max_files:
                    return
                try:
                    entries = sorted(folder.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
                except Exception:
                    return
                for entry in entries:
                    if len(lines) >= max_files:
                        return
                    lines.append(f"{prefix}{entry.name}{'/' if entry.is_dir() else ''}")
                    if entry.is_dir():
                        walk(entry, depth + 1, prefix + "  ")

            walk(path, 0)
            return {"ok": True, "data": "\n".join(lines)}

        return {"ok": False, "error": f"Unsupported project action: {action}"}

    @app.post("/agents")
    async def agents(payload: dict):
        runtime_profiles: list[dict] = []
        if hasattr(agent, "swarm") and agent.swarm:
            try:
                runtime_profiles = [
                    {
                        "key": p.get("name", ""),
                        "label": p.get("display_name") or p.get("name", ""),
                        "name": p.get("name", ""),
                    }
                    for p in (agent.swarm.list_profiles() or [])
                    if p.get("name")
                ]
            except Exception:
                runtime_profiles = []

        by_key: dict[str, dict] = {}
        for item in [*runtime_profiles, *catalog_agents]:
            key = str(item.get("key") or item.get("name") or "").strip()
            if not key:
                continue
            by_key[key] = {
                "key": key,
                "label": str(item.get("label") or key),
                "name": str(item.get("name") or key),
            }

        merged = sorted(by_key.values(), key=lambda x: x.get("label", "").lower())
        return {"ok": True, "data": merged}

    @app.post("/skills")
    async def skills(payload: dict):
        action = payload.get("action", "list") if isinstance(payload, dict) else "list"

        base_root = Path(__file__).parent.parent
        projects_root = base_root / "data" / "projects"
        profiles_root = base_root / "prompts" / "profiles"

        def _collect_skill_files(project_name: str | None = None, agent_profile: str | None = None) -> list[dict]:
            roots: list[tuple[Path, str]] = [(base_root / "skills", "global")]
            if project_name:
                roots.append((projects_root / project_name / ".a0proj" / "skills", "project"))
            if agent_profile:
                roots.append((profiles_root / agent_profile / "skills", "agent"))

            output: list[dict] = []
            seen: set[str] = set()
            for root, scope in roots:
                if not root.exists():
                    continue

                for md in root.glob("*.md"):
                    if md.name == "SKILL.md":
                        continue
                    key = str(md.resolve())
                    if key in seen:
                        continue
                    seen.add(key)
                    try:
                        text = md.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        text = ""
                    description = ""
                    for line in text.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            description = line[:240]
                            break
                    output.append({
                        "name": md.stem,
                        "path": str(md),
                        "description": description,
                        "scope": scope,
                    })

                for marker in root.rglob("SKILL.md"):
                    folder = marker.parent
                    key = str(marker.resolve())
                    if key in seen:
                        continue
                    seen.add(key)
                    try:
                        text = marker.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        text = ""
                    description = ""
                    for line in text.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            description = line[:240]
                            break
                    output.append({
                        "name": folder.name,
                        "path": str(marker),
                        "description": description,
                        "scope": scope,
                    })

            output.sort(key=lambda item: ((item.get("name") or "").lower(), item.get("path") or ""))
            return output

        if action == "list":
            return {
                "ok": True,
                "data": _collect_skill_files(
                    project_name=payload.get("project_name"),
                    agent_profile=payload.get("agent_profile"),
                ),
            }

        if action == "delete":
            raw = str(payload.get("skill_path") or "")
            if not raw:
                return {"ok": False, "error": "skill_path is required"}
            path = Path(raw).resolve()
            allowed_roots = [
                (base_root / "skills").resolve(),
                (projects_root).resolve(),
                (profiles_root).resolve(),
            ]
            if not any(path == root or root in path.parents for root in allowed_roots):
                return {"ok": False, "error": "Delete blocked: path not in skill roots"}
            if path.name == "SKILL.md" and path.parent == (base_root / "skills"):
                return {"ok": False, "error": "Cannot delete global SKILL.md template"}
            if not path.exists():
                return {"ok": False, "error": "Skill not found"}
            path.unlink()
            return {"ok": True}

        return {"ok": False, "error": f"Unsupported skills action: {action}"}

    @app.post("/skills_import_preview")
    async def skills_import_preview(request: Request):
        return await _skills_import_impl(request, preview_only=True)

    @app.post("/skills_import")
    async def skills_import(request: Request):
        return await _skills_import_impl(request, preview_only=False)

    async def _skills_import_impl(request: Request, preview_only: bool):
        from security.scanner import SecurityScanner

        form = await request.form()
        upload = form.get("skills_file")
        if not upload:
            return {"success": False, "error": "skills_file is required"}

        namespace = str(form.get("namespace") or "").strip()
        namespace = re.sub(r"[^a-zA-Z0-9._-]+", "_", namespace).strip("_")
        conflict = str(form.get("conflict") or "skip").strip().lower()
        if conflict not in {"skip", "overwrite", "rename"}:
            conflict = "skip"

        project_name = str(form.get("project_name") or "").strip()
        agent_profile = str(form.get("agent_profile") or "").strip()
        source_url = str(form.get("source_url") or "").strip()
        review_summary = str(form.get("review_summary") or "").strip()

        trusted_csv = str(compat_settings.get("skills_trusted_sources") or "")
        trusted_sources = [s.strip() for s in trusted_csv.split(",") if s.strip()]
        allow_untrusted = bool(compat_settings.get("skills_allow_untrusted_import", True))
        require_review = bool(compat_settings.get("skills_require_review_summary", True))

        if source_url and trusted_sources and (not allow_untrusted):
            if not any(source_url.startswith(prefix) for prefix in trusted_sources):
                return {
                    "success": False,
                    "error": "Import blocked: source is not trusted by policy",
                }

        if not preview_only and require_review and not review_summary:
            return {
                "success": False,
                "error": "Review summary is required before import",
            }

        base_root = Path(__file__).parent.parent
        projects_root = base_root / "data" / "projects"
        profile_root = base_root / "prompts" / "profiles"

        if project_name:
            target_root = projects_root / project_name / ".a0proj" / "skills"
        elif agent_profile:
            target_root = profile_root / agent_profile / "skills"
        else:
            target_root = base_root / "skills" / "imports"
        target_root.mkdir(parents=True, exist_ok=True)

        scanner = SecurityScanner()
        installed: list[str] = []
        skipped: list[str] = []
        rejected: list[dict] = []

        with tempfile.TemporaryDirectory(prefix="skills_import_") as tmpdir:
            archive_path = Path(tmpdir) / "skills.zip"
            content = await upload.read()
            archive_path.write_bytes(content)

            try:
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(Path(tmpdir) / "unzipped")
            except Exception as exc:
                return {"success": False, "error": f"Invalid zip archive: {exc}"}

            extracted_root = Path(tmpdir) / "unzipped"
            candidates = list(extracted_root.rglob("SKILL.md"))
            if not candidates:
                return {
                    "success": False,
                    "error": "No SKILL.md files found in archive",
                }

            for skill_md in candidates:
                source_dir = skill_md.parent
                raw_name = source_dir.name
                safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", raw_name).strip("_") or "skill"
                if namespace:
                    safe_name = f"{namespace}_{safe_name}"

                skill_text = skill_md.read_text(encoding="utf-8", errors="replace")
                validation = scanner.validate_skill_markdown(skill_text)
                if not validation.get("valid"):
                    rejected.append({
                        "name": raw_name,
                        "reason": f"schema validation failed: {'; '.join(validation.get('errors', []))}",
                    })
                    continue

                injection_scan = scanner.scan_skill_markdown(skill_text, source=str(skill_md))
                if injection_scan.get("blocked"):
                    rejected.append({
                        "name": raw_name,
                        "reason": "security scan blocked: potential prompt-injection patterns",
                    })
                    continue

                destination = target_root / safe_name
                selected_destination = destination
                if destination.exists():
                    if conflict == "skip":
                        skipped.append(raw_name)
                        continue
                    if conflict == "overwrite":
                        selected_destination = destination
                    else:
                        counter = 2
                        while (target_root / f"{safe_name}_{counter}").exists():
                            counter += 1
                        selected_destination = target_root / f"{safe_name}_{counter}"

                installed.append(str(selected_destination.relative_to(target_root)))
                if preview_only:
                    continue

                if selected_destination.exists() and conflict == "overwrite":
                    shutil.rmtree(selected_destination)
                shutil.copytree(source_dir, selected_destination, dirs_exist_ok=False)

        return {
            "success": True,
            "namespace": namespace,
            "imported": installed,
            "imported_count": len(installed),
            "skipped": skipped,
            "skipped_count": len(skipped),
            "rejected": rejected,
            "rejected_count": len(rejected),
            "review_required": require_review,
        }

    @app.post("/skills_export")
    async def skills_export(payload: dict | None = None):
        payload = payload or {}
        project_name = str(payload.get("project_name") or "").strip()
        agent_profile = str(payload.get("agent_profile") or "").strip()

        base_root = Path(__file__).parent.parent
        if project_name:
            source_root = base_root / "data" / "projects" / project_name / ".a0proj" / "skills"
        elif agent_profile:
            source_root = base_root / "prompts" / "profiles" / agent_profile / "skills"
        else:
            source_root = base_root / "skills"

        if not source_root.exists():
            return {"ok": False, "error": "No skills found for selected scope"}

        with tempfile.TemporaryDirectory(prefix="skills_export_") as tmpdir:
            zip_path = Path(tmpdir) / "skills_export.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for marker in source_root.rglob("SKILL.md"):
                    rel = marker.relative_to(source_root)
                    zf.write(marker, arcname=str(rel))
                    for extra in marker.parent.glob("*"):
                        if extra.name == "SKILL.md" or extra.is_dir():
                            continue
                        zf.write(extra, arcname=str(rel.parent / extra.name))
            encoded = base64.b64encode(zip_path.read_bytes()).decode("ascii")

        return {
            "ok": True,
            "filename": f"skills_export_{int(time.time())}.zip",
            "archive_base64": encoded,
        }

    @app.post("/skills_create_from_text")
    async def skills_create_from_text(payload: dict | None = None):
        payload = payload or {}
        title = str(payload.get("title") or "").strip()
        source_text = str(payload.get("source_text") or "").strip()
        install = bool(payload.get("install"))
        project_name = str(payload.get("project_name") or "").strip()
        agent_profile = str(payload.get("agent_profile") or "").strip()

        if not title:
            return {"ok": False, "error": "title is required"}
        if not source_text:
            return {"ok": False, "error": "source_text is required"}

        safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", title.lower()).strip("_") or "new_skill"
        preview = (
            f"# Skill: {title}\n\n"
            "Category: custom\n"
            f"Tags: [{safe_name}]\n\n"
            "## When to Use\n"
            f"Use this skill when the task matches: {title}.\n\n"
            "## Steps\n"
            "1. Review the source notes below.\n"
            "2. Apply the workflow safely and verify outputs.\n"
            "3. Record key results and known limits.\n\n"
            "## Source Notes\n"
            f"{source_text.strip()}\n"
        )

        if not install:
            return {"ok": True, "preview": preview, "name": safe_name}

        base_root = Path(__file__).parent.parent
        if project_name:
            target_root = base_root / "data" / "projects" / project_name / ".a0proj" / "skills"
        elif agent_profile:
            target_root = base_root / "prompts" / "profiles" / agent_profile / "skills"
        else:
            target_root = base_root / "skills" / "imports"
        target_root.mkdir(parents=True, exist_ok=True)

        destination = target_root / safe_name
        counter = 2
        while destination.exists():
            destination = target_root / f"{safe_name}_{counter}"
            counter += 1
        destination.mkdir(parents=True, exist_ok=False)
        marker = destination / "SKILL.md"
        marker.write_text(preview, encoding="utf-8")
        return {"ok": True, "preview": preview, "name": destination.name, "path": str(marker)}

    @app.post("/memory_dashboard")
    async def memory_dashboard(payload: dict | None = None):
        return {"ok": True, "data": {"rows": [], "summary": {}}}

    @app.post("/mcp_servers_status")
    async def mcp_servers_status(payload: dict | None = None):
        if hasattr(agent, "mcp_client") and agent.mcp_client:
            status = agent.mcp_client.get_status()
            servers = []
            if isinstance(status, dict):
                for name, info in (status.get("servers") or {}).items():
                    servers.append({
                        "name": name,
                        "connected": bool((info or {}).get("connected")),
                        "tool_count": len((info or {}).get("tools") or []),
                        "tools": (info or {}).get("tools") or [],
                        "error": (info or {}).get("error", ""),
                    })
            servers.sort(key=lambda s: (s.get("name") or "").lower())
            return {"ok": True, "success": True, "data": status, "status": servers}
        empty = {"servers": {}, "configured": 0, "connected": 0, "total_tools": 0}
        return {"ok": True, "success": True, "data": empty, "status": []}

    @app.post("/mcp_servers_apply")
    async def mcp_servers_apply(payload: dict):
        value = payload.get("mcp_servers") if isinstance(payload, dict) else None
        if isinstance(value, str) and value.strip():
            compat_settings["mcp_servers"] = value
            compat_settings["mcpServers"] = value
        status_resp = await mcp_servers_status(None)
        return {"ok": True, "success": True, "status": status_resp.get("status", [])}

    @app.post("/mcp_server_get_detail")
    async def mcp_server_get_detail(payload: dict):
        server_name = ""
        if isinstance(payload, dict):
            server_name = str(payload.get("server_name") or "")

        detail = {"name": server_name, "connected": False, "tools": [], "tool_count": 0, "error": ""}
        if hasattr(agent, "mcp_client") and agent.mcp_client and server_name:
            status = agent.mcp_client.get_status() or {}
            info = (status.get("servers") or {}).get(server_name) or {}
            tools = info.get("tools") or []
            detail = {
                "name": server_name,
                "connected": bool(info.get("connected")),
                "tools": tools,
                "tool_count": len(tools),
                "error": info.get("error", ""),
            }
        return {"ok": True, "success": True, "data": detail, "detail": detail}

    @app.post("/mcp_server_get_log")
    async def mcp_server_get_log(payload: dict):
        server_name = ""
        if isinstance(payload, dict):
            server_name = str(payload.get("server_name") or "")
        log_lines: list[str] = [f"MCP server: {server_name or 'unknown'}", "No runtime log available in compatibility mode."]
        return {"ok": True, "success": True, "data": log_lines, "log": "\n".join(log_lines)}

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

    @app.post("/resource_hub")
    async def resource_hub(payload: dict | None = None):
        root = Path(__file__).parent.parent

        def list_names(folder: Path, pattern: str, exclude: set[str] | None = None) -> list[dict]:
            exclude = exclude or set()
            output: list[dict] = []
            if not folder.exists():
                return output
            for file in sorted(folder.glob(pattern), key=lambda p: p.name.lower()):
                if file.name in exclude:
                    continue
                output.append({
                    "name": file.name,
                    "path": str(file.relative_to(root)),
                    "size": file.stat().st_size,
                })
            return output

        tasks = []
        if hasattr(agent, "task_board") and agent.task_board:
            for task in agent.task_board.list_all(limit=200):
                d = task.to_dict()
                tasks.append({
                    "id": d.get("id"),
                    "title": d.get("title") or d.get("id"),
                    "status": d.get("status", "unknown"),
                })

        mcp = {"configured": 0, "connected": 0, "total_tools": 0}
        if hasattr(agent, "mcp_client") and agent.mcp_client:
            status = agent.mcp_client.get_status() or {}
            mcp = {
                "configured": status.get("configured", 0),
                "connected": status.get("connected", 0),
                "total_tools": status.get("total_tools", 0),
            }

        return {
            "ok": True,
            "data": {
                "adapters": list_names(root / "adapters", "*.py", {"__init__.py"}),
                "prompts": list_names(root / "prompts", "*.md"),
                "tools": list_names(root / "tools", "*.py", {"__init__.py", "base.py", "response.py"}),
                "skills": list_names(root / "skills", "*.md", {"SKILL.md"}),
                "tasks": tasks,
                "mcp": mcp,
            },
        }

    @app.post("/resource_file")
    async def resource_file(payload: dict):
        root = Path(__file__).parent.parent
        kind = str(payload.get("kind", "")).strip().lower()
        name = str(payload.get("name", "")).strip()

        if not name or "/" in name or "\\" in name or ".." in name:
            return JSONResponse({"error": "Invalid file name"}, status_code=400)

        base_dir_by_kind = {
            "adapters": root / "adapters",
            "prompts": root / "prompts",
            "tools": root / "tools",
            "skills": root / "skills",
        }
        base_dir = base_dir_by_kind.get(kind)
        if not base_dir:
            return JSONResponse({"error": "Unsupported resource kind"}, status_code=400)

        target = base_dir / name
        if not target.exists() or not target.is_file():
            return JSONResponse({"error": "Resource not found"}, status_code=404)

        try:
            content = target.read_text(encoding="utf-8")
            return {"ok": True, "kind": kind, "name": name, "content": content}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

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
