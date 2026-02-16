# iTaK New Tools & Skills - Setup Guide

## At a Glance
- Audience: Users, operators, developers, and contributors working with iTaK.
- Scope: This page explains `iTaK New Tools & Skills - Setup Guide`.
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


This document provides setup instructions for the newly added tools and skills.

## Overview

iTaK now includes comprehensive support for:
- **Git/GitHub Operations** - Clone, commit, push, pull repositories
- **Email Management** - Send/read emails via SMTP/IMAP
- **Social Media** - Post, read, reply, like on Twitter, Facebook, LinkedIn, Instagram
- **Web Search** - Already uses SearXNG for privacy-focused search

## Git Tool Setup

### Features
- Clone repositories
- Check status and view diffs
- Add, commit, and push changes
- Pull updates and switch branches
- View commit history

### Configuration
No special configuration needed - uses system Git installation.

### Example Usage
```json
{
    "tool_name": "git_tool",
    "tool_args": {
        "action": "clone",
        "repo": "https://github.com/user/repo.git"
    }
}
```

## Email Tool Setup

### Features
- Send emails via SMTP
- Read emails via IMAP
- List email folders
- Support for Gmail, Outlook, and custom servers

### Configuration
Add to `config.json`:
```json
{
    "email": {
        "smtp": {
            "server": "smtp.gmail.com",
            "port": 587,
            "username": "your-email@gmail.com",
            "password": "your-app-password"
        },
        "imap": {
            "server": "imap.gmail.com",
            "port": 993,
            "username": "your-email@gmail.com",
            "password": "your-app-password"
        }
    }
}
```

### Gmail Setup
1. Enable 2-factor authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an App Password
4. Use the generated password (not your regular password) in config

### Outlook/Office365 Setup
```json
{
    "email": {
        "smtp": {
            "server": "smtp.office365.com",
            "port": 587,
            "username": "your-email@outlook.com",
            "password": "your-password"
        },
        "imap": {
            "server": "outlook.office365.com",
            "port": 993,
            "username": "your-email@outlook.com",
            "password": "your-password"
        }
    }
}
```

### Example Usage
```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "send",
        "to": "recipient@example.com",
        "subject": "Hello from iTaK",
        "body": "This is an automated message from iTaK."
    }
}
```

## Social Media Tool Setup

### Supported Platforms
- **Twitter/X** - Post tweets, read timeline, reply, like
- **Facebook** - Post updates, read feed, comment, like
- **LinkedIn** - Share posts, read feed, comment, like
- **Instagram** - Post content, read feed, comment, like

### Configuration
Add to `config.json`:
```json
{
    "social_media": {
        "twitter": {
            "api_key": "your-api-key",
            "api_secret": "your-api-secret",
            "access_token": "your-access-token",
            "access_token_secret": "your-access-token-secret"
        },
        "facebook": {
            "access_token": "your-page-access-token"
        },
        "linkedin": {
            "access_token": "your-access-token"
        },
        "instagram": {
            "access_token": "your-access-token"
        }
    }
}
```

### Twitter/X API Setup
1. Go to https://developer.twitter.com/
2. Create a new app
3. Generate API keys and access tokens
4. Enable read/write permissions
5. Add credentials to config.json

### Facebook API Setup
1. Go to https://developers.facebook.com/
2. Create a new app
3. Get a Page Access Token
4. Add required permissions (pages_manage_posts, pages_read_engagement)
5. Add token to config.json

### LinkedIn API Setup
1. Go to https://www.linkedin.com/developers/
2. Create a new app
3. Request API access
4. Generate access tokens with required scopes (w_member_social, r_liteprofile)
5. Add token to config.json

### Instagram API Setup
1. Use Facebook Graph API
2. Connect Instagram Business Account
3. Get access token through Facebook
4. Requires Instagram Business or Creator account
5. Add token to config.json

### Example Usage
```json
{
    "tool_name": "social_media_tool",
    "tool_args": {
        "platform": "twitter",
        "action": "post",
        "message": "Hello from iTaK! 🤖"
    }
}
```

## Web Search (SearXNG)

### Configuration
Web search already uses SearXNG if configured:
```json
{
    "searxng": {
        "url": "https://your-searxng-instance.com"
    }
}
```

Falls back to DuckDuckGo if SearXNG is not configured.

## Security Best Practices

### Credential Storage
- Store all credentials in `config.json`
- Use environment variables for sensitive data
- Never commit credentials to version control
- Add `config.json` to `.gitignore`

### API Keys
- Use App Passwords for email (not account passwords)
- Regularly rotate API keys and tokens
- Use read-only permissions when write access isn't needed
- Monitor API usage for suspicious activity

### Rate Limits
- Respect platform API rate limits
- Implement backoff strategies for retries
- Monitor quota usage

## Testing

Run the test suite to verify your setup:
```bash
python -m pytest tests/test_tools.py -v
```

All 17 tests should pass:
- 4 Git tool tests
- 4 Email tool tests
- 9 Social Media tool tests

## Skill-Tool Parity

Every tool has a matching skill document that teaches the agent when and how to use it:

| Tool | Skill | Prompt |
|------|-------|--------|
| `git_tool.py` | `git_operations.md` | `agent.system.tool.git.md` |
| `email_tool.py` | `email_management.md` | `agent.system.tool.email.md` |
| `social_media_tool.py` | `social_media_management.md` | `agent.system.tool.social_media.md` |

## Troubleshooting

### Git Tool
- **Error: Not a git repository** - Initialize with `git init` or clone first
- **Error: Permission denied** - Check SSH keys or HTTPS credentials

### Email Tool
- **Error: Authentication failed** - Use App Password for Gmail
- **Error: Connection timeout** - Verify server and port settings
- **Error: TLS error** - Use port 587 for SMTP, 993 for IMAP

### Social Media Tool
- **Error: API credentials not configured** - Add credentials to config.json
- **Error: Authentication failed** - Regenerate tokens, check expiration
- **Error: Rate limit exceeded** - Wait before making more requests

## Current Implementation Status

### Git Tool
✅ Fully implemented and tested

### Email Tool
✅ Fully implemented and tested

### Social Media Tool
⚠️ Framework complete with demo mode
- Core structure and validation: ✅ Complete
- API integration: 🔧 Ready for implementation
- Currently returns demo placeholders
- Full API integration requires actual credentials

To activate full social media features, add API credentials and implement the actual API calls in each platform method.

## Next Steps

1. Add your API credentials to `config.json`
2. Test each tool with your credentials
3. Customize rate limits and timeouts as needed
4. Implement full API integration for social media platforms
5. Add any platform-specific features you need

## Support

For issues or questions:
- Check the skill documents in `skills/`
- Review the prompt files in `prompts/`
- See the example configuration in `config.json.example`
- Run tests to verify functionality
