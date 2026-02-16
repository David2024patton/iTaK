# Tool: email_tool

## When to Use

Use this tool when the user needs to:

- **Create a new email address** (free, temporary, no setup required)
- Check emails from temporary email accounts
- Send emails
- Read and check emails  
- List email folders
- Manage email communications
- Set up automated responses

## Arguments

| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| action | str | Yes | Email action: create_account, check_temp_mail, send, read, list_folders |
| username | str | No | Username for account creation or email address for checking temp mail |
| password | str | No | Password for account creation or checking temp mail |
| to | str | No | Recipient email (required for send) |
| subject | str | No | Email subject (required for send) |
| body | str | No | Email body content (required for send) |
| from_email | str | No | Sender email (default: configured username) |
| folder | str | No | IMAP folder name (default: INBOX) |
| limit | int | No | Number of emails to retrieve (default: 10) |

## Configuration Required

### For Creating Email Accounts

**No configuration needed!** The `create_account` action uses the free Mail.tm API.

### For SMTP/IMAP (Existing Accounts)

Only required for sending/reading from existing email providers:

```json
{
    "email": {
        "smtp": {
            "server": "smtp.gmail.com",
            "port": 587,
            "username": "user@gmail.com",
            "password": "app-password"
        },
        "imap": {
            "server": "imap.gmail.com",
            "port": 993,
            "username": "user@gmail.com",
            "password": "app-password"
        }
    }
}
```

## Examples

### Example 1: Create a new email address (no config needed!)

```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "create_account"
    }
}
```

### Example 2: Create email with custom username

```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "create_account",
        "username": "mybot2024"
    }
}
```

### Example 3: Check temporary email inbox

```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "check_temp_mail",
        "username": "itak_a3k9x2m1@mail.tm",
        "password": "xK9#mP2$vR8@qL5!",
        "limit": 10
    }
}
```

### Example 4: Send an email (requires SMTP config)

```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "send",
        "to": "recipient@example.com",
        "subject": "Meeting Reminder",
        "body": "Don't forget about our meeting tomorrow at 2pm."
    }
}
```

### Example 5: Read recent emails (requires IMAP config)

```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "read",
        "folder": "INBOX",
        "limit": 5
    }
}
```

### Example 6: List folders (requires IMAP config)

```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "list_folders"
    }
}
```

## Tips

- **Create account first** - No configuration needed, just call create_account
- Store the returned email address and password to check emails later
- Temporary email accounts are free but not permanent (may be deleted)
- For Gmail SMTP/IMAP, use App Passwords instead of account password
- Check that SMTP/IMAP access is enabled in email provider settings
- Use secure storage for credentials (never hardcode)
- Temporary emails are for testing only - not secure for sensitive data
