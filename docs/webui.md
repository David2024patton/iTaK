# WebUI & API Reference

## At a Glance
- Audience: Users, operators, developers, and contributors working with iTaK.
- Scope: This page explains `WebUI & API Reference`.
- Last reviewed: 2026-02-16.

## Quick Start
- Docs hub: [WIKI.md](WIKI.md)
- Beginner path: [NOOBS_FIRST_DAY.md](NOOBS_FIRST_DAY.md)
- AI-oriented project map: [AI_CONTEXT.md](AI_CONTEXT.md)

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Use explicit file paths and exact command examples from this page when automating tasks.
- Treat scale/compliance statements as environment-dependent unless paired with test or audit evidence.


> The monitoring dashboard and REST API.

## Overview

iTaK includes a full-stack monitoring dashboard built with FastAPI + WebSocket. It provides real-time agent monitoring, memory search, task management, and system health.

**Default URL:** `http://localhost:48920`

---

## Dashboard

**File:** `webui/static/index.html` | **Lines:** ~650

A single-page application that shows:

| Panel | What it Shows |
|-------|---------------|
| **Health** | Agent status, uptime, subsystem checklist |
| **Stats** | Iteration count, response times, model usage |
| **Logs** | Real-time structured event log |
| **Memory** | Search across all 4 memory layers |
| **Tasks** | Kanban board (pending/active/complete/failed) |
| **Tools** | List of loaded tools with descriptions |
| **Security** | Security scan results, output guard stats |
| **Chat** | Send messages to the agent from the browser |

### WebSocket

The dashboard connects via WebSocket for real-time updates:

```javascript
const ws = new WebSocket("ws://localhost:48920/ws");
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // data.type: "log", "progress", "heartbeat", "stats"
    updateDashboard(data);
};
```

---

## REST API

**File:** `webui/server.py`

All endpoints return JSON.

- Compatibility/UI endpoints are primarily mounted at root (for example: `/poll`, `/chat_create`, `/launchpad_apps`, `/resource_hub`).
- Auth-protected API endpoints are mounted under `/api/*` (for example memory stats/search and tool listing).

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (200 OK) |
| GET | `/stats` | Agent statistics |
| GET | `/subsystems` | All subsystem status |
| GET | `/config` | Safe config (secrets masked) |

**Example: GET /api/v1/stats**
```json
{
    "iterations": 42,
    "total_iterations": 1500,
    "uptime_seconds": 3600,
    "tools_loaded": 8,
    "extensions_loaded": 12,
    "memory_stats": {...},
    "model_usage": {...}
}
```

### Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/logs?search=&limit=50&offset=0` | Query agent logs |

**Example: GET /api/v1/logs?search=error&limit=10**
```json
{
    "logs": [
        {
            "timestamp": "2025-12-15T10:30:00",
            "event_type": "error",
            "data": {"message": "Connection refused"}
        }
    ],
    "total": 1
}
```

### Memory

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/memory/search?query=&category=&limit=10` | Search memory |
| GET | `/memory/stats` | Layer statistics |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks?status=&limit=50` | List tasks |
| GET | `/tasks/{id}` | Get single task |
| POST | `/tasks` | Create task |
| POST | `/tasks/{id}/complete` | Mark complete |
| POST | `/tasks/{id}/fail` | Mark failed |
| DELETE | `/tasks/{id}` | Delete task |
| GET | `/tasks/board` | Kanban board view |

**Example: POST /api/v1/tasks**
```json
{
    "title": "Deploy v2",
    "description": "Build, push, and deploy version 2",
    "steps": ["Build", "Push", "Deploy", "Verify"]
}
```

### Tools

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tools` | List all loaded tools |

### Security

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/security/scan` | Scan code for vulnerabilities |

**Example: POST /api/v1/security/scan**
```json
{"code": "import os\nos.system('rm -rf /')"}
```
Response:
```json
{"safe": false, "blocked": true, "findings": [...]}
```

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send message to agent |

**Example: POST /api/v1/chat**
```json
{"message": "What's on my task board?"}
```

### MCP

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/mcp/status` | MCP client connections |
| GET | `/mcp/server/health` | MCP server health |

### Self-Healing

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/self-heal/stats` | Healing statistics |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/inbound` | Receive external webhook |
| GET | `/webhooks/stats` | Webhook statistics |

### Swarm

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/swarm/stats` | Swarm coordinator stats |
| GET | `/swarm/profiles` | Available agent profiles |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | List all users |
| POST | `/users` | Add a user |
| DELETE | `/users/{id}` | Remove a user |
| GET | `/users/stats` | User registry stats |

### Presence & Media

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/presence` | Current agent status |
| GET | `/media/stats` | Media pipeline stats |

### Resource Hub & Launchpad

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/resource_hub` | Aggregate resource index (adapters, prompts, tools, skills, tasks, MCP summary) |
| POST | `/resource_file` | Fetch preview content for a selected resource item |
| POST | `/launchpad_apps` | List launchpad apps from catalog |
| POST | `/catalog_refresh` | Refresh runtime catalog from local catalog file |
| POST | `/catalog_sync_from_cherry` | Pull and sync catalog from configured Cherry source |

### System Smoke Tests (Settings UI)

The External Settings tab exposes one-click smoke checks and matching CLI commands.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/system_test_run` | Run allowlisted smoke test scripts (`resources`, `memory`, `chat`, `all`) |

Backed scripts:
- `tools/check_resource_endpoints.sh`
- `tools/check_memory_smoke.sh`
- `tools/check_chat_smoke.sh`
- `tools/check_system_smoke.sh`

`/system_test_run` sets `WEBUI_BASE_URL` automatically so tests run against the active WebUI port.

---

## Configuration

```json
{
    "webui": {
        "enabled": true,
        "host": "0.0.0.0",
        "port": 48920
    }
}
```

## Starting the WebUI

```python
from webui.server import start_webui
start_webui(agent, host="0.0.0.0", port=48920)
```

Or via Docker:
```yaml
services:
  itak:
    ports:
      - "48920:48920"
```
