# iTaK Deployment Checklist

## At a Glance

1. Complete Development checklist
2. Set strong auth tokens in config

  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

  - [ ] WebUI auth token set
  - [ ] MCP token set when MCP server is enabled

3. Configure limits and service stack

  ```bash
  docker compose up -d
  ```

  - [ ] Rate limits reviewed for team usage
  - [ ] Optional services (Neo4j, Weaviate, SearXNG) validated

4. Optional adapter enablement

  - [ ] Discord token set (if required)
  - [ ] Telegram token set (if required)
  - [ ] Slack token set (if required)

5. Operational readiness

  - [ ] Multi-user access validated
  - [ ] Logs reviewed and rotation configured
  - [ ] Alerting pipeline configured
1. Install dependencies

  ```bash
  cd iTaK
  pip install -r install/requirements/requirements.txt
  ```

2. Configure local files

  ```bash
  cp install/config/config.json.example config.json
  cp .env.example .env
  ```

3. Add at least one LLM key in `.env`

  ```bash
  GOOGLE_API_KEY=your_key_here
  # or
  OPENAI_API_KEY=your_key_here
  ```

4. Validate setup

  ```bash
  python -m app.main --doctor
  ```

  - [ ] Doctor checks pass for required components
  - [ ] At least one LLM provider is available

5. Smoke run

  ```bash
  python -m app.main
  # optional
  python -m app.main --webui
  ```

  - [ ] Agent starts without critical errors
  - [ ] WebUI reachable at `http://localhost:48920` when enabled

---

## Team or Staging Environment

**Use case:** Shared internal environment before production.

### Additional Prerequisites

- [ ] Docker installed (`docker --version`)
- [ ] Compose available (`docker compose version`)

### Setup Steps

1. Complete Development checklist
2. Set strong auth tokens in config

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```


  - [ ] WebUI auth token set
  - [ ] MCP token set when MCP server is enabled


3. Configure limits and service stack

  ```bash
  docker compose up -d
  ```


  - [ ] Rate limits reviewed for team usage
  - [ ] Optional services (Neo4j, Weaviate, SearXNG) validated

4. Optional adapter enablement

  - [ ] Discord token set (if required)
  - [ ] Telegram token set (if required)
  - [ ] Slack token set (if required)

5. Operational readiness


  - [ ] Multi-user access validated
  - [ ] Logs reviewed and rotation configured
  - [ ] Alerting pipeline configured

---

## Production Environment

**Use case:** Internet-facing or business-critical deployment.

### Critical Warning

- [ ] Access restricted to trusted users only
- [ ] Security monitoring and incident process documented
- [ ] Backup and restore process tested

### Infrastructure and Security

- [ ] HTTPS/TLS configured via reverse proxy
- [ ] Firewall rules and host hardening applied
- [ ] Output guard enabled and tested
- [ ] SSRF and path-guard protections verified
- [ ] Rate limits tightened for production traffic

### Runtime Configuration

Use conservative defaults and explicit override tracking.

```json
{
  "agent": {
    "max_iterations": 30,
    "timeout_seconds": 300
  },
  "security": {
    "rate_limit": {
      "global_rpm": 120,
      "per_user_rpm": 10,
      "per_tool": {
        "code_execution": 5,
        "web_search": 20
      }
    }
  },
  "output_guard": {
    "enabled": true,
    "strict_mode": true,
    "log_redactions": true
  }
}
```

- [ ] Iteration and timeout limits set
- [ ] Strict output guard enabled
- [ ] Conservative rate limits enabled

### Runtime Override and Migration Runbook

- [ ] Validate `ITAK_SET_*` overrides via doctor

  ```bash
  python -m app.main --doctor
  ```

- [ ] Record approved override keys in release notes
- [ ] Capture migration status before cutover

  ```bash
  python install.py --migration-status --migration-source data --migration-target runtime
  ```

- [ ] Run migration with backup and verification report

  ```bash
  python install.py --migrate-user-data --migration-source data --migration-target runtime
  ```

- [ ] Store rollback archive path and restore command in incident notes

### Data and Monitoring

- [ ] Persistent database volumes configured
- [ ] Daily backup job enabled
- [ ] CPU, memory, disk, error-rate, and uptime monitoring enabled
- [ ] API usage and cost monitoring enabled

### Final Go-Live Validation

- [ ] Regression tests pass (`pytest tests/ -v`)
- [ ] Adapter-specific smoke checks pass
- [ ] Security checks pass (`python -m app.main --doctor`)
- [ ] Rollback procedure reviewed with on-call owner

### Dokploy WebSocket Validation (Chat UI)

Use this when chat output appears in logs but not in the main chat panel.

1. Verify reverse-proxy upgrade headers

  - [ ] `Upgrade: websocket` is forwarded
  - [ ] `Connection: upgrade` is forwarded
  - [ ] WebSocket read timeout is at least `60s`

2. Validate browser transport

  - [ ] Open browser devtools on your Dokploy URL
  - [ ] Confirm `wss://.../socket.io/...` connects without repeated reconnect loops
  - [ ] Confirm `state_request`/`state_push` traffic is flowing while chat is active

3. Validate app behavior after deploy

  - [ ] Send one test prompt in chat
  - [ ] Confirm `/message_async` returns `ok: true`
  - [ ] Confirm the assistant reply appears in the chat panel after websocket snapshot push

4. WebSocket-only sanity check (current build)

  - [ ] The frontend triggers `state_request` after `/message_async`
  - [ ] No `/poll` request is required for normal chat visibility
