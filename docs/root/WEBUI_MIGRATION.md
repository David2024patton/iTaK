# WebUI Migration to Agent Zero Architecture

## At a Glance
- Audience: Developers integrating channels, APIs, and system architecture components.
- Scope: Explain component boundaries, integration points, and expected behavior across interfaces.
- Last reviewed: 2026-02-16.

## Quick Start
- Identify the integration boundary first (adapter, API endpoint, or UI component).
- Trace implementation details from [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md).
- Validate behavior with smoke checks after each configuration change.

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Use explicit endpoint names, adapter flags, and file paths for automation tasks.
- Note root endpoints vs `/api/*` endpoints to avoid integration mismatches.


## Summary

This PR successfully migrates the iTaK webui from a vanilla JavaScript implementation to Agent Zero's Alpine.js-based component architecture, as specified in `gameplan.md` §4.

## What Changed

### Before
- **Architecture**: Vanilla JavaScript (no framework)
- **Files**: 3 files (index.html, app.js, style.css)
- **Lines of Code**: 1,318 total
- **Structure**: Monolithic single-file application
- **Features**: Basic monitoring dashboard with stats, logs, and chat

### After
- **Architecture**: Alpine.js reactive framework with component-based design
- **Files**: 439 files across 58 directories
- **Structure**: Modular components with Alpine stores
- **Features**: Full Agent Zero UI including:
  - Chat interface with attachments and speech
  - Sidebar with chat history and tasks
  - Settings panel (agent, MCP, skills, secrets, backup)
  - Projects system (Git-based workspaces)
  - Modals (file browser, editor, scheduler, memory dashboard)
  - Notification system with toasts
  - Welcome screen
  - Responsive design with mobile support

## Files Copied from Agent Zero

All 439 files from [Agent Zero's webui directory](https://github.com/frdel/agent-zero/tree/main/webui) have been copied:

### Components (`/webui/static/components/`)
- `chat/` - Chat interface, attachments, input, speech, navigation
- `sidebar/` - Left sidebar with chats, tasks, preferences
- `settings/` - Agent configuration, MCP, skills, speech, secrets, backup
- `modals/` - Context, file browser/editor, history, memory, scheduler
- `notifications/` - Toast notifications and notification store
- `projects/` - Project management (Git repositories)
- `welcome/` - Welcome screen
- `messages/` - Process groups, action buttons
- `tooltips/` - Tooltip system
- `sync/` - Sync status tracking

### JavaScript Modules (`/webui/static/js/`)
- `index.js` - Main app entry point
- `AlpineStore.js` - Store management
- `api.js` - API client
- `components.js` - Component loader
- `messages.js` - Message rendering
- `websocket.js` - WebSocket handling
- `modals.js` - Modal system
- `shortcuts.js` - Keyboard shortcuts
- `speech_browser.js` - Text-to-speech
- `device.js` - Device detection
- Plus: CSS utilities, sleep, scroller, timeout, transformers, service worker

### Stylesheets (`/webui/static/css/`)
- `index.css` - Main stylesheet with design tokens, dark/light mode
- `messages.css`, `modals.css`, `notifications.css`, `settings.css`
- `buttons.css`, `tables.css`, `toast.css`, `speech.css`
- `scheduler.css`, `scheduler-datepicker.css`

### Vendor Libraries (`/webui/static/vendor/`)
- **Alpine.js** - Reactive framework (65KB)
- **ACE Editor** - Full code editor with 100+ language modes (5.2MB)
- **KaTeX** - Math rendering (460KB)
- **Flatpickr** - Date/time picker (50KB)
- **Marked** - Markdown parser (35KB)
- **Socket.IO** - Real-time communication (150KB)
- **QRCode** - QR code generation (15KB)
- **Google Icons** - Icon font (400KB)

## Backend Compatibility

### Current Status: ⚠️ Integration Needed

The Agent Zero webui expects a **Flask + Socket.IO** backend, but iTaK uses **FastAPI + plain WebSocket**.

**What's Been Done**:
- ✅ Added `python-socketio>=5.11.0` to `requirements.txt`
- ✅ All frontend files copied and ready
- ✅ Alpine.js framework initialized

**What Remains** (follow-up work):
- Integrate Socket.IO server into `webui/server.py`
- Map Agent Zero's API endpoints to iTaK's backend
- Test chat, settings, and core functionality

See `docs/WEBUI_AGENT_ZERO_STATUS.md` for detailed status.

## Testing

The webui files are in place, but full functionality requires backend integration (Socket.IO).

**Current state**: 
- HTML/CSS/JS structure complete
- Page will load with Alpine.js framework
- Backend communication will fail until Socket.IO integration is complete

## Next Steps

1. **Integrate Socket.IO** into FastAPI backend (`webui/server.py`)
2. **Map API endpoints** to match Agent Zero's expectations
3. **Test core features**: chat, settings, memory, tasks
4. **Add iTaK-specific features**: Mission Control tab, Swarm UI, Memory layer visualization
5. **Update branding**: Replace remaining "Agent Zero" references with "iTaK"

## File Structure

```
webui/
├── static/
│   ├── index.html          # Alpine.js-based UI shell
│   ├── index.js            # Main app entry point
│   ├── index.css           # Design tokens and base styles
│   ├── components/         # 58 component directories
│   ├── js/                 # 21 JavaScript modules
│   ├── css/                # 10 stylesheets
│   ├── vendor/             # Alpine, ACE, KaTeX, Socket.IO, etc.
│   ├── public/             # 40+ SVG icons
│   ├── static_backup/      # Original vanilla JS webui (backup)
│   ├── app.js.old          # Original app.js (backup)
│   └── style.css.old       # Original style.css (backup)
├── server.py               # FastAPI backend (needs Socket.IO integration)
└── __init__.py
```

## Dependency Changes

### Added to `requirements.txt`
```python
python-socketio>=5.11.0,<6.0.0
```

This enables Socket.IO support for the Agent Zero webui's real-time communication.

## Documentation

- **`docs/WEBUI_AGENT_ZERO_STATUS.md`** - Detailed migration status, progress tracking, and remaining work

## Related Issues

Addresses the requirement from `gameplan.md` §4:
> "Implementation: Fork Agent Zero's `webui/` directory. Don't build from scratch - Agent Zero already has a complete Alpine.js dashboard with chat, settings, sidebar, modals, notifications, projects, and WebSocket streaming."

## Question Answered

**Q**: "the webui was supposed to copy the agent zero webui. does it do that?"

**A**: **YES** - The webui structure has been completely replaced with Agent Zero's architecture. All 439 files have been copied. The frontend is ready; backend integration (Socket.IO) is the next step.

---

**Migration Progress**: ~60% complete (structure ✅, backend integration pending)
