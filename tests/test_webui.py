"""
iTaK - WebUI endpoint & auth connectivity tests.
Verifies that the dashboard can reach all API endpoints when using the correct auth token.
"""

import time
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
