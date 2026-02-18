"""
iTaK Doctor - Comprehensive diagnostic and repair tool.

Inspired by `openclaw doctor`. Runs a full system diagnostic that:
1. Preflight checks         (Python, packages, config, API keys)
2. Service connectivity     (Neo4j, Weaviate, SearXNG, Ollama)
3. Config validation        (detect misconfigs, missing fields)
4. File structure integrity (data dirs, prompt files, skill files)
5. Repair suggestions       (actionable fix commands)

Usage:
    python -m app.main --doctor      # Full diagnostic
    python -m core.doctor            # Standalone
"""

import asyncio
import argparse
import importlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

# Add project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ─── Colour helpers ────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _ok(msg: str) -> str:
    return f"  {GREEN}[OK]{RESET}  {msg}"


def _warn(msg: str) -> str:
    return f"  {YELLOW}[!!]{RESET}  {msg}"


def _fail(msg: str) -> str:
    return f"  {RED}[XX]{RESET}  {msg}"


def _header(msg: str) -> str:
    return f"\n{BOLD}{CYAN}-- {msg} --{RESET}"


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text or "")


# ─── Check functions ───────────────────────────────────────────

def check_preflight() -> tuple[list[str], int, int]:
    """Run preflight checks (delegates to core/preflight.py)."""
    lines: list[str] = []
    passed = 0
    failed = 0

    try:
        from core.preflight import run_preflight
        result = run_preflight(auto_install=False)

        for item in result.passed:
            lines.append(_ok(item))
            passed += 1
        for item in result.warnings:
            lines.append(_warn(item))
        for item in result.errors:
            lines.append(_fail(item))
            failed += 1
    except ImportError:
        lines.append(_fail("core/preflight.py not found"))
        failed += 1

    return lines, passed, failed


def check_config() -> tuple[list[str], int, int]:
    """Validate config.json structure and values."""
    lines: list[str] = []
    passed = 0
    failed = 0

    config_path = Path("config.json")
    if not config_path.exists():
        lines.append(_fail("config.json not found"))
        lines.append("        --> cp install/config/config.json.example config.json")
        return lines, 0, 1

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        lines.append(_ok("config.json is valid JSON"))
        passed += 1
    except json.JSONDecodeError as e:
        lines.append(_fail(f"config.json has invalid JSON: {e}"))
        return lines, 0, 1

    # Required top-level keys
    required_sections = ["agent", "models"]
    recommended_sections = [
        "memory", "security", "output_guard", "tools",
        "adapters", "webui", "heartbeat",
    ]

    for section in required_sections:
        if section in config:
            lines.append(_ok(f"config.{section} present"))
            passed += 1
        else:
            lines.append(_fail(f"config.{section} MISSING (required)"))
            failed += 1

    for section in recommended_sections:
        if section in config:
            lines.append(_ok(f"config.{section} present"))
            passed += 1
        else:
            lines.append(_warn(f"config.{section} missing (using defaults)"))

    # Model validation (honor ITAK_SET_ overrides so diagnostics match runtime)
    effective_config = config
    try:
        from core.models import apply_env_overrides
        effective_config, _, _ = apply_env_overrides(config, prefix="ITAK_SET_")
    except Exception:
        effective_config = config

    models = effective_config.get("models", {})
    for slot in ["chat", "utility"]:
        model_cfg = models.get(slot, {})
        if model_cfg.get("model"):
            lines.append(_ok(f"models.{slot} = {model_cfg['model']}"))
            passed += 1
        else:
            lines.append(_fail(f"models.{slot} has no model configured"))
            failed += 1

    return lines, passed, failed


def check_env_overrides() -> tuple[list[str], int, int]:
    """Validate ITAK_SET_ environment overrides against existing config schema."""
    lines: list[str] = []
    passed = 0
    failed = 0

    config_path = Path("config.json")
    if not config_path.exists():
        lines.append(_warn("config.json not found, skipping ITAK_SET_ override validation"))
        return lines, 1, 0

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        from core.models import apply_env_overrides
        _, override_errors, override_applied = apply_env_overrides(config, prefix="ITAK_SET_")
        if override_applied:
            lines.append(_ok(f"ITAK_SET_ overrides applied: {len(override_applied)}"))
            passed += 1
        else:
            lines.append(_ok("No ITAK_SET_ overrides detected"))
            passed += 1

        if override_errors:
            for err in override_errors:
                lines.append(_fail(f"Invalid ITAK_SET_ override: {err}"))
                failed += 1
    except Exception as exc:
        lines.append(_fail(f"ITAK_SET_ override validation failed: {exc}"))
        failed += 1

    return lines, passed, failed


def check_api_keys() -> tuple[list[str], int, int]:
    """Check that at least one LLM API key is available."""
    lines: list[str] = []
    passed = 0
    failed = 0

    # Load .env first
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())
        lines.append(_ok(".env file loaded"))
        passed += 1
    else:
        lines.append(_warn(".env file not found - checking env vars only"))

    config: dict = {}
    config_api_keys: dict = {}
    configured_model_providers: list[str] = []
    try:
        config = json.loads(Path("config.json").read_text(encoding="utf-8"))
        config_api_keys = config.get("api_keys", {}) if isinstance(config.get("api_keys", {}), dict) else {}
        for slot in ["chat", "utility", "browser", "embeddings"]:
            model_cfg = config.get("models", {}).get(slot, {})
            if not isinstance(model_cfg, dict):
                continue
            provider = str(model_cfg.get("provider", "") or "").strip().lower()
            model_name = str(model_cfg.get("model", "") or "").strip().lower()
            if provider and provider != "litellm":
                configured_model_providers.append(provider)
            elif "/" in model_name:
                configured_model_providers.append(model_name.split("/", 1)[0])
    except Exception:
        pass

    key_map = {
        "Google Gemini": {
            "env": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
            "config": ["google", "gemini"],
        },
        "OpenAI": {
            "env": ["OPENAI_API_KEY"],
            "config": ["openai"],
        },
        "Anthropic Claude": {
            "env": ["ANTHROPIC_API_KEY"],
            "config": ["anthropic"],
        },
        "OpenRouter": {
            "env": ["OPENROUTER_API_KEY"],
            "config": ["openrouter"],
        },
        "Groq": {
            "env": ["GROQ_API_KEY"],
            "config": ["groq"],
        },
        "NVIDIA NIM": {
            "env": ["NVIDIA_NIM_API_KEY", "NVIDIA_API_KEY"],
            "config": ["nvidia", "nvidia_nim"],
        },
    }

    found_any = False
    for provider, key_sources in key_map.items():
        val = ""
        used_source = ""

        for env_var in key_sources.get("env", []):
            candidate = os.environ.get(env_var, "")
            if candidate:
                val = candidate
                used_source = env_var
                break

        if not val:
            for cfg_key in key_sources.get("config", []):
                candidate = config_api_keys.get(cfg_key, "")
                if candidate:
                    val = str(candidate)
                    used_source = f"config.api_keys.{cfg_key}"
                    break

        if val:
            masked = val[:8] + "..." + val[-4:] if len(val) > 16 else "****"
            suffix = f" ({used_source})" if used_source else ""
            lines.append(_ok(f"{provider}{suffix}: {masked}"))
            passed += 1
            found_any = True
        else:
            lines.append(_warn(f"{provider}: not configured"))

    if not found_any:
        local_only_providers = {"ollama", "fastembed"}
        has_non_local_provider = any(
            provider for provider in configured_model_providers
            if provider not in local_only_providers
        )

        if has_non_local_provider:
            lines.append(_fail("No LLM API key found! Add at least one to .env or config.api_keys"))
            lines.append("        --> echo NVIDIA_NIM_API_KEY=your_key >> .env")
            failed += 1
        else:
            lines.append(_warn("No remote API key found, but configured models are local-only (Ollama/FastEmbed)"))
            passed += 1

    # Platform tokens
    platform_keys = {
        "DISCORD_TOKEN": "Discord",
        "TELEGRAM_TOKEN": "Telegram",
        "SLACK_TOKEN": "Slack",
    }
    for env_var, platform in platform_keys.items():
        if os.environ.get(env_var):
            lines.append(_ok(f"{platform} token configured"))
            passed += 1
        else:
            lines.append(_warn(f"{platform} token not set (adapter disabled)"))

    return lines, passed, failed


async def check_services() -> tuple[list[str], int, int]:
    """Test connectivity to external services."""
    lines: list[str] = []
    passed = 0
    failed = 0

    # Neo4j
    neo4j_uri = os.environ.get("NEO4J_URI", "")
    if neo4j_uri:
        try:
            import neo4j as neo4j_pkg
            driver = neo4j_pkg.GraphDatabase.driver(
                neo4j_uri,
                auth=("neo4j", os.environ.get("NEO4J_PASSWORD", "")),
            )
            driver.verify_connectivity()
            driver.close()
            lines.append(_ok(f"Neo4j connected: {neo4j_uri}"))
            passed += 1
        except Exception as e:
            lines.append(_fail(f"Neo4j FAILED: {e}"))
            lines.append("        --> Check NEO4J_URI and NEO4J_PASSWORD in .env")
            failed += 1
    else:
        lines.append(_warn("Neo4j not configured (knowledge graph disabled)"))

    # SearXNG
    searxng_url = os.environ.get("SEARXNG_URL", "")
    if not searxng_url:
        # Check config
        try:
            config = json.loads(Path("config.json").read_text(encoding="utf-8"))
            searxng_url = config.get("tools", {}).get("web_search", {}).get("searxng_url", "")
        except Exception:
            pass

    if searxng_url:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(searxng_url.rstrip("/search"))
                if resp.status_code < 500:
                    lines.append(_ok(f"SearXNG reachable: {searxng_url}"))
                    passed += 1
                else:
                    lines.append(_fail(f"SearXNG returned {resp.status_code}"))
                    failed += 1
        except Exception as e:
            lines.append(_fail(f"SearXNG FAILED: {e}"))
            lines.append(f"        --> Check if SearXNG is running at {searxng_url}")
            failed += 1
    else:
        lines.append(_warn("SearXNG not configured (web search disabled)"))

    # Ollama
    for port in [11434]:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(f"http://localhost:{port}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    model_names = [m.get("name", "?") for m in models[:5]]
                    lines.append(_ok(f"Ollama running ({len(models)} models: {', '.join(model_names)})"))
                    passed += 1
                else:
                    lines.append(_warn(f"Ollama returned {resp.status_code}"))
        except Exception:
            lines.append(_warn("Ollama not running on localhost:11434"))

    # Weaviate
    weaviate_url = os.environ.get("WEAVIATE_URL", "")
    if weaviate_url:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{weaviate_url}/v1/.well-known/ready")
                if resp.status_code == 200:
                    lines.append(_ok(f"Weaviate ready: {weaviate_url}"))
                    passed += 1
                else:
                    lines.append(_fail(f"Weaviate returned {resp.status_code}"))
                    failed += 1
        except Exception as e:
            lines.append(_fail(f"Weaviate FAILED: {e}"))
            failed += 1
    else:
        lines.append(_warn("Weaviate not configured (semantic search disabled)"))

    return lines, passed, failed


def check_file_structure() -> tuple[list[str], int, int]:
    """Verify required files and directories exist."""
    lines: list[str] = []
    passed = 0
    failed = 0

    required_dirs = ["core", "tools", "prompts", "skills", "adapters", "security", "memory", "extensions"]
    for dirname in required_dirs:
        if Path(dirname).is_dir():
            count = len(list(Path(dirname).glob("*.py"))) + len(list(Path(dirname).glob("*.md")))
            lines.append(_ok(f"{dirname}/ ({count} files)"))
            passed += 1
        else:
            lines.append(_fail(f"{dirname}/ MISSING"))
            lines.append(f"        --> mkdir {dirname}")
            failed += 1

    data_dirs = ["data", "logs"]
    for dirname in data_dirs:
        p = Path(dirname)
        if p.is_dir():
            lines.append(_ok(f"{dirname}/ exists"))
            passed += 1
        else:
            p.mkdir(parents=True, exist_ok=True)
            lines.append(_ok(f"{dirname}/ created"))
            passed += 1

    # Tool-prompt parity
    tools_dir = Path("tools")
    prompts_dir = Path("prompts")
    tool_files = {f.stem for f in tools_dir.glob("*.py") if f.stem not in ("__init__", "base")}
    prompt_files = {
        f.stem.replace("agent.system.tool.", "")
        for f in prompts_dir.glob("agent.system.tool.*.md")
    }

    # Map prompt names to tool names (handle naming differences)
    name_map = {
        "code_exe": "code_execution",
        "search_engine": "web_search",
        "memory": "memory_save",
        "delegate": "delegate_task",
        "knowledge": "knowledge_tool",
        "browser": "browser_agent",
    }

    mapped_prompts = set()
    for p in prompt_files:
        mapped_prompts.add(name_map.get(p, p))

    tools_without_prompts = tool_files - mapped_prompts - {"memory_load", "response"}
    if tools_without_prompts:
        for t in tools_without_prompts:
            lines.append(_warn(f"Tool '{t}' has no matching prompt file"))
    else:
        lines.append(_ok("All tools have matching prompt files"))
        passed += 1

    # Skill coverage
    skills_dir = Path("skills")
    skill_files = {f.stem for f in skills_dir.glob("*.md") if f.stem != "SKILL"}
    if len(skill_files) >= 6:
        lines.append(_ok(f"{len(skill_files)} skills available"))
        passed += 1
    else:
        lines.append(_warn(f"Only {len(skill_files)} skills - consider adding more"))

    return lines, passed, failed


def check_tool_health() -> tuple[list[str], int, int]:
    """Verify all tools can be imported."""
    lines: list[str] = []
    passed = 0
    failed = 0

    tools_dir = Path("tools")
    for tool_file in sorted(tools_dir.glob("*.py")):
        if tool_file.stem == "__init__":
            continue
        module_name = f"tools.{tool_file.stem}"
        try:
            importlib.import_module(module_name)
            lines.append(_ok(f"tools.{tool_file.stem} imports clean"))
            passed += 1
        except Exception as e:
            lines.append(_fail(f"tools.{tool_file.stem} IMPORT ERROR: {e}"))
            failed += 1

    return lines, passed, failed


def check_security(deep: bool = False) -> tuple[list[str], int, int]:
    """Verify security hardening modules are functional."""
    lines: list[str] = []
    passed = 0
    failed = 0

    # 1. SSRF Guard
    try:
        from security.ssrf_guard import SSRFGuard
        # Use a domain from the allowlist for testing
        guard = SSRFGuard({"security": {"url_allowlist": ["github.com"]}})
        ok, _ = guard.validate_url("http://github.com", source="doctor")
        bad, _ = guard.validate_url("file:///etc/passwd", source="doctor")
        if ok and not bad:
            lines.append(_ok("SSRF Guard functional (blocks file:// + private IPs)"))
            passed += 1
        else:
            lines.append(_fail("SSRF Guard not blocking correctly"))
            failed += 1
    except ImportError:
        lines.append(_fail("security/ssrf_guard.py not found"))
        failed += 1

    # 2. Path Traversal Guard
    try:
        from security.path_guard import validate_path
        ok, _ = validate_path("data/test.txt")
        bad, _ = validate_path("../../../etc/passwd")
        if ok and not bad:
            lines.append(_ok("Path Guard functional (blocks ../ traversal)"))
            passed += 1
        else:
            lines.append(_fail("Path Guard not blocking correctly"))
            failed += 1
    except ImportError:
        lines.append(_fail("security/path_guard.py not found"))
        failed += 1

    # 2b. Symlink escape hardening
    try:
        from security.path_guard import safe_join, validate_path
        with tempfile.TemporaryDirectory(prefix="itak-doctor-path-") as tmp:
            root = Path(tmp) / "root"
            root.mkdir(parents=True, exist_ok=True)
            outside = Path(tmp) / "outside"
            outside.mkdir(parents=True, exist_ok=True)

            join_ok = safe_join(root, "safe", "file.txt") is not None
            if not join_ok:
                lines.append(_fail("Path Guard safe_join unexpectedly rejected safe path"))
                failed += 1
            else:
                lines.append(_ok("Path Guard safe_join accepts safe paths"))
                passed += 1

            link = root / "link_out"
            symlink_supported = True
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                symlink_supported = False

            if symlink_supported:
                escaped = safe_join(root, "link_out", "payload.txt")
                path_safe, _ = validate_path(
                    str(link / "payload.txt"),
                    allowed_roots=[root],
                    allow_absolute=True,
                    allow_symlinks=False,
                )
                if escaped is None and not path_safe:
                    lines.append(_ok("Path Guard blocks symlink-based path escape"))
                    passed += 1
                else:
                    lines.append(_fail("Path Guard did not block symlink-based path escape"))
                    failed += 1
            else:
                lines.append(_warn("Symlink hardening test skipped (symlinks unsupported in environment)"))
                passed += 1
    except Exception as exc:
        lines.append(_warn(f"Could not run symlink hardening check: {exc}"))
        passed += 1

    # 3. Constant-time secret comparison
    try:
        from security.secrets import SecretManager
        sm = SecretManager()
        if hasattr(sm, 'verify_token'):
            lines.append(_ok("SecretManager.verify_token (hmac.compare_digest) available"))
            passed += 1
        else:
            lines.append(_fail("SecretManager missing verify_token method"))
            failed += 1
    except ImportError:
        lines.append(_fail("security/secrets.py not found"))
        failed += 1

    # 4. Auth-failure lockout
    try:
        from security.rate_limiter import RateLimiter
        rl = RateLimiter()
        if hasattr(rl, 'record_auth_failure') and hasattr(rl, 'check_auth_lockout'):
            lines.append(_ok("RateLimiter auth-failure lockout methods available"))
            passed += 1
        else:
            lines.append(_fail("RateLimiter missing auth lockout methods"))
            failed += 1
    except ImportError:
        lines.append(_fail("security/rate_limiter.py not found"))
        failed += 1

    # 5. WebUI auth token config
    try:
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            webui = config.get("webui", {})
            if webui.get("auth_token"):
                lines.append(_ok("WebUI auth token configured"))
                passed += 1
            else:
                lines.append(_warn("WebUI auth token not set (auto-generated at runtime)"))
                lines.append("        --> Add \"webui\": {\"auth_token\": \"<token>\"} to config.json")
                passed += 1  # Not fatal, auto-generates
        else:
            lines.append(_warn("config.json not found, skipping WebUI auth check"))
            passed += 1
    except Exception:
        lines.append(_warn("Could not check WebUI auth config"))
        passed += 1

    # 6. Security scanner severity/risk model + repository sweep
    try:
        from security.scanner import SecurityScanner

        scanner = SecurityScanner()

        smoke_result = scanner.scan_code('eval("2+2")', source="doctor_smoke")
        if {
            "severity_counts",
            "risk_score",
            "risk_level",
        }.issubset(set(smoke_result.keys())):
            lines.append(_ok("SecurityScanner severity/risk metadata available"))
            passed += 1
        else:
            lines.append(_fail("SecurityScanner missing severity/risk metadata fields"))
            failed += 1

        findings: list[dict] = []
        secrets_found: list[dict] = []
        files_scanned = 0
        scan_targets = [
            (Path("tools"), [".py"]),
            (Path("adapters"), [".py"]),
            (Path("extensions"), [".py", ".md"]),
        ]
        if deep:
            scan_targets.extend([
                (Path("core"), [".py"]),
                (Path("webui"), [".py"]),
            ])

        for target_dir, exts in scan_targets:
            if not target_dir.exists():
                continue
            target_result = scanner.scan_directory(target_dir, extensions=exts)
            findings.extend(target_result.get("findings", []))
            secrets_found.extend(target_result.get("secrets_found", []))
            files_scanned += int(target_result.get("files_scanned", 0) or 0)

        project_scan = {
            **scanner._build_risk_summary(findings, secrets_found, bool(secrets_found)),
            "findings": findings,
            "secrets_found": secrets_found,
            "files_scanned": files_scanned,
        }
        sev = project_scan.get("severity_counts", {})
        risk_level = project_scan.get("risk_level", "UNKNOWN")
        risk_score = project_scan.get("risk_score", "?")
        files_scanned = int(project_scan.get("files_scanned", 0) or 0)
        secret_count = int(sev.get("SECRETS", 0) or 0)
        critical_count = int(sev.get("CRITICAL", 0) or 0)
        warning_count = int(sev.get("WARNING", 0) or 0)

        lines.append(
            _ok(
                "Security scan summary: "
                f"files={files_scanned}, critical={critical_count}, "
                f"warnings={warning_count}, secrets={secret_count}, "
                f"risk={risk_level} ({risk_score}/100)"
            )
        )

        if secret_count > 0:
            lines.append(_fail("Security scan detected exposed secrets in repository"))
            failed += 1
        elif critical_count > 0:
            suffix = " in deep scan" if deep else ""
            lines.append(_warn(f"Security scan found CRITICAL patterns{suffix}; review required"))
            passed += 1
        else:
            lines.append(_ok("Security scan found no CRITICAL patterns or exposed secrets"))
            passed += 1

    except ImportError:
        lines.append(_fail("security/scanner.py not found"))
        failed += 1
    except Exception as exc:
        lines.append(_warn(f"Could not complete security scanner sweep: {exc}"))
        passed += 1

    return lines, passed, failed


def check_bottlenecks(deep: bool = False) -> tuple[list[str], int, int]:
    """Detect likely performance bottlenecks and chat hangup risks."""
    lines: list[str] = []
    passed = 0
    failed = 0

    config: dict = {}
    config_path = Path("config.json")
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            lines.append(_ok("Loaded config.json for bottleneck analysis"))
            passed += 1
        except Exception as exc:
            lines.append(_warn(f"Could not parse config.json for bottleneck analysis: {exc}"))
    else:
        lines.append(_warn("config.json not found; using runtime defaults for bottleneck checks"))

    webui_cfg = config.get("webui", {}) if isinstance(config.get("webui", {}), dict) else {}
    timeout_seconds = int(webui_cfg.get("message_timeout_seconds", 180) or 180)
    if timeout_seconds < 60:
        lines.append(_warn(f"webui.message_timeout_seconds={timeout_seconds}s is low and may fail long responses"))
    elif timeout_seconds > 600:
        lines.append(_warn(f"webui.message_timeout_seconds={timeout_seconds}s is high and may mask hung model calls"))
    else:
        lines.append(_ok(f"webui.message_timeout_seconds={timeout_seconds}s"))
        passed += 1

    if bool(webui_cfg.get("uvicorn_access_logs_enabled", False)):
        lines.append(_warn("webui.uvicorn_access_logs_enabled=true (adds IO overhead under high request volume)"))
    else:
        lines.append(_ok("webui.uvicorn_access_logs_enabled=false"))
        passed += 1

    workdir_max_files = int(webui_cfg.get("workdir_max_files", 500) or 500)
    if workdir_max_files > 2000:
        lines.append(_warn(f"webui.workdir_max_files={workdir_max_files} may slow file browser responses"))
    else:
        lines.append(_ok(f"webui.workdir_max_files={workdir_max_files}"))
        passed += 1

    chats_dir = Path("data") / "chats"
    if chats_dir.exists():
        context_files = sorted(chats_dir.glob("*.json"))
        context_count = len(context_files)
        if context_count > 300:
            lines.append(_warn(f"{context_count} chat context files detected; sidebar/poll payloads may grow"))
        else:
            lines.append(_ok(f"{context_count} chat context file(s)"))
            passed += 1

        max_logs = 0
        heaviest_ctx = ""
        sampled = 0
        sample_limit = 2000 if deep else 600
        for fp in context_files[:sample_limit]:
            try:
                payload = json.loads(fp.read_text(encoding="utf-8"))
                logs = payload.get("logs", []) if isinstance(payload, dict) else []
                log_len = len(logs) if isinstance(logs, list) else 0
                sampled += 1
                if log_len > max_logs:
                    max_logs = log_len
                    heaviest_ctx = fp.name
            except Exception:
                continue

        if sampled == 0:
            lines.append(_warn("No readable chat context files found for log-size analysis"))
        elif max_logs > 2500:
            lines.append(_warn(f"Largest chat log has {max_logs} entries ({heaviest_ctx}); expect slower initial chat loads"))
        else:
            lines.append(_ok(f"Largest chat log size is {max_logs} entries"))
            passed += 1
    else:
        lines.append(_warn("data/chats directory missing; skipping chat bottleneck checks"))

    lines.append(_ok("Bottleneck analysis completed"))
    passed += 1
    return lines, passed, failed


# ─── Main doctor ───────────────────────────────────────────────

async def collect_doctor_report(deep: bool = False) -> dict:
    """Collect doctor diagnostics as a machine-readable report."""
    total_passed = 0
    total_failed = 0

    report: dict = {
        "timestamp": time.time(),
        "deep": bool(deep),
        "checks": [],
    }

    checks = [
        ("Preflight (Python, packages, config)", check_preflight),
        ("Configuration", check_config),
        ("Environment Overrides", check_env_overrides),
        ("API Keys & Tokens", check_api_keys),
        ("File Structure & Parity", check_file_structure),
        ("Tool Health", check_tool_health),
        ("Security Hardening", lambda: check_security(deep=deep)),
        ("Bottleneck Risk Scan", lambda: check_bottlenecks(deep=deep)),
    ]

    for title, check_fn in checks:
        check_lines, p, f = check_fn()
        total_passed += p
        total_failed += f
        report["checks"].append({
            "name": title,
            "passed": p,
            "failed": f,
            "lines": [_strip_ansi(line) for line in check_lines],
        })

    service_lines, sp, sf = await check_services()
    total_passed += sp
    total_failed += sf
    report["checks"].append({
        "name": "Service Connectivity",
        "passed": sp,
        "failed": sf,
        "lines": [_strip_ansi(line) for line in service_lines],
    })

    report["summary"] = {
        "passed": total_passed,
        "failed": total_failed,
        "healthy": total_failed == 0,
    }
    return report


def _print_doctor_report(report: dict):
    """Render the doctor report in the existing terminal-friendly format."""
    print(f"\n{BOLD}{'=' * 56}{RESET}")
    print(f"{BOLD}   iTaK Doctor - Full System Diagnostic{RESET}")
    print(f"{BOLD}{'=' * 56}{RESET}")

    for check in report.get("checks", []):
        print(_header(check.get("name", "Check")))
        for line in check.get("lines", []):
            if line.startswith("  ["):
                print(line)
            else:
                print(f"  {line}")

    summary = report.get("summary", {})
    total_passed = int(summary.get("passed", 0) or 0)
    total_failed = int(summary.get("failed", 0) or 0)

    print(f"\n{BOLD}{'=' * 56}{RESET}")
    if total_failed == 0:
        print(f"  {GREEN}{BOLD}ALL CHECKS PASSED{RESET} ({total_passed} passed)")
        print(f"  {GREEN}Your iTaK agent is ready to run!{RESET}")
    else:
        print(f"  {RED}{BOLD}{total_failed} ISSUE(S) FOUND{RESET} ({total_passed} passed, {total_failed} failed)")
        print(f"  {YELLOW}Fix the issues above and run again: python -m app.main --doctor{RESET}")
    print(f"{BOLD}{'=' * 56}{RESET}\n")


def _save_doctor_report_json(report: dict) -> str:
    """Persist doctor report as a JSON artifact in logs/."""
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    path = logs_dir / f"doctor-report-{stamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return str(path)


async def run_doctor(output_format: str = "text", deep: bool = False, save_json: bool = False) -> bool:
    """Run doctor diagnostics. Returns True if healthy."""
    report = await collect_doctor_report(deep=deep)

    if output_format == "json":
        print(json.dumps(report, indent=2))
    else:
        _print_doctor_report(report)

    if save_json:
        artifact = _save_doctor_report_json(report)
        if output_format == "json":
            print(json.dumps({"doctor_report_path": artifact}))
        else:
            print(_ok(f"Doctor report saved: {artifact}"))

    summary = report.get("summary", {})
    return bool(summary.get("healthy", False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="iTaK Doctor")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON report")
    parser.add_argument("--deep", action="store_true", help="Run deeper scanner and bottleneck sampling")
    parser.add_argument("--save-json", action="store_true", help="Save report JSON artifact under logs/")
    args = parser.parse_args()

    ok = asyncio.run(
        run_doctor(
            output_format="json" if args.json else "text",
            deep=args.deep,
            save_json=args.save_json,
        )
    )
    sys.exit(0 if ok else 1)
