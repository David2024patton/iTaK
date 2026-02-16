# iTaK AI Context

> Structured project facts for AI agents and automation.

## Project Facts (Snapshot)

```yaml
project: iTaK
language: python
entrypoint: app/main.py
webui_backend: webui/server.py
adapters:
  - cli
  - webui
  - discord
  - telegram
  - slack
memory_layers:
  - markdown
  - sqlite
  - neo4j
  - weaviate
security_modules:
  - security/secrets.py
  - security/output_guard.py
  - security/path_guard.py
  - security/ssrf_guard.py
  - security/rate_limit.py
  - security/rate_limiter.py
  - security/scanner.py
rbac: core/users.py
task_board: core/task_board.py
swarm: core/swarm.py
self_heal: core/self_heal.py
```

---

## Important Commands

### Run

```bash
python -m app.main --webui
python -m app.main --adapter cli
```

### Test

```bash
pytest tests -q
pytest tests --collect-only -q
```

### Smoke Scripts

```bash
bash tools/check_resource_endpoints.sh
bash tools/check_memory_smoke.sh
bash tools/check_chat_smoke.sh
bash tools/check_system_smoke.sh
```

Optional target override:

```bash
WEBUI_BASE_URL=http://127.0.0.1:43067 bash tools/check_system_smoke.sh
```

---

## High-Value Endpoints

- `POST /resource_hub`
- `POST /resource_file`
- `POST /launchpad_apps`
- `POST /catalog_refresh`
- `POST /catalog_sync_from_cherry`
- `POST /system_test_run`

Auth-protected API group exists under `/api/*` for memory and system endpoints.

---

## Documentation Map

- Wiki home: [WIKI.md](WIKI.md)
- Beginner quick path: [NOOBS_FIRST_DAY.md](NOOBS_FIRST_DAY.md)
- Tools: [tools.md](tools.md)
- WebUI/API: [webui.md](webui.md)
- Testing: [root/TESTING.md](root/TESTING.md)
