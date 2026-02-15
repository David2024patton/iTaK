# Skill: Email Management
Category: tool
Tags: email, smtp, imap, communication, mail, account-creation

## When to Use
Use this skill when you need to:
- **Create your own email address** (temporary, free)
- Send emails programmatically
- Read and check emails
- List email folders
- Manage email communications
- Set up automated email responses
- Monitor incoming messages

## Steps

### Creating Your Own Email Account
1. Use `email_tool` with action "create_account"
2. Optionally provide a username (auto-generated if not provided)
3. System creates a free temporary email via Mail.tm API
4. Returns email address, password, and auth token
5. **No configuration required** - works out of the box!

### Checking Temporary Email
1. Use action "check_temp_mail"
2. Provide the username (email address) and password from creation
3. Returns list of received emails

### Sending an Email
1. Use `email_tool` with action "send"
2. Provide recipient address (to)
3. Specify subject and body content
4. Email will be sent via configured SMTP server

### Reading Emails (IMAP)
1. Use action "read" to fetch emails
2. Optionally specify folder (default: INBOX)
3. Set limit for number of emails to retrieve
4. Emails will be retrieved via IMAP

### Listing Email Folders
1. Use action "list_folders"
2. Returns all available IMAP folders
3. Use folder names with "read" action

## Configuration

### For Creating Email Accounts (Temporary)
**No configuration needed!** The `create_account` action uses the free Mail.tm API service which requires no API keys or credentials. Just call it and get a working email address.

### For SMTP/IMAP (Existing Accounts)
The email tool requires SMTP and IMAP configuration in `config.json` for sending/reading from existing email providers:

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

### Example 1: Create your own email address
```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "create_account"
    }
}
```

Response:
```
✅ Successfully created temporary email account!

Email Address: itak_a3k9x2m1@mail.tm
Password: xK9#mP2$vR8@qL5!
Account ID: 507f1f77bcf86cd799439011
Auth Token: eyJhbGci...

⚠️ IMPORTANT:
- This is a temporary email address from Mail.tm
- Emails may be deleted after a period of inactivity
- Use 'check_temp_mail' action to read emails
- Store these credentials securely
```

### Example 2: Check temporary email inbox
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

### Example 3: Create account with custom username
```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "create_account",
        "username": "mybot2024"
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
        "subject": "Status Update",
        "body": "The task has been completed successfully."
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

### Example 6: List all folders (requires IMAP config)
```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "list_folders"
    }
}
```

## Common Errors

| Error | Fix |
|-------|-----|
| No available domains from Mail.tm | Service may be temporarily down, try again later |
| Failed to authenticate with Mail.tm | Check username and password are correct |
| SMTP configuration not found | Add email.smtp settings to config.json for sending |
| IMAP configuration not found | Add email.imap settings to config.json for reading |
| Authentication failed | Check username/password, use App Password for Gmail |
| Connection timeout | Verify server address and port, check firewall |
| TLS error | Ensure using correct port (587 for SMTP, 993 for IMAP) |
| Folder not found | Use list_folders action to see available folders |

## Temporary Email Features

**Mail.tm Service:**
- ✅ Completely free, no API key required
- ✅ Instant account creation
- ✅ Can receive emails immediately
- ✅ No signup or registration needed
- ⚠️ Temporary - emails auto-delete after inactivity
- ⚠️ For testing/development, not production use
- ⚠️ Cannot send emails from temp accounts (receive-only)

## Security Notes
- Never hardcode passwords in code
- Temporary email accounts are public - don't use for sensitive data
- Use App Passwords instead of account passwords for Gmail
- Store credentials securely in config.json
- Consider using environment variables for sensitive data
- Enable 2FA on permanent email accounts
- Temporary emails are not secure - use for testing only
