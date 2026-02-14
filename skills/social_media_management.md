# Skill: Social Media Management
Category: tool
Tags: social-media, twitter, facebook, linkedin, instagram, api, communication

## When to Use
Use this skill when you need to:
- Post updates to social media platforms
- Read and monitor social media feeds
- Reply to posts, tweets, or comments
- Like or interact with content
- Manage social media presence
- Monitor mentions or engagement
- Automate social media responses

## Supported Platforms
- **Twitter/X** - Post tweets, read timeline, reply, like
- **Facebook** - Post updates, read feed, comment, like
- **LinkedIn** - Share posts, read feed, comment, like
- **Instagram** - Post content, read feed, comment, like

## Steps

### Posting to Social Media
1. Use `social_media_tool` with your chosen platform
2. Set action to "post"
3. Provide message content
4. Post will be published to the platform

### Reading Social Media Feeds
1. Set action to "read"
2. Optionally specify limit for number of posts
3. Returns recent posts from your feed

### Replying to Posts
1. Set action to "reply"
2. Provide the post_id you want to reply to
3. Include your reply message
4. Reply will be posted as a comment

### Liking Content
1. Set action to "like"
2. Provide the post_id to like
3. Like will be registered on the platform

## Configuration

Each platform requires API credentials in `config.json`:

### Twitter/X Configuration
```json
{
    "social_media": {
        "twitter": {
            "api_key": "your-api-key",
            "api_secret": "your-api-secret",
            "access_token": "your-access-token",
            "access_token_secret": "your-access-token-secret"
        }
    }
}
```

### Facebook Configuration
```json
{
    "social_media": {
        "facebook": {
            "access_token": "your-page-access-token"
        }
    }
}
```

### LinkedIn Configuration
```json
{
    "social_media": {
        "linkedin": {
            "access_token": "your-access-token"
        }
    }
}
```

### Instagram Configuration
```json
{
    "social_media": {
        "instagram": {
            "access_token": "your-access-token"
        }
    }
}
```

## Getting API Credentials

### Twitter/X
1. Go to developer.twitter.com
2. Create a new app
3. Generate API keys and access tokens
4. Enable required permissions (read/write)

### Facebook
1. Go to developers.facebook.com
2. Create a new app
3. Get a Page Access Token
4. Add required permissions (pages_manage_posts, etc.)

### LinkedIn
1. Go to linkedin.com/developers
2. Create a new app
3. Request API access
4. Generate access tokens with proper scopes

### Instagram
1. Use Facebook Graph API
2. Connect Instagram Business Account
3. Get access token through Facebook
4. Requires Instagram Business or Creator account

## Examples

### Example 1: Post a tweet
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

### Example 2: Read Facebook feed
```json
{
    "tool_name": "social_media_tool",
    "tool_args": {
        "platform": "facebook",
        "action": "read",
        "limit": 5
    }
}
```

### Example 3: Reply to a LinkedIn post
```json
{
    "tool_name": "social_media_tool",
    "tool_args": {
        "platform": "linkedin",
        "action": "reply",
        "post_id": "12345",
        "message": "Great insight! Thanks for sharing."
    }
}
```

### Example 4: Like an Instagram post
```json
{
    "tool_name": "social_media_tool",
    "tool_args": {
        "platform": "instagram",
        "action": "like",
        "post_id": "67890"
    }
}
```

### Example 5: Post to multiple platforms
First post to Twitter:
```json
{
    "tool_name": "social_media_tool",
    "tool_args": {
        "platform": "twitter",
        "action": "post",
        "message": "New blog post is live!"
    }
}
```

Then post to LinkedIn:
```json
{
    "tool_name": "social_media_tool",
    "tool_args": {
        "platform": "linkedin",
        "action": "post",
        "message": "New blog post is live! Check it out."
    }
}
```

## Common Errors

| Error | Fix |
|-------|-----|
| API credentials not configured | Add platform config to config.json |
| Authentication failed | Regenerate access tokens, check expiration |
| Rate limit exceeded | Wait before making more requests, respect API limits |
| Invalid post_id | Verify the post/tweet ID is correct |
| Permission denied | Check API permissions/scopes for your app |
| Platform not supported | Use: twitter, facebook, linkedin, or instagram |

## Best Practices

1. **Rate Limits**: Respect platform API rate limits
2. **Content**: Follow each platform's content policies
3. **Authentication**: Regularly refresh access tokens
4. **Privacy**: Don't share API keys in logs or messages
5. **Testing**: Test with personal accounts first
6. **Monitoring**: Watch for API changes and updates
7. **Compliance**: Follow platform terms of service

## Security Notes
- Store API credentials securely in config.json
- Never commit credentials to version control
- Use environment variables for sensitive data
- Regularly rotate access tokens
- Monitor API usage for suspicious activity
- Use read-only tokens when write access isn't needed
