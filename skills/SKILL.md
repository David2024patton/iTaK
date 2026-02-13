# iTaK Skill Template

Skills are markdown knowledge files in `skills/`. They teach the agent HOW to do something without writing code. Auto-discovered at startup.

## Template

```markdown
# Skill: [Name]
Category: [code | devops | research | trading | os | tool]
Tags: [tag1, tag2, tag3]

## When to Use
Trigger conditions - when should the agent use this skill.

## Steps
1. First, do this
2. Then, do that
3. Verify by checking this

## Examples

### Example 1: [scenario]
> User: "Deploy the new version"
```bash
docker compose build
docker compose up -d
docker compose logs -f
```

### Example 2: [scenario]
> User: "Check if the service is running"
```bash
docker ps --filter name=myapp
curl http://localhost:8080/health
```

## Common Errors
| Error | Fix |
|-------|-----|
| Connection refused | Check if the service is running |
| Permission denied | Run with sudo or fix file permissions |
```

## How It Works

1. Drop a `.md` file in `skills/`
2. The agent finds it by filename/content keyword match
3. Relevant skills get injected into the system prompt context
4. No code changes needed - just markdown

## Categories

| Category | Use For |
|----------|---------|
| `code` | Languages, frameworks, patterns |
| `devops` | Docker, deployment, CI/CD |
| `research` | Search strategies, analysis |
| `trading` | Markets, APIs, strategies |
| `os` | OS-specific commands |
| `tool` | Tool-specific guides |

> **Need to add a new tool instead?** See `tools/TOOL_TEMPLATE.md` for the code template.
