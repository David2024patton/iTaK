# Adapters Reference

## At a Glance
- Audience: Users, operators, developers, and contributors working with iTaK.
- Scope: This page explains `Adapters Reference`.
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


> Every communication adapter explained with setup instructions and examples.

## Overview

Adapters connect iTaK to messaging platforms. They translate between platform-specific message formats and the agent's `monologue()` method.

```
Discord  ─┐
Telegram ─┤──> BaseAdapter ──> Agent.monologue() ──> BaseAdapter ──> Platform
Slack    ─┤
CLI      ─┘
```

All adapters inherit from `BaseAdapter` and share:
- Output Guard integration (PII/secret scrubbing)
- Progress broadcasting
- Message handling pipeline

---

## base.py - BaseAdapter

**Lines:** ~100 | **The shared interface.**

### Key Methods

| Method | Purpose |
|--------|---------|
| `__init__(agent, config)` | Store agent ref, register for progress updates |
| `start()` | Start listening for messages |
| `stop()` | Graceful shutdown |
| `send_message(content)` | Send to user (override in subclass) |
| `edit_message(id, content)` | Edit existing message |
| `_sanitize_output(text)` | Run Output Guard on text |
| `_on_progress(event, data)` | Handle progress events |
| `handle_message(user_id, content)` | Process incoming message through agent |

### Output Guard Integration

Every adapter inherits `_sanitize_output()`:

```python
def _sanitize_output(self, text: str) -> str:
    if hasattr(self.agent, 'output_guard') and self.agent.output_guard:
        result = self.agent.output_guard.sanitize(text)
        return result.sanitized_text
    return text
```

**Subclasses MUST call `_sanitize_output()` before sending any text to the user.** This is the last line of defense against PII/secret leaks.

---

## cli.py - Terminal Adapter

**Lines:** ~85 | **Local terminal interface for development.**

### Usage
```bash
python -m app.main --adapter cli
```

```
[iTaK] Ready. Type your message:
> What's the weather like?
[iTaK] Thinking...
[iTaK] Let me search for that...
[iTaK] The weather in your area is...
>
```

### Features
- Colorized output (green for agent, blue for status)
- Progress updates shown inline
- Ctrl+C for graceful shutdown
- No authentication needed (single user)

---

## discord.py - Discord Bot

**Lines:** ~300 | **Full Discord bot with slash commands.**

### Setup

1. Create a bot at [discord.dev](https://discord.com/developers/applications)
2. Add the token to `.env`:
```bash
DISCORD_TOKEN=your_token_here
```
3. Configure in `config.json`:
```json
{
    "adapters": {
        "discord": {
            "enabled": true,
            "prefix": "!",
            "allowed_channels": [],
            "allowed_roles": [],
            "typing_indicator": true,
            "max_message_length": 2000
        }
    }
}
```

### Features

| Feature | Description |
|---------|-------------|
| Prefix commands | `!ask how do I...` |
| Mentions | `@iTaK how do I...` |
| DMs | Direct messages to the bot |
| Threads | Replies in threads for long conversations |
| Reactions | Emoji reactions for status (thumbsup, hourglass) |
| Embeds | Rich embeds for formatted responses |
| File attachments | Process images and files |
| Typing indicator | Shows "iTaK is typing..." while processing |
| Message splitting | Auto-splits responses > 2000 chars |

### Multi-user

Discord users are identified by their Discord ID. Combined with the `users.py` RBAC system:
- Unknown users get the `unknown_user_role` (default: `user`)
- Registered users get their assigned role
- Owner users can manage other users via commands

---

## telegram.py - Telegram Bot

**Lines:** ~230 | **Telegram bot with inline keyboard support.**

### Setup

1. Create a bot via [@BotFather](https://t.me/botfather)
2. Add the token to `.env`:
```bash
TELEGRAM_TOKEN=your_token_here
```
3. Configure in `config.json`:
```json
{
    "adapters": {
        "telegram": {
            "enabled": true,
            "allowed_chat_ids": [],
            "typing_indicator": true,
            "parse_mode": "Markdown"
        }
    }
}
```

### Features
- Private and group chats
- Markdown formatting in responses
- Typing indicator
- Photo/file processing
- Inline keyboards for interactive responses

---

## slack.py - Slack Bot

**Lines:** ~100 | **Slack bot using Socket Mode.**

### Setup

1. Create a Slack App at [api.slack.com](https://api.slack.com/apps)
2. Enable Socket Mode
3. Add tokens to `.env`:
```bash
SLACK_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
```
4. Configure in `config.json`:
```json
{
    "adapters": {
        "slack": {
            "enabled": true,
            "allowed_channels": []
        }
    }
}
```

### Features
- Socket Mode (no public URL needed)
- Channel/DM messaging
- Thread support
- Slack Block Kit formatting

---

## Running Multiple Adapters

You can run multiple adapters simultaneously:

```python
# main.py
agent = Agent(config=config)
await agent.startup()

# Start all enabled adapters
if config["adapters"].get("discord", {}).get("enabled"):
    discord = DiscordAdapter(agent, config["adapters"]["discord"])
    asyncio.create_task(discord.start())

if config["adapters"].get("telegram", {}).get("enabled"):
    telegram = TelegramAdapter(agent, config["adapters"]["telegram"])
    asyncio.create_task(telegram.start())

# CLI always available for debugging
cli = CLIAdapter(agent, {})
await cli.start()
```

The same agent instance serves all platforms. Memory is shared across all adapters.
