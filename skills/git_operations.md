# Skill: Git Operations
Category: devops
Tags: git, github, version-control, repository

## When to Use
Use this skill when you need to:
- Clone Git repositories
- Check repository status
- View changes (diffs)
- Commit and push changes
- Pull updates from remote
- Switch branches
- View commit history
- Manage version control

## Steps

### Cloning a Repository
1. Use `git_tool` with action "clone"
2. Provide the repository URL
3. Repository will be cloned to current directory

### Checking Status and Changes
1. Use action "status" to see current state
2. Use action "diff" to see uncommitted changes
3. Use action "log" to view commit history

### Committing Changes
1. Use action "add" to stage files (default: all files)
2. Use action "commit" with a descriptive message
3. Use action "push" to send changes to remote

### Pulling Updates
1. Use action "pull" to fetch and merge remote changes
2. Optionally specify a branch name

### Branch Management
1. Use action "checkout" to switch branches
2. Provide the branch name

## Examples

### Example 1: Clone a repository
```json
{
    "tool_name": "git_tool",
    "tool_args": {
        "action": "clone",
        "repo": "https://github.com/user/repo.git"
    }
}
```

### Example 2: Check status and commit
```json
{
    "tool_name": "git_tool",
    "tool_args": {
        "action": "status",
        "repo": "./my-repo"
    }
}
```

```json
{
    "tool_name": "git_tool",
    "tool_args": {
        "action": "commit",
        "repo": "./my-repo",
        "message": "Add new feature"
    }
}
```

### Example 3: Push changes
```json
{
    "tool_name": "git_tool",
    "tool_args": {
        "action": "push",
        "repo": "./my-repo",
        "branch": "main"
    }
}
```

### Example 4: View commit history
```json
{
    "tool_name": "git_tool",
    "tool_args": {
        "action": "log",
        "repo": "./my-repo"
    }
}
```

## Common Errors

| Error | Fix |
|-------|-----|
| Not a git repository | Initialize with `git init` or clone a repository first |
| Permission denied | Check authentication (SSH keys or credentials) |
| Merge conflicts | Resolve conflicts manually, then commit |
| Detached HEAD | Checkout a proper branch with `checkout` action |
| Push rejected | Pull latest changes first with `pull` action |
