# First-Pass Port Matrix (iTaK ↔ Agent Zero + OpenClaw)

Purpose: practical file-to-file map for side-by-side porting.

Reference roots:
- iTaK: `E:/test/iTaK`
- Agent Zero: `E:/test/iTaK/references/agent-zero`
- OpenClaw: `E:/test/iTaK/references/openclaw`

## 1) UI / Main Chat Send-Receive

| iTaK target | Agent Zero source | OpenClaw source | Current status | Next port action |
|---|---|---|---|---|
| `webui/static/index.js` | `references/agent-zero/webui/index.js` | `references/openclaw/src/commands/health.ts` (timing/health reporting ideas) | Mostly aligned to A0 + iTaK perf patches | Periodic upstream diff for send/state_request/state_push deltas |
| `webui/static/js/api.js` | `references/agent-zero/webui/js/api.js` | `references/openclaw/src/infra/errors.ts` (error-shaping pattern) | iTaK extended with request timeouts | Keep timeout defaults configurable from settings |
| `webui/static/js/messages.js` | `references/agent-zero/webui/js/messages.js` | `references/openclaw/src/terminal/health-style.ts` (formatting discipline) | iTaK diverged with perf guards | Run targeted parity diff after each upstream pull |
| `webui/server.py` | `references/agent-zero/python/api/message_async.py`, `references/agent-zero/python/websocket_handlers/state_sync_handler.py` | `references/openclaw/src/gateway/server-methods/health.ts` (health surface ideas) | iTaK compatible + optimized | Add optional snapshot timing telemetry endpoint |

## 2) Security / Hardening

| iTaK target | Agent Zero source | OpenClaw source | Current status | Next port action |
|---|---|---|---|---|
| `security/secrets.py` | `references/agent-zero/python/helpers/secrets.py` | `references/openclaw/src/security/secret-equal.ts` | Implemented with constant-time checks + masking | Add regression tests for partial secret leaks (streaming text) |
| `security/path_guard.py` | — | `references/openclaw/src/security/scan-paths.ts`, `references/openclaw/src/infra/fs-safe.ts` | Implemented traversal checks | Add symlink-escape checks mirroring OpenClaw `fs-safe` |
| `security/ssrf_guard.py` | — | `references/openclaw/src/security/external-content.ts` | Implemented allow/deny URL validation | Add test cases for edge schemes + localhost aliases |
| `security/rate_limiter.py` | — | `references/openclaw/src/security/audit.ts` (policy severity style) | Implemented auth lockout | Add rate-limit health counters surfaced in doctor |
| `security/scanner.py` | — | `references/openclaw/src/security/audit.ts`, `references/openclaw/src/security/audit-extra.ts`, `references/openclaw/src/security/audit-fs.ts` | Basic scanner exists | Port risk scoring + categorized findings model |

## 3) Doctor / Diagnostics / Health

| iTaK target | Agent Zero source | OpenClaw source | Current status | Next port action |
|---|---|---|---|---|
| `core/doctor.py` | `references/agent-zero/python/api/health.py` (minimal health shape) | `references/openclaw/src/commands/health.ts`, `references/openclaw/src/daemon/diagnostics.ts`, `references/openclaw/src/infra/diagnostic-flags.ts` | Extended with bottleneck scan | Add doctor flags (`--deep`, `--json`) and machine-readable output |
| `app/main.py` (`--doctor`) | — | `references/openclaw/src/commands/health.ts` | Wired | Add optional health snapshot artifact in `logs/` |
| `webui/server.py` (`/api/health`) | `references/agent-zero/python/api/health.py` | `references/openclaw/src/gateway/server/health-state.ts` | Present | Add service-level timings and degraded-mode reason |

## 4) Adapters (Discord / Telegram / Slack)

| iTaK target | Agent Zero source | OpenClaw source | Current status | Next port action |
|---|---|---|---|---|
| `adapters/discord.py` | — | `references/openclaw/src/discord/monitor.ts`, `references/openclaw/src/discord/send.ts`, `references/openclaw/src/discord/targets.ts` | Basic adapter present | Port robust monitor/backoff + target resolution patterns |
| `adapters/telegram.py` | — | `references/openclaw/src/telegram/monitor.ts`, `references/openclaw/src/telegram/send.ts`, `references/openclaw/src/telegram/webhook.ts` | Basic adapter present | Port recoverable network error handling + offset store strategy |
| `adapters/slack.py` | — | `references/openclaw/src/slack/monitor.ts`, `references/openclaw/src/slack/send.ts`, `references/openclaw/src/slack/resolve-channels.ts` | Basic adapter present | Port channel/account binding and retry semantics |
| `adapters/base.py` | — | `references/openclaw/src/channels/plugins/types.ts` | Base abstraction present | Align adapter capability contracts with OpenClaw plugin style |

## 5) Suggested Port Order (Low Risk → High Impact)

1. Adapter reliability primitives (Telegram/Discord retry + backoff)
2. Security scanner severity model (`security/scanner.py` parity with OpenClaw audit categories)
3. Doctor CLI output modes (`core/doctor.py` + `app/main.py`)
4. WebUI snapshot timing telemetry (`webui/server.py` + `webui/static/index.js`)
5. Deep symlink/path-hardening checks (`security/path_guard.py` + doctor checks)

## 6) Operating Rules for Side-by-Side Ports

- Always refresh references before a port batch: `./tools/side_by_side_upstreams.ps1 -Refresh -Status`
- Port in narrow slices (one subsystem per PR/commit group).
- Run doctor and targeted tests after each slice.
- Keep `references/` read-only; copy patterns, not wholesale files.
