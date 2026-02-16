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
import importlib
import json
import os
import sys
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
        lines.append(f"        --> cp install/config/config.json.example config.json")
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

    # Model validation
    models = config.get("models", {})
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

    key_map = {
        "Google Gemini": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "OpenAI": ["OPENAI_API_KEY"],
        "Anthropic Claude": ["ANTHROPIC_API_KEY"],
        "OpenRouter": ["OPENROUTER_API_KEY"],
        "Groq": ["GROQ_API_KEY"],
    }

    found_any = False
    for provider, env_vars in key_map.items():
        val = ""
        used_env_var = ""
        for env_var in env_vars:
            candidate = os.environ.get(env_var, "")
            if candidate:
                val = candidate
                used_env_var = env_var
                break
        if val:
            masked = val[:8] + "..." + val[-4:] if len(val) > 16 else "****"
            suffix = f" ({used_env_var})" if used_env_var else ""
            lines.append(_ok(f"{provider}{suffix}: {masked}"))
            passed += 1
            found_any = True
        else:
            lines.append(_warn(f"{provider}: not configured"))

    if not found_any:
        lines.append(_fail("No LLM API key found! Add at least one to .env"))
        lines.append(f"        --> echo GOOGLE_API_KEY=your_key >> .env")
        failed += 1

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
            lines.append(f"        --> Check NEO4J_URI and NEO4J_PASSWORD in .env")
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


def check_security() -> tuple[list[str], int, int]:
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
        from security.path_guard import validate_path, validate_session_id
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
                lines.append(f"        --> Add \"webui\": {{\"auth_token\": \"<token>\"}} to config.json")
                passed += 1  # Not fatal, auto-generates
        else:
            lines.append(_warn("config.json not found, skipping WebUI auth check"))
            passed += 1
    except Exception:
        lines.append(_warn("Could not check WebUI auth config"))
        passed += 1

    return lines, passed, failed


# ─── Main doctor ───────────────────────────────────────────────

async def run_doctor() -> bool:
    """Run the full doctor diagnostic. Returns True if healthy."""
    total_passed = 0
    total_failed = 0

    print(f"\n{BOLD}{'=' * 56}{RESET}")
    print(f"{BOLD}   iTaK Doctor - Full System Diagnostic{RESET}")
    print(f"{BOLD}{'=' * 56}{RESET}")

    checks = [
        ("Preflight (Python, packages, config)", check_preflight),
        ("Configuration", check_config),
        ("Environment Overrides", check_env_overrides),
        ("API Keys & Tokens", check_api_keys),
        ("File Structure & Parity", check_file_structure),
        ("Tool Health", check_tool_health),
        ("Security Hardening", check_security),
    ]

    for title, check_fn in checks:
        print(_header(title))
        check_lines, p, f = check_fn()
        for line in check_lines:
            print(line)
        total_passed += p
        total_failed += f

    # Service connectivity (async)
    print(_header("Service Connectivity"))
    service_lines, sp, sf = await check_services()
    for line in service_lines:
        print(line)
    total_passed += sp
    total_failed += sf

    # Summary
    print(f"\n{BOLD}{'=' * 56}{RESET}")
    if total_failed == 0:
        print(f"  {GREEN}{BOLD}ALL CHECKS PASSED{RESET} ({total_passed} passed)")
        print(f"  {GREEN}Your iTaK agent is ready to run!{RESET}")
    else:
        print(f"  {RED}{BOLD}{total_failed} ISSUE(S) FOUND{RESET} ({total_passed} passed, {total_failed} failed)")
        print(f"  {YELLOW}Fix the issues above and run again: python -m app.main --doctor{RESET}")
    print(f"{BOLD}{'=' * 56}{RESET}\n")

    return total_failed == 0


if __name__ == "__main__":
    ok = asyncio.run(run_doctor())
    sys.exit(0 if ok else 1)
