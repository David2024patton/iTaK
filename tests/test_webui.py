"""
iTaK - WebUI endpoint & auth connectivity tests.
Verifies that the dashboard can reach all API endpoints when using the correct auth token.
"""

import time
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient


def _make_agent(token="test-secret-token"):
    """Create a minimal mock agent for WebUI tests."""
    agent = MagicMock()
    agent.config = {
        "webui": {"auth_token": token},
    }
    agent._start_time = time.time()
    agent.total_iterations = 5
    agent.tools = []
    agent.heartbeat = None
    agent.memory = None
    agent.rate_limiter = None
    agent.sub_agents = None
    agent.task_board = None
    agent.mcp_client = None
    agent.self_heal = None
    agent.webhooks = None
    agent.swarm = None
    agent.user_registry = None
    agent.presence = None
    agent.media = None
    agent.mcp_server = None
    agent.progress = None
    agent.logger = MagicMock()
    agent.logger.query = MagicMock(return_value=[])
    return agent


@pytest.fixture
def client():
    """Create a TestClient with a mock agent."""
    from webui.server import create_app
    agent = _make_agent()
    app = create_app(agent)
    return TestClient(app)


TOKEN = "test-secret-token"
AUTH_HEADER = {"Authorization": f"Bearer {TOKEN}"}


class TestWebUIAuth:
    """Verify that auth middleware works correctly."""

    def test_health_no_auth_needed(self, client):
        """Health endpoint should be accessible without auth."""
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_stats_requires_auth(self, client):
        """Stats endpoint should reject unauthenticated requests."""
        res = client.get("/api/stats")
        assert res.status_code == 401

    def test_stats_with_auth(self, client):
        """Stats endpoint should accept valid auth token."""
        res = client.get("/api/stats", headers=AUTH_HEADER)
        assert res.status_code == 200
        data = res.json()
        assert "uptime_seconds" in data
        assert "tools_loaded" in data

    def test_wrong_token_rejected(self, client):
        """Wrong token should be rejected."""
        res = client.get("/api/stats", headers={"Authorization": "Bearer wrong-token"})
        assert res.status_code == 401


class TestWebUIEndpoints:
    """Verify all dashboard-connected API endpoints respond correctly."""

    def test_logs(self, client):
        res = client.get("/api/logs?limit=10", headers=AUTH_HEADER)
        assert res.status_code == 200
        assert "logs" in res.json()

    def test_memory_search(self, client):
        res = client.get("/api/memory/search?query=test", headers=AUTH_HEADER)
        assert res.status_code == 200
        assert "results" in res.json()

    def test_tools(self, client):
        res = client.get("/api/tools", headers=AUTH_HEADER)
        assert res.status_code == 200
        assert "tools" in res.json()

    def test_tasks_list(self, client):
        res = client.get("/api/tasks?limit=50", headers=AUTH_HEADER)
        assert res.status_code == 200
        assert "tasks" in res.json()

    def test_config(self, client):
        res = client.get("/api/config", headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_mcp_status(self, client):
        res = client.get("/api/mcp/status", headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_self_heal_stats(self, client):
        res = client.get("/api/self-heal/stats", headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_subsystems(self, client):
        res = client.get("/api/subsystems", headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_webhooks_stats(self, client):
        res = client.get("/api/webhooks/stats", headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_swarm_stats(self, client):
        res = client.get("/api/swarm/stats", headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_swarm_profiles(self, client):
        res = client.get("/api/swarm/profiles", headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_users(self, client):
        res = client.get("/api/users", headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_user_stats(self, client):
        res = client.get("/api/users/stats", headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_presence(self, client):
        res = client.get("/api/presence", headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_media_stats(self, client):
        res = client.get("/api/media/stats", headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_static_index_no_auth(self, client):
        """Static files should be served without auth."""
        res = client.get("/")
        assert res.status_code == 200
        assert "iTaK" in res.text


class TestSettingsParity:
    """Guard against frontend/backend settings drift."""

    @staticmethod
    def _collect_frontend_settings_keys() -> tuple[set[str], set[str]]:
        root = Path(__file__).resolve().parents[1]
        settings_dir = root / "webui" / "static" / "components" / "settings"

        used_settings_keys: set[str] = set()
        used_additional_keys: set[str] = set()

        settings_patterns = [
            re.compile(r"\$store\.settings\.settings\.([a-zA-Z_][a-zA-Z0-9_]*)"),
            re.compile(r"settingsStore\.settings\?\.([a-zA-Z_][a-zA-Z0-9_]*)"),
            re.compile(r"settingsStore\.settings\.([a-zA-Z_][a-zA-Z0-9_]*)"),
        ]
        settings_alias_attr_pattern = re.compile(
            r"(?:x-[a-zA-Z:-]+|:[a-zA-Z_-]+)\s*=\s*\"[^\"]*\b(?<!\$store\.)settings\.([a-zA-Z_][a-zA-Z0-9_]*)"
        )
        additional_patterns = [
            re.compile(r"(?:\$store\.settings\.additional|additional)\?*\.([a-zA-Z_][a-zA-Z0-9_]*)"),
            re.compile(r"\$store\.settings\.additional\?\.([a-zA-Z_][a-zA-Z0-9_]*)"),
        ]

        for file_path in settings_dir.rglob("*.html"):
            content = file_path.read_text(encoding="utf-8")
            for pattern in settings_patterns:
                used_settings_keys.update(pattern.findall(content))
            used_settings_keys.update(settings_alias_attr_pattern.findall(content))
            for pattern in additional_patterns:
                used_additional_keys.update(pattern.findall(content))

        for file_path in settings_dir.rglob("*.js"):
            content = file_path.read_text(encoding="utf-8")
            for pattern in settings_patterns:
                used_settings_keys.update(pattern.findall(content))
            for pattern in additional_patterns:
                used_additional_keys.update(pattern.findall(content))

        used_settings_keys.discard("settings")
        used_additional_keys.discard("additional")

        # Dynamic key access used in UI stores
        used_settings_keys.add("api_keys")

        # MCP editor compatibility keys used in mcp-servers-store.js
        used_settings_keys.update({"mcp_servers", "mcpServers"})

        return used_settings_keys, used_additional_keys

    def test_settings_get_includes_all_frontend_used_keys(self, client):
        used_settings_keys, used_additional_keys = self._collect_frontend_settings_keys()

        res = client.post("/settings_get", json={})
        assert res.status_code == 200
        payload = res.json()
        assert payload.get("ok") is True

        settings = payload.get("settings", {})
        additional = payload.get("additional", {})
        assert isinstance(settings, dict)
        assert isinstance(additional, dict)

        missing_settings = sorted(k for k in used_settings_keys if k not in settings)
        missing_additional = sorted(k for k in used_additional_keys if k not in additional)

        assert not missing_settings, f"Missing settings keys: {missing_settings}"
        assert not missing_additional, f"Missing additional keys: {missing_additional}"

    def test_mcp_compat_endpoints_have_agent_zero_shape(self, client):
        status = client.post("/mcp_servers_status", json={})
        assert status.status_code == 200
        status_payload = status.json()
        assert status_payload.get("success") is True
        assert "status" in status_payload

        apply_resp = client.post("/mcp_servers_apply", json={"mcp_servers": "{\n  \"mcpServers\": {}\n}"})
        assert apply_resp.status_code == 200
        apply_payload = apply_resp.json()
        assert apply_payload.get("success") is True
        assert "status" in apply_payload

        detail = client.post("/mcp_server_get_detail", json={"server_name": "example"})
        assert detail.status_code == 200
        detail_payload = detail.json()
        assert detail_payload.get("success") is True
        assert "detail" in detail_payload

        log_resp = client.post("/mcp_server_get_log", json={"server_name": "example"})
        assert log_resp.status_code == 200
        log_payload = log_resp.json()
        assert log_payload.get("success") is True
        assert isinstance(log_payload.get("log"), str)

    def test_catalog_refresh_returns_counts(self, client):
        res = client.post("/catalog_refresh", json={})
        assert res.status_code == 200
        payload = res.json()
        assert payload.get("ok") is True
        counts = payload.get("counts", {})
        assert isinstance(counts.get("chat_providers"), int)
        assert isinstance(counts.get("embedding_providers"), int)
        assert isinstance(counts.get("agents"), int)
        assert isinstance(payload.get("additional"), dict)

    def test_catalog_status_returns_summary(self, client):
        res = client.post("/catalog_status", json={})
        assert res.status_code == 200
        payload = res.json()
        assert payload.get("ok") is True
        summary = payload.get("summary", {})
        assert isinstance(summary.get("source"), str)
        assert isinstance(summary.get("provider_count"), int)
        assert isinstance(summary.get("model_count"), int)
        counts = payload.get("counts", {})
        assert isinstance(counts.get("minapps"), int)

    def test_minapps_endpoints_return_list(self, client):
        minapps = client.post("/minapps", json={})
        assert minapps.status_code == 200
        payload = minapps.json()
        assert payload.get("ok") is True
        assert isinstance(payload.get("data"), list)
        assert isinstance(payload.get("count"), int)

        launchpad = client.post("/launchpad_apps", json={})
        assert launchpad.status_code == 200
        lp_payload = launchpad.json()
        assert lp_payload.get("ok") is True
        assert isinstance(lp_payload.get("data"), list)
        assert isinstance(lp_payload.get("count"), int)
