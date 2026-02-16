# Screenshot Capture Checklist

Use this checklist to recapture all UI images in a clean, repeatable way.

## Capture Standard
- Resolution: `1920x1080`
- Browser zoom: `100%`
- Theme: default project theme
- Data state: realistic but sanitized (no secrets, no personal identifiers)
- Window state: no devtools, no debug overlays, no temporary banners
- Naming: use filenames exactly as listed below

## Capture Order

### README-critical (capture first)
- [ ] `dashboard-monitor.png` — Dashboard Monitor tab (used in README)
- [ ] `dashboard-mission-control.png` — Mission Control view (used in README)

### Dashboard
- [ ] `dashboard-home.png` — Dashboard landing state
- [ ] `dashboard-fullpage.png` — Full-page dashboard context
- [ ] `dashboard-scrolled.png` — Scrolled dashboard section state
- [ ] `dashboard-api-health.png` — API health panel visible

### Agent Zero alignment views
- [ ] `agentzero-dashboard-home.png` — Agent Zero styled home/dashboard
- [ ] `agentzero-dashboard-settings.png` — Agent Zero settings panel
- [ ] `agentzero-dashboard-sidebar-tasks.png` — Sidebar + tasks section
- [ ] `agentzero-dashboard-clean-sync.png` — Clean sync/ready state

### UI flow set
- [ ] `ui-01-chat-main.png` — Main chat view
- [ ] `ui-02-memory-dashboard.png` — Memory dashboard
- [ ] `ui-03-scheduler.png` — Scheduler section
- [ ] `ui-04-settings-agent.png` — Agent settings
- [ ] `ui-05-settings-skills.png` — Skills settings
- [ ] `ui-06-settings-external-services.png` — External services settings
- [ ] `ui-07-settings-mcp-a2a.png` — MCP/A2A settings
- [ ] `ui-08-settings-developer.png` — Developer settings
- [ ] `ui-09-settings-backup-restore.png` — Backup/restore settings
- [ ] `ui-10-launchpad-section.png` — Launchpad section
- [ ] `ui-11-tasks-section.png` — Tasks section
- [ ] `ui-12-preferences-section.png` — Preferences section
- [ ] `ui-13-notifications.png` — Notifications section
- [ ] `ui-14-file-browser.png` — File browser view
- [ ] `ui-15-projects.png` — Projects view

## Final QA Before Commit
- [ ] All files are PNG format
- [ ] Filenames match checklist exactly
- [ ] No sensitive info visible
- [ ] Core text is readable at normal zoom
- [ ] README images render correctly after push

## Automated Validation
- Run exact-set validation: `tools/validate_screenshots.sh`
- Allow extra PNGs temporarily: `tools/validate_screenshots.sh --allow-extra`
