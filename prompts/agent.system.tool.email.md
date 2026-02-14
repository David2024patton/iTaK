# Tool: email_tool

## When to Use
Use this tool when the user needs to:
- Send emails
- Read and check emails  
- List email folders
- Manage email communications
- Set up automated responses

## Arguments
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| action | str | Yes | Email action: send, read, list_folders |
| to | str | No | Recipient email (required for send) |
| subject | str | No | Email subject (required for send) |
| body | str | No | Email body content (required for send) |
| from_email | str | No | Sender email (default: configured username) |
| folder | str | No | IMAP folder name (default: INBOX) |
| limit | int | No | Number of emails to retrieve (default: 10) |

## Configuration Required
The tool requires SMTP and IMAP settings in config.json:
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

### Example 1: Send an email
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

### Example 2: Read recent emails
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

### Example 3: List folders
```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "list_folders"
    }
}
```

## Tips
- For Gmail, use App Passwords instead of account password
- Check that SMTP/IMAP access is enabled in email provider settings
- Use secure storage for credentials (never hardcode)
- Test with a personal email first before automating
