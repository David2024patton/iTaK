# Skills Reference

## At a Glance
- Audience: Developers and contributors authoring, maintaining, and mapping iTaK skills.
- Scope: This page explains `Skills Reference`.
- Last reviewed: 2026-02-16.

## Quick Start
- Locate the owning module and expected inputs before editing behavior.
- Cross-check data flow with [root/DATABASES.md](root/DATABASES.md) when state is involved.
- Re-run focused tests after updates to confirm no regression in tool contracts.

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Match skill intent to concrete tool capabilities before proposing workflow changes.
- Keep filename-based discovery assumptions explicit when adding or renaming skills.


> All skills that ship with iTaK, plus how to create your own.

## Overview

Skills are markdown knowledge files in `skills/`. They teach the agent HOW to do things without writing code. The agent auto-discovers them by keyword-matching filenames and content.

**Skills = knowledge. Tools = code.** A skill teaches the agent strategy and best practices. A tool gives it the ability to execute.

---

## Built-in Skills

| Skill | File | Matches With Tool |
|-------|------|-------------------|
| Code Execution | `code_execution.md` | `code_execution.py` |
| Web Research | `web_research.md` | `web_search.py` (uses SearXNG) |
| Browser Agent | `browser_agent.md` | `browser_agent.py` |
| Task Delegation | `delegation.md` | `delegate_task.py` |
| Knowledge Graph | `knowledge_graph.md` | `knowledge_tool.py` |
| Git Operations | `git_operations.md` | `git_tool.py` |
| Email Management | `email_management.md` | `email_tool.py` |
| Social Media Management | `social_media_management.md` | `social_media_tool.py` |
| Docker Operations | `docker_ops.md` | `code_execution.py` (terminal) |
| Linux Commands | `os_linux.md` | `code_execution.py` (terminal) |
| macOS Commands | `os_macos.md` | `code_execution.py` (terminal) |
| Windows Commands | `os_windows.md` | `code_execution.py` (terminal) |

> Every tool now has a matching skill. The OS-specific skills are loaded automatically based on the detected operating system.

---

## Skill-Tool Parity

The system maintains **1:1 parity** between tools and skills:

```
tools/code_execution.py    <-->  skills/code_execution.md
tools/web_search.py        <-->  skills/web_research.md (uses SearXNG)
tools/browser_agent.py     <-->  skills/browser_agent.md
tools/delegate_task.py     <-->  skills/delegation.md
tools/knowledge_tool.py    <-->  skills/knowledge_graph.md
tools/git_tool.py          <-->  skills/git_operations.md
tools/email_tool.py        <-->  skills/email_management.md
tools/social_media_tool.py <-->  skills/social_media_management.md
tools/memory_save.py       <-->  (covered in web_research.md)
tools/memory_load.py       <-->  (covered in web_research.md)
tools/response.py          <-->  (no skill needed - always used)
```

---

## Creating a New Skill

See [SKILL.md](../skills/SKILL.md) for the full template. Quick version:

```markdown
# Skill: [Name]
Category: [code | devops | research | trading | os | tool]
Tags: [tag1, tag2, tag3]

## When to Use
Trigger conditions.

## Steps
1. Do this
2. Then that

## Examples
### Example 1
(show concrete usage)

## Common Errors
| Error | Fix |
|-------|-----|
| ... | ... |
```

Drop it in `skills/` and the agent finds it automatically.

---

## When to Create a Skill vs a Tool

| Need | Create |
|------|--------|
| Teach the agent a new strategy/workflow | **Skill** (markdown) |
| Give the agent a new capability | **Tool** (Python) |
| Add domain knowledge | **Skill** |
| Connect to an external API | **Tool** |
| OS-specific commands | **Skill** |
| New file format processing | **Tool** |
