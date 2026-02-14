# Skill: Email Management
Category: tool
Tags: email, smtp, imap, communication, mail

## When to Use
Use this skill when you need to:
- Send emails programmatically
- Read and check emails
- List email folders
- Manage email communications
- Set up automated email responses
- Monitor incoming messages

## Steps

### Sending an Email
1. Use `email_tool` with action "send"
2. Provide recipient address (to)
3. Specify subject and body content
4. Email will be sent via configured SMTP server

### Reading Emails
1. Use action "read" to fetch emails
2. Optionally specify folder (default: INBOX)
3. Set limit for number of emails to retrieve
4. Emails will be retrieved via IMAP

### Listing Email Folders
1. Use action "list_folders"
2. Returns all available IMAP folders
3. Use folder names with "read" action

## Configuration

The email tool requires SMTP and IMAP configuration in `config.json`:

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
1. Enable 2-factor authentication
2. Generate an App Password (not your regular password)
3. Use App Password in configuration
4. SMTP: smtp.gmail.com:587
5. IMAP: imap.gmail.com:993

### Outlook/Office365 Setup
1. SMTP: smtp.office365.com:587
2. IMAP: outlook.office365.com:993
3. Use your email and password

## Examples

### Example 1: Send an email
```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "send",
        "to": "recipient@example.com",
        "subject": "Status Update",
        "body": "The task has been completed successfully."
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

### Example 3: List all folders
```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "list_folders"
    }
}
```

### Example 4: Check specific folder
```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "read",
        "folder": "Sent",
        "limit": 10
    }
}
```

## Common Errors

| Error | Fix |
|-------|-----|
| SMTP configuration not found | Add email.smtp settings to config.json |
| IMAP configuration not found | Add email.imap settings to config.json |
| Authentication failed | Check username/password, use App Password for Gmail |
| Connection timeout | Verify server address and port, check firewall |
| TLS error | Ensure using correct port (587 for SMTP, 993 for IMAP) |
| Folder not found | Use list_folders action to see available folders |

## Security Notes
- Never hardcode passwords in code
- Use App Passwords instead of account passwords
- Store credentials securely in config.json
- Consider using environment variables for sensitive data
- Enable 2FA on email accounts
