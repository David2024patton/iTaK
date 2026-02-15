# Tool: social_media_tool

## When to Use
Use this tool when the user needs to:
- Post content to social media (Twitter, Facebook, LinkedIn, Instagram)
- Read social media feeds
- Reply to posts or comments
- Like content on social platforms
- Manage social media presence
- Monitor social media activity

## Arguments
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| platform | str | Yes | Platform: twitter, facebook, linkedin, instagram |
| action | str | Yes | Action: post, read, reply, like, get_profile |
| message | str | No | Content to post or reply (required for post/reply) |
| post_id | str | No | Post/tweet ID (required for reply/like) |
| user | str | No | Username to interact with |
| limit | int | No | Number of posts to retrieve (default: 10) |

## Configuration Required
Each platform needs API credentials in config.json:

```json
{
    "social_media": {
        "twitter": {
            "api_key": "...",
            "api_secret": "...",
            "access_token": "...",
            "access_token_secret": "..."
        },
        "facebook": {
            "access_token": "..."
        },
        "linkedin": {
            "access_token": "..."
        },
        "instagram": {
            "access_token": "..."
        }
    }
}
```

## Examples

### Example 1: Post to Twitter
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

### Example 2: Read LinkedIn feed
```json
{
    "tool_name": "social_media_tool",
    "tool_args": {
        "platform": "linkedin",
        "action": "read",
        "limit": 10
    }
}
```

### Example 3: Reply to Facebook post
```json
{
    "tool_name": "social_media_tool",
    "tool_args": {
        "platform": "facebook",
        "action": "reply",
        "post_id": "123456789",
        "message": "Thanks for sharing!"
    }
}
```

### Example 4: Like Instagram post
```json
{
    "tool_name": "social_media_tool",
    "tool_args": {
        "platform": "instagram",
        "action": "like",
        "post_id": "987654321"
    }
}
```

## Tips
- Get API credentials from each platform's developer portal
- Test with read-only operations first
- Respect rate limits to avoid being blocked
- Use specific post IDs when replying or liking
- Keep access tokens secure and rotate regularly
- Note: Current implementation includes demo placeholders - full API integration required for production use
