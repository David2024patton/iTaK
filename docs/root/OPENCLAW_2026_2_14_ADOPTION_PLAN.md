# OpenClaw v2026.2.14 Adoption Plan for iTaK

## At a Glance

- Audience: Maintainers and security-focused developers implementing cross-project hardening updates.
- Scope: Translate OpenClaw v2026.2.14 changes into actionable, file-level iTaK work items.
- Last reviewed: 2026-02-16.

## Quick Start

- Start with Phase 1 security work before feature parity updates.
- Implement each PR slice independently and run tests after each merge.
- Keep this checklist updated with commit hashes as tasks land.

## Deep Dive

This plan is based on OpenClaw release: https://github.com/openclaw/openclaw/releases/tag/v2026.2.14

## AI Notes

- Treat this document as the source of truth for OpenClaw parity work sequencing.
- Prefer small merges with tests over a single large migration branch.

---

## Goals

1. Close high-risk security gaps first.
2. Improve long-running stability (memory and queue growth).
3. Improve reliability of one-shot CLI and channel delivery paths.
4. Add regression tests so hardening does not regress later.

---

## Current iTaK Coverage Snapshot

| Area | Current iTaK status | Evidence files |
|------|----------------------|----------------|
| Path traversal checks | Partial to strong | `security/path_guard.py`, `security/scanner.py` |
| SSRF protections | Present | `security/ssrf_guard.py`, `core/webhooks.py` |
| Webhook auth | Present but simple shared secret | `core/webhooks.py`, `webui/server.py` |
| Media local path safety | Partial | `core/media.py` |
| Cache growth bounds | Partial | `security/rate_limiter.py`, scattered maps/caches |
| One-shot lifecycle cleanup | Partial | `adapters/*`, `core/agent.py`, CLI flow in `main.py` |

---

## Phase 1 - Security Parity (Do First)

### PR-1: Harden webhook authentication and routing

- [ ] Add explicit required-secret mode for inbound webhooks.
- [ ] Reject ambiguous webhook target matching if multiple handlers match.
- [ ] Add adapter-specific signature verification hooks for providers that support signatures.

Target files:

- `core/webhooks.py`
- `webui/server.py`
- `core/config_watcher.py` (if runtime reload needed)
- `docs/security.md`

Tests:

- `tests/test_webhooks_security.py` (new)

### PR-2: Strengthen media path and URL safety

- [ ] Enforce strict local media root allowlists.
- [ ] Reject filesystem-root allowlist entries.
- [ ] Require explicit override for trusted validated paths.
- [ ] Apply SSRF guard to all URL-backed media fetch paths.

Target files:

- `core/media.py`
- `security/ssrf_guard.py`
- `adapters/discord.py`
- `adapters/telegram.py`
- `adapters/slack.py`

Tests:

- `tests/test_media_security.py` (new)
- `tests/test_ssrf_guard.py` (extend)

### PR-3: Enforce file mutation bounds and symlink safety

- [ ] Ensure all mutating file operations are workspace-bounded.
- [ ] Explicitly detect and block symlink escape writes/deletes.
- [ ] Add regression tests for traversal and symlink edge cases.

Target files:

- `security/path_guard.py`
- `tools/code_execution.py` (if file writes happen through tool surface)
- `core/agent.py` (if tool orchestration path checks are needed)

Tests:

- `tests/test_path_guard.py` (extend)

---

## Phase 2 - Stability and Reliability

### PR-4: Bound long-lived memory structures

- [ ] Add size caps and TTL pruning for long-lived dictionaries/caches.
- [ ] Add periodic maintenance pruning path.
- [ ] Emit diagnostic counters for evictions and current size.

Target files:

- `core/agent.py`
- `core/progress.py`
- `core/task_board.py`
- `security/rate_limiter.py`
- `heartbeat/monitor.py`

Tests:

- `tests/test_memory_bounds.py` (new)

### PR-5: Improve one-shot CLI and plugin cleanup behavior

- [ ] Ensure one-shot command paths always exit after successful delivery.
- [ ] Ensure cleanup hooks run on both success and failure paths.

Target files:

- `main.py`
- `adapters/cli.py`
- `extensions/*` (if lifecycle hooks are wired there)

Tests:

- `tests/test_cli_oneshot.py` (new)

### PR-6: Preserve in-flight stream output under concurrency

- [ ] Prevent active stream text from being dropped on concurrent completion events.
- [ ] Add guard against stream reset while a run is still active.

Target files:

- `webui/server.py`
- `webui/static/app.js`
- `core/logger.py`

Tests:

- `tests/test_streaming_concurrency.py` (new)

---

## Phase 3 - Ops and Diagnostics

### PR-7: Add stricter diagnostics commands

- [ ] Add security audit check for weak webhook config.
- [ ] Add no-em-dash and markdown lint checks to docs CI summary output.
- [ ] Add checks for unsafe URL/media config values.

Target files:

- `core/doctor.py`
- `tools/check_no_emdash.sh`
- `.github/workflows/ci.yml`

Tests:

- `tests/test_doctor_security.py` (extend)

### PR-8: Add migration helpers for config aliases

- [ ] Add migration helper for renamed config keys where relevant.
- [ ] Keep old keys temporarily with explicit deprecation notices.

Target files:

- `core/models.py`
- `core/doctor.py`
- `docs/config.md`

Tests:

- `tests/test_config_migration.py` (new)

---

## Suggested Merge Order

1. PR-1 Webhook security
2. PR-2 Media safety
3. PR-3 File mutation bounds
4. PR-4 Cache bounds
5. PR-5 One-shot cleanup
6. PR-6 Streaming concurrency
7. PR-7 Diagnostics
8. PR-8 Config migrations

---

## Acceptance Criteria

- [ ] New security tests pass in CI.
- [ ] No regression in current smoke tests.
- [ ] No em-dash and markdown lint checks still pass.
- [ ] Docs updated for each merged PR.
- [ ] `docs/root/PRODUCTION_TESTING_SUMMARY.md` updated with final validation counts.

---

## Progress Log

- 2026-02-16: Plan created and linked in wiki/testing docs.
