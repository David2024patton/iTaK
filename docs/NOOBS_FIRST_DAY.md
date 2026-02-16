# iTaK Noob First Day Guide

## At a Glance
- Audience: Beginners, operators, and AI agents navigating iTaK documentation quickly.
- Scope: This page explains `iTaK Noob First Day Guide`.
- Last reviewed: 2026-02-16.

## Quick Start
- Complete installation first: [installation.md](installation.md).
- Run your first launch path: [getting-started.md](getting-started.md).
- Validate health checks from [root/QUICK_START.md](root/QUICK_START.md).

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Follow role-based paths first, then dive into module-specific deep references.
- Keep links and commands current so both humans and automation can rely on them.


> If this is your first time touching iTaK, follow this page exactly.

## Goal

By the end of this guide, you will:

- Install iTaK
- Open the Web UI
- Send your first message
- Run a quick health/smoke check

---

## Step 1: Install

```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
python install.py
```

What this does:

- Detects OS/platform
- Installs dependencies
- Creates starter config files
- Starts iTaK services

---

## Step 2: Open the UI

Open your browser to:

- `http://localhost:8000`

If you see the dashboard, you are good.

---

## Step 3: Configure API Key

In Settings, add at least one model provider key (for example Gemini/OpenAI/Anthropic), then save.

---

## Step 4: Test Basic Chat

Try this in chat:

- `Hello iTaK, what can you do?`

Expected result: a normal response, not an error.

---

## Step 5: Run Smoke Tests (One Click)

In Web UI:

- Settings → External Services → System Smoke Tests
- Click `Run All`

This runs:

- endpoint checks
- memory roundtrip
- chat roundtrip

---

## Common Problems

### Port already in use

- Stop conflicting service or run iTaK on a different port.

### API key errors

- Re-open Settings, re-paste key, save, and retry.

### Docker issues

- Ensure Docker is running (`docker ps`).

---

## Next Docs

- Full setup: [root/INSTALLATION_GUIDE.md](root/INSTALLATION_GUIDE.md)
- Testing: [root/TESTING.md](root/TESTING.md)
- Tools: [tools.md](tools.md)
- API/WebUI: [webui.md](webui.md)
