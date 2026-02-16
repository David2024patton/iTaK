# Agent Zero v0.9.8 Adoption Plan for iTaK

## At a Glance

- Audience: Maintainers and product owners evaluating Agent Zero v0.9.8 parity in iTaK.
- Scope: Map Agent Zero v0.9.8 changes into iTaK current status and implementation tasks.
- Last reviewed: 2026-02-16.

## Quick Start

- Review the parity matrix first to separate shipped features from gaps.
- Execute Phase 1 and Phase 2 in order for highest user impact.
- Update this document with PR links and commit hashes as work lands.

## Deep Dive

Release source: https://github.com/agent0ai/agent-zero/releases/tag/v0.9.8

Primary highlights in v0.9.8:

- Web UI redesign with process groups and detail controls
- Message queue while the agent is still running
- Skills system (`SKILL.md`) replacing instruments
- Git-based project cloning flow
- WebSocket-first frontend transport
- Workdir and workspace-structure prompt controls
- User data consolidation and migration support

Transcript-driven additions to capture:

- Skills import from zip packs and external indexes
- "Create skill" workflow for converting ad-hoc docs into reusable skills
- Explicit trust and review guidance for third-party skills (prompt-injection risk)
- Process-group execution stats visibility (steps, runtime, started-at)
- Queue behavior controls (queue only vs immediate intervention)

## AI Notes

- Use this plan as the canonical Agent Zero parity tracker for v0.9.8.
- Prefer evidence from code paths and tests over assumptions from release notes.

---

## Parity Matrix (iTaK vs Agent Zero v0.9.8)

| v0.9.8 Capability | iTaK Status | Evidence in iTaK | Action |
|---|---|---|---|
| WebSocket-first UI transport | Mostly implemented | `webui/static/components/sync/*`, `webui/static/components/settings/developer/websocket-*`, `webui/server.py` | Keep hardening transport fallback and telemetry |
| Polling fallback when WebSocket degrades | Implemented | `webui/static/components/sync/sync-store.js` | Keep as safety path |
| Process groups with detail modes | Implemented | `webui/static/components/messages/process-group/*`, `webui/static/components/sidebar/bottom/preferences/preferences-store.js` | Add UX polish and metrics badges |
| Message queue during active run | Implemented | `webui/static/components/chat/message-queue/message-queue-store.js` | Add queue reliability tests |
| File browser and in-browser file actions | Implemented (basic to medium) | `webui/static/components/modals/file-browser/*` | Expand edit workflows and permissions tests |
| Welcome banners / home notices | Implemented | `webui/static/components/welcome/*` | Add policy-driven banner rules |
| Chat width preference | Implemented | `webui/static/components/sidebar/bottom/preferences/preferences-store.js` | No major gap |
| Skills model (`SKILL.md` style) | Implemented | `skills/SKILL.md`, `docs/skills.md` | Add import/export compatibility tests |
| Skill zip import flow in UI | Partial | Skills settings components exist; import UX parity not complete | Add zip import + recursive skill discovery |
| Skill source trust controls | Gap | Security guidance exists but no dedicated skill trust policy layer | Add trusted-source and review checks |
| Create-skill assisted workflow | Partial | Skills and tool ecosystem exists | Add guided create-skill UX and validation |
| Git project clone flow in UI | Partial | `tools/git_tool.py`, project docs, launchpad/catalog features | Add first-class clone wizard in project creation flow |
| Subagent profiles | Implemented | `prompts/profiles/*.md`, swarm/subagent docs | Add profile pack import UX |
| Workdir path + show file structure in prompt | Implemented | `webui/static/components/settings/agent/workdir.html` and settings store | Add stronger bounds validation in UI and backend |
| User data migration and consolidation flow | Partial | Install/setup scripts and docs | Add explicit migration command and rollback docs |
| Env prefix config overrides (`A0_SET_*`) | Gap | No direct equivalent | Consider iTaK-specific env override prefix and migration utility |
| New providers (CometAPI, Z.AI, Moonshot, Bedrock) | Partial/unknown by provider | Provider coverage in current config/docs may differ | Audit providers and add missing adapters intentionally |

---

## Phase 1 (High-Impact UX and Reliability)

### PR-AZ1: Process group and queue reliability hardening

- [ ] Add regression tests for process-group step transition state.
- [ ] Add regression tests for queued message ordering and flush behavior.
- [ ] Ensure queue survives reconnects and transient sync fallback.

Target files:

- `webui/static/components/messages/process-group/*`
- `webui/static/components/chat/message-queue/*`
- `webui/static/components/sync/*`
- `tests/` (new UI/API integration tests)

### PR-AZ2: File browser action parity

- [ ] Verify rename/create/delete/edit flows against backend guards.
- [ ] Add clear permission errors and path-bound enforcement messaging.
- [ ] Add smoke tests for file browser CRUD actions.

Target files:

- `webui/static/components/modals/file-browser/*`
- Backend endpoints in `webui/server.py`
- `security/path_guard.py`

---

## Phase 2 (Project and Skills Portability)

### PR-AZ3: Git project clone wizard in project init

- [ ] Add UI form for Git URL + optional token/credentials.
- [ ] Add trust warning step before clone.
- [ ] Show clone status and post-clone health checks.

Target files:

- Project/create UI components under `webui/static/components/*`
- `tools/git_tool.py`
- `webui/server.py`

### PR-AZ4: Skills import/export compatibility workflow

- [ ] Add skills bundle import flow (zip) with validation.
- [ ] Add export flow for shareable iTaK skills packs.
- [ ] Keep `SKILL.md` compatibility in docs and tests.
- [ ] Support recursive zip discovery for nested skill directories.
- [ ] Prevent duplicate skill install collisions with clear conflict policy.
- [ ] Add import report output (installed, skipped, rejected, reason).

### PR-AZ4b: Skills trust and security policy

- [ ] Add trusted-source policy config for skill imports (allowlist mode optional).
- [ ] Add mandatory review summary before enabling newly imported skills.
- [ ] Add prompt-injection warning banners in skills UI flows.
- [ ] Add skill package integrity checks (manifest/schema validation).

Target files:

- `webui/static/components/settings/skills/*`
- `security/scanner.py` (or new skill safety validator)
- `docs/skills.md`
- `docs/security.md`

Tests:

- `tests/test_skills_import.py` (new)
- `tests/test_skills_security.py` (new)

### PR-AZ4c: Create-skill workflow parity

- [ ] Add guided "create skill from docs/text" path in UI.
- [ ] Enforce required `SKILL.md` fields before save.
- [ ] Add generated-skill preview and one-click install.

Target files:

- Skills settings components under `webui/static/components/settings/skills/*`
- `skills/` validation helpers (new if needed)
- `docs/skills.md`

---

## Phase 3 (Platform and Ops)

### PR-AZ5: Environment override layer

- [ ] Define iTaK env override prefix (for example `ITAK_SET_*`).
- [ ] Add parser with schema-safe key mapping and validation.
- [ ] Add `doctor` checks for invalid overrides.

Target files:

- `core/models.py`
- `core/doctor.py`
- `main.py` / startup config loader

### PR-AZ6: User-data migration command

- [ ] Add explicit migration helper for user/runtime data moves.
- [ ] Add backup verification and rollback guidance.
- [ ] Add one command migration status report.

Target files:

- `install.py`
- `installers/*`
- `docs/root/INSTALLATION_GUIDE.md`
- `docs/root/DEPLOYMENT_CHECKLIST.md`

---

## Acceptance Criteria

- [ ] Each PR has targeted tests and no regressions in smoke checks.
- [ ] Markdown and no-em-dash checks pass.
- [ ] Docs are updated per merged slice.
- [ ] `docs/root/iTAK_VS_AGENT_ZERO.md` reflects shipped parity after each phase.

---

## Progress Log

- 2026-02-16: v0.9.8 release reviewed and parity plan drafted.
