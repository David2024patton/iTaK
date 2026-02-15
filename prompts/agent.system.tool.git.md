# Tool: git_tool

## When to Use
Use this tool when the user needs to perform Git or GitHub operations such as:
- Cloning repositories
- Checking repository status
- Viewing diffs or commit history
- Committing and pushing changes
- Pulling updates
- Switching branches

## Arguments
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| action | str | Yes | Git action: clone, status, diff, add, commit, push, pull, checkout, log |
| repo | str | No | Repository URL or local path (default: current directory) |
| message | str | No | Commit message (required for commit action) |
| branch | str | No | Branch name (for checkout, push, pull) |
| files | list | No | Files to add (for add action, default: all files) |

## Examples

### Example 1: Clone a repository
```json
{
    "tool_name": "git_tool",
    "tool_args": {
        "action": "clone",
        "repo": "https://github.com/username/repository.git"
    }
}
```

### Example 2: Check status and commit
```json
{
    "tool_name": "git_tool",
    "tool_args": {"action": "status", "repo": "./project"}
}
```

```json
{
    "tool_name": "git_tool",
    "tool_args": {
        "action": "commit",
        "repo": "./project",
        "message": "Implement new feature"
    }
}
```

### Example 3: Push to remote
```json
{
    "tool_name": "git_tool",
    "tool_args": {
        "action": "push",
        "repo": "./project",
        "branch": "main"
    }
}
```

## Tips
- Always check status before committing
- Use descriptive commit messages
- Pull before pushing to avoid conflicts
- Handle authentication errors by checking SSH keys or credentials
