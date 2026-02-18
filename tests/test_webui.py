"""
iTaK - WebUI endpoint & auth connectivity tests.
Verifies that the dashboard can reach all API endpoints when using the correct auth token.
"""

import time
import json
import re
import io
import zipfile
import subprocess
import secrets
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
        payload = res.json()
        assert payload["status"] == "ok"
        assert "state_sync" in payload
        assert "snapshot_build" in payload["state_sync"]

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

    def test_chat_export_contains_all_logs(self, client):
        """Chat export should include all logs for a context without polling."""
        create = client.post("/chat_create", json={})
        assert create.status_code == 200
        ctxid = create.json().get("ctxid")
        assert ctxid

        for i in range(3):
            msg = client.post(
                "/message_async",
                json={"text": f"msg {i}", "context": ctxid},
            )
            assert msg.status_code == 200

        exported = client.post("/chat_export", json={"ctxid": ctxid})
        assert exported.status_code == 200
        export_payload = exported.json()
        assert export_payload.get("ok") is True
        exported_ctx = json.loads(export_payload.get("content") or "{}")
        all_logs = exported_ctx.get("logs", [])
        assert isinstance(all_logs, list)
        assert len(all_logs) >= 6  # 3 user + 3 response
        assert exported_ctx.get("log_version") == len(all_logs)

    def test_poll_endpoint_removed(self, client):
        """Legacy poll endpoint should be removed in websocket-only mode."""
        removed = client.post(
            "/poll",
            json={"context": None, "log_from": 0, "notifications_from": 0},
        )
        assert removed.status_code in {404, 405}


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


class TestQueueReliabilityRegression:
    """Regression coverage for AZ1 message queue ordering and flush behavior."""

    @staticmethod
    def _create_context(client) -> str:
        created = client.post("/chat_create", json={})
        assert created.status_code == 200
        payload = created.json()
        assert payload.get("ok") is True
        ctxid = payload.get("ctxid")
        assert isinstance(ctxid, str) and ctxid
        return ctxid

    @staticmethod
    def _queue_item(client, ctxid: str, item_id: str, text: str):
        res = client.post(
            "/message_queue_add",
            json={
                "context": ctxid,
                "item_id": item_id,
                "text": text,
                "attachments": [],
            },
        )
        assert res.status_code == 200
        payload = res.json()
        assert payload.get("ok") is True

    @staticmethod
    def _chat_export(client, ctxid: str) -> dict:
        res = client.post("/chat_export", json={"ctxid": ctxid})
        assert res.status_code == 200
        payload = res.json()
        assert payload.get("ok") is True
        return json.loads(payload.get("content") or "{}")

    def test_send_all_preserves_queue_order_and_flushes(self, client):
        ctxid = self._create_context(client)
        self._queue_item(client, ctxid, "q1", "first")
        self._queue_item(client, ctxid, "q2", "second")
        self._queue_item(client, ctxid, "q3", "third")

        send = client.post("/message_queue_send", json={"context": ctxid, "send_all": True})
        assert send.status_code == 200
        assert send.json().get("ok") is True

        snapshot = self._chat_export(client, ctxid)
        logs = snapshot.get("logs") or []
        assert [entry.get("content") for entry in logs[-3:]] == ["first", "second", "third"]
        assert all((entry.get("kvps") or {}).get("queued") for entry in logs[-3:])
        assert snapshot.get("message_queue") == []

    def test_send_single_item_only_removes_target_item(self, client):
        ctxid = self._create_context(client)
        self._queue_item(client, ctxid, "q1", "first")
        self._queue_item(client, ctxid, "q2", "second")
        self._queue_item(client, ctxid, "q3", "third")

        send = client.post("/message_queue_send", json={"context": ctxid, "item_id": "q2"})
        assert send.status_code == 200
        assert send.json().get("ok") is True

        snapshot = self._chat_export(client, ctxid)
        logs = snapshot.get("logs") or []
        assert logs[-1].get("content") == "second"

        queued_items = snapshot.get("message_queue") or []
        assert [item.get("id") for item in queued_items] == ["q1", "q3"]

    def test_add_is_idempotent_for_same_item_id_across_retries(self, client):
        ctxid = self._create_context(client)
        self._queue_item(client, ctxid, "retry-id", "retry payload")
        # Simulate reconnect/retry replay with the same item id.
        self._queue_item(client, ctxid, "retry-id", "retry payload")

        snapshot = self._chat_export(client, ctxid)
        queued_items = snapshot.get("message_queue") or []
        assert len(queued_items) == 1
        assert queued_items[0].get("id") == "retry-id"

    def test_queue_survives_poll_cycles_until_sent(self, client):
        ctxid = self._create_context(client)
        self._queue_item(client, ctxid, "stable-id", "survives")

        first_poll = self._chat_export(client, ctxid)
        second_poll = self._chat_export(client, ctxid)

        first_items = first_poll.get("message_queue") or []
        second_items = second_poll.get("message_queue") or []
        assert [item.get("id") for item in first_items] == ["stable-id"]
        assert [item.get("id") for item in second_items] == ["stable-id"]


class TestChatResponseVisibilityRegression:
    """Regression coverage for message_async -> websocket snapshot visibility."""

    def test_message_async_response_is_present_in_poll_logs(self):
        from webui.server import create_app

        agent = _make_agent()
        agent.monologue = AsyncMock(return_value="hello from agent")
        app = create_app(agent)
        client = TestClient(app)

        send = client.post(
            "/message_async",
            json={"text": "hi there"},
        )
        assert send.status_code == 200
        send_payload = send.json()
        assert send_payload.get("ok") is True
        context_id = send_payload.get("context")
        assert isinstance(context_id, str) and context_id

        # Background response is async; wait briefly for completion before export.
        for _ in range(20):
            snapshot = client.post("/chat_export", json={"ctxid": context_id})
            assert snapshot.status_code == 200
            snapshot_payload = snapshot.json()
            logs = json.loads(snapshot_payload.get("content") or "{}").get("logs") or []
            if any(entry.get("type") == "response" for entry in logs):
                break
            time.sleep(0.05)

        user_logs = [entry for entry in logs if entry.get("type") == "user"]
        response_logs = [entry for entry in logs if entry.get("type") == "response"]

        assert user_logs, "Expected at least one user log entry"
        assert response_logs, "Expected at least one response log entry"
        assert user_logs[-1].get("content") == "hi there"
        assert response_logs[-1].get("content") == "hello from agent"
        assert (response_logs[-1].get("kvps") or {}).get("finished") is True


class TestFileBrowserCrudRegression:
    """Regression coverage for AZ2 file browser CRUD and guard behavior."""

    @staticmethod
    def _set_workdir(client, workdir: Path):
        res = client.post("/settings_set", json={"settings": {"workdir_path": str(workdir)}})
        assert res.status_code == 200
        assert res.json().get("ok") is True

    def test_file_browser_crud_flow(self, client, tmp_path):
        self._set_workdir(client, tmp_path)

        create = client.post(
            "/edit_work_dir_file",
            json={"path": str(tmp_path / "alpha.txt"), "content": "hello alpha"},
        )
        assert create.status_code == 200
        assert create.json().get("ok") is True

        load = client.get(f"/edit_work_dir_file?path={str(tmp_path / 'alpha.txt')}")
        assert load.status_code == 200
        load_payload = load.json()
        assert load_payload.get("ok") is True
        assert load_payload.get("data", {}).get("content") == "hello alpha"

        renamed = client.post(
            "/rename_work_dir_file",
            json={
                "action": "rename",
                "path": str(tmp_path / "alpha.txt"),
                "currentPath": str(tmp_path),
                "newName": "beta.txt",
            },
        )
        assert renamed.status_code == 200
        assert renamed.json().get("ok") is True

        folder = client.post(
            "/rename_work_dir_file",
            json={
                "action": "create-folder",
                "parentPath": str(tmp_path),
                "currentPath": str(tmp_path),
                "newName": "docs",
            },
        )
        assert folder.status_code == 200
        assert folder.json().get("ok") is True

        listing = client.get(f"/get_work_dir_files?path={str(tmp_path)}")
        assert listing.status_code == 200
        listing_payload = listing.json()
        assert listing_payload.get("ok") is True
        names = [entry.get("name") for entry in listing_payload.get("data", {}).get("entries", [])]
        assert "beta.txt" in names
        assert "docs" in names

        delete = client.post(
            "/delete_work_dir_file",
            json={"path": str(tmp_path / "beta.txt"), "currentPath": str(tmp_path)},
        )
        assert delete.status_code == 200
        assert delete.json().get("ok") is True

    def test_path_outside_workdir_returns_clear_error(self, client, tmp_path):
        self._set_workdir(client, tmp_path)

        res = client.post(
            "/rename_work_dir_file",
            json={
                "action": "rename",
                "path": "/etc/passwd",
                "currentPath": str(tmp_path),
                "newName": "x.txt",
            },
        )
        assert res.status_code == 200
        payload = res.json()
        assert payload.get("ok") is False
        assert "outside configured workdir" in payload.get("error", "")

    def test_delete_workdir_root_is_blocked(self, client, tmp_path):
        self._set_workdir(client, tmp_path)

        res = client.post(
            "/delete_work_dir_file",
            json={"path": str(tmp_path), "currentPath": str(tmp_path)},
        )
        assert res.status_code == 200
        payload = res.json()
        assert payload.get("ok") is False
        assert "cannot delete workdir root" in payload.get("error", "").lower()


class TestProcessGroupTransitionRegression:
    """Regression guardrails for process-group transition wiring in frontend messages."""

    def test_process_group_transition_hooks_present(self):
        root = Path(__file__).resolve().parents[1]
        messages_js = root / "webui" / "static" / "js" / "messages.js"
        content = messages_js.read_text(encoding="utf-8")

        assert "const STEP_COLLAPSE_DELAY" in content
        assert "scheduleStepCollapse(expandedStep, delay);" in content
        assert "toggleStepCollapse(step, true);" in content
        assert "const isGroupComplete = isProcessGroupComplete(group);" in content


class TestProjectsAndSkillsRegression:
    """Regression coverage for AZ3/AZ4 project + skills parity features."""

    @staticmethod
    def _make_local_git_repo(tmp_path: Path) -> Path:
        repo = tmp_path / "seed-repo"
        repo.mkdir(parents=True, exist_ok=True)
        (repo / "README.md").write_text("hello\n", encoding="utf-8")
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-m",
                "init",
            ],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        return repo

    def test_projects_clone_and_git_health(self, client, tmp_path):
        repo = self._make_local_git_repo(tmp_path)
        project_name = f"clone_{secrets.token_hex(4)}"

        clone = client.post(
            "/projects",
            json={
                "action": "clone",
                "project": {
                    "name": project_name,
                    "title": "Clone Test",
                    "color": "#123456",
                    "git_url": str(repo),
                },
            },
        )
        assert clone.status_code == 200
        payload = clone.json()
        assert payload.get("ok") is True
        git_status = payload.get("data", {}).get("git_status", {})
        assert git_status.get("is_git_repo") is True
        assert isinstance(git_status.get("current_branch"), str)

        options = client.post("/projects", json={"action": "list_options"})
        assert options.status_code == 200
        assert any(opt.get("key") == project_name for opt in options.json().get("data", []))

    def test_skills_import_export_create_flow(self, client):
        project_name = f"skills_{secrets.token_hex(4)}"

        create_project = client.post(
            "/projects",
            json={
                "action": "create",
                "project": {
                    "name": project_name,
                    "title": "Skills Project",
                },
            },
        )
        assert create_project.status_code == 200
        assert create_project.json().get("ok") is True

        skill_zip = io.BytesIO()
        with zipfile.ZipFile(skill_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "pack/network/alpha/SKILL.md",
                "# Skill: Alpha\n\n## When to Use\nUse alpha.\n\n## Steps\n1. Do one thing.\n",
            )
        skill_zip.seek(0)

        preview = client.post(
            "/skills_import_preview",
            files={"skills_file": ("skills.zip", skill_zip.getvalue(), "application/zip")},
            data={
                "namespace": "pack",
                "conflict": "skip",
                "project_name": project_name,
            },
        )
        assert preview.status_code == 200
        preview_payload = preview.json()
        assert preview_payload.get("success") is True
        assert preview_payload.get("imported_count") == 1

        missing_review = client.post(
            "/skills_import",
            files={"skills_file": ("skills.zip", skill_zip.getvalue(), "application/zip")},
            data={
                "namespace": "pack",
                "conflict": "skip",
                "project_name": project_name,
            },
        )
        assert missing_review.status_code == 200
        assert missing_review.json().get("success") is False
        assert "Review summary" in missing_review.json().get("error", "")

        imported = client.post(
            "/skills_import",
            files={"skills_file": ("skills.zip", skill_zip.getvalue(), "application/zip")},
            data={
                "namespace": "pack",
                "conflict": "skip",
                "project_name": project_name,
                "review_summary": "Reviewed structure and source safety",
            },
        )
        assert imported.status_code == 200
        imported_payload = imported.json()
        assert imported_payload.get("success") is True
        assert imported_payload.get("imported_count") == 1

        listed = client.post(
            "/skills",
            json={"action": "list", "project_name": project_name},
        )
        assert listed.status_code == 200
        listed_payload = listed.json()
        assert listed_payload.get("ok") is True
        assert any("SKILL.md" in (item.get("path") or "") for item in listed_payload.get("data", []))

        exported = client.post(
            "/skills_export",
            json={"project_name": project_name},
        )
        assert exported.status_code == 200
        exported_payload = exported.json()
        assert exported_payload.get("ok") is True
        assert isinstance(exported_payload.get("archive_base64"), str)
        archive = zipfile.ZipFile(io.BytesIO(__import__("base64").b64decode(exported_payload["archive_base64"])))
        assert any(name.endswith("SKILL.md") for name in archive.namelist())

        created_preview = client.post(
            "/skills_create_from_text",
            json={
                "title": "Network Troubleshooting",
                "source_text": "Check ping, then DNS, then route.",
                "project_name": project_name,
                "install": False,
            },
        )
        assert created_preview.status_code == 200
        created_preview_payload = created_preview.json()
        assert created_preview_payload.get("ok") is True
        assert "## When to Use" in created_preview_payload.get("preview", "")

        created_install = client.post(
            "/skills_create_from_text",
            json={
                "title": "Network Troubleshooting",
                "source_text": "Check ping, then DNS, then route.",
                "project_name": project_name,
                "install": True,
            },
        )
        assert created_install.status_code == 200
        created_install_payload = created_install.json()
        assert created_install_payload.get("ok") is True
        installed_path = created_install_payload.get("path")
        assert installed_path and Path(installed_path).exists()
