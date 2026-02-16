# Email Account Creation Feature

## At a Glance
- Audience: Developers and operators configuring autonomous email account workflows.
- Scope: Document autonomous email account workflows, supported actions, and operational constraints.
- Last reviewed: 2026-02-16.

## Quick Start
- Confirm active email provider behavior before relying on automation in production.
- Validate request payloads against current tool action schemas.
- Test both account creation and inbox-check flows end-to-end.

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Preserve exact tool action names and payload shapes when generating email automation calls.
- Verify provider limitations (temporary inbox lifecycle, rate limits) before production use.


## Overview

iTaK can now create its own email addresses automatically using the free Mail.tm API service. **No configuration or API keys required!**

## How It Works

The email tool has been enhanced with two new actions:

### 1. `create_account` - Create a New Email Address

Creates a free, temporary email account instantly:

```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "create_account"
    }
}
```

**Response:**
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

### 2. `check_temp_mail` - Check Emails

Check the inbox of a created email account:

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

**Response:**
```
Found 2 email(s) for itak_a3k9x2m1@mail.tm:

1. 📧 New
   From: notifications@github.com
   Subject: Your GitHub verification code
   Date: 2026-02-14T03:00:00Z
   ID: abc123

2. 📖 Read
   From: welcome@mail.tm
   Subject: Welcome to Mail.tm
   Date: 2026-02-14T02:55:00Z
   ID: def456
```

## Features

✅ **Zero Configuration** - No API keys, no setup, just call and use
✅ **Instant Creation** - Email address created in seconds
✅ **Auto-Generated** - Usernames and passwords generated automatically
✅ **Custom Usernames** - Optionally specify your own username
✅ **Fully Functional** - Can receive emails immediately
✅ **Free Forever** - Uses free Mail.tm API service

## Use Cases

### Automated Testing
Create disposable email addresses for testing signup flows:
```json
{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "create_account",
        "username": "test_signup_flow_001"
    }
}
```

### Development & Debugging
Get temporary emails for development without polluting your personal inbox.

### Anonymous Communication
Receive emails without revealing your personal email address.

### Account Verification
Use for services that require email verification but you don't want to use your main email.

## Limitations

⚠️ **Temporary Nature**
- Emails and accounts may be deleted after inactivity
- Not suitable for important or long-term communications
- For testing and development only

⚠️ **Receive-Only**
- Temporary accounts can only **receive** emails
- Cannot send emails from temp accounts
- For sending, use SMTP configuration with a real email account

⚠️ **No Privacy Guarantees**
- These are public temporary email services
- Don't use for sensitive information
- Anyone with the email and password can access the account

## Technical Details

### Service Used
**Mail.tm** (https://mail.tm/)
- Free, open-source temporary email service
- REST API with no authentication required for basic operations
- Rate limit: 8 requests per second per IP
- Messages auto-expire after period of inactivity

### Implementation
- Uses `httpx` async HTTP client (already in requirements.txt)
- Generates cryptographically secure random passwords
- Returns all credentials needed for future access
- Handles authentication tokens automatically

### Error Handling
- Network errors gracefully handled
- HTTP status codes properly reported
- Detailed error messages for debugging
- Validates credentials before attempting operations

## Examples

### Example 1: Basic Account Creation
```python
# Agent receives request: "Create an email address for me"

{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "create_account"
    }
}

# Result: itak_x9k3m2a1@mail.tm created with auto-generated password
```

### Example 2: Custom Username
```python
# Agent receives: "Create email with username 'myproject2024'"

{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "create_account",
        "username": "myproject2024"
    }
}

# Result: myproject2024@mail.tm created
```

### Example 3: Check for New Messages
```python
# Agent: "Check if myproject2024@mail.tm has any new emails"

{
    "tool_name": "email_tool",
    "tool_args": {
        "action": "check_temp_mail",
        "username": "myproject2024@mail.tm",
        "password": "saved_password_here",
        "limit": 5
    }
}

# Returns: List of received emails with subjects, senders, dates
```

## Integration with Other Tools

The email creation feature works seamlessly with other iTaK capabilities:

### With Browser Agent
```
1. Create temporary email
2. Use browser agent to sign up for service
3. Check temp email for verification code
4. Complete signup process
```

### With Knowledge Graph
```
1. Create email for project
2. Store credentials in knowledge graph
3. Retrieve later when needed
4. Check emails as part of monitoring workflow
```

### With Memory System
```
1. Create email
2. Save email/password to memory
3. Agent remembers credentials for future use
4. Can check emails automatically when needed
```

## Comparison: Before vs After

### Before
❌ Required manual email account setup
❌ Needed to configure SMTP/IMAP
❌ Required sharing personal email credentials
❌ Limited to pre-existing accounts

### After
✅ Creates email accounts on demand
✅ No configuration needed
✅ No personal credentials required
✅ Unlimited accounts (within rate limits)

## Security Considerations

1. **Credentials Storage**: Store email/password securely if needed later
2. **Temporary Use**: Only for non-sensitive, temporary purposes
3. **No PII**: Don't send personally identifiable information to temp emails
4. **Rate Limits**: Respect Mail.tm's 8 QPS rate limit
5. **Terms of Service**: Follow Mail.tm's terms of service

## Troubleshooting

### "No available domains from Mail.tm service"
- Service may be temporarily down
- Try again in a few minutes
- Check Mail.tm status page

### "Failed to authenticate with Mail.tm"
- Double-check email address and password
- Account may have expired due to inactivity
- Create a new account if needed

### Network/Connection Errors
- Check internet connectivity
- Verify firewall isn't blocking api.mail.tm
- Try again after a short delay

## Future Enhancements

Potential improvements for future versions:

1. Support for multiple temp email providers (fallback options)
2. Email notification webhooks
3. Automatic email parsing and extraction
4. Integration with task automation
5. Email forwarding capabilities
6. Custom domain support (if Mail.tm adds it)

## Conclusion

The email account creation feature empowers iTaK to be truly autonomous in managing email-based workflows. No human intervention needed - the agent can create, access, and manage its own email addresses on demand.

**Key Takeaway**: iTaK can now handle any task requiring email without needing pre-configured accounts or credentials!
