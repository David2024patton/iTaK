# iTaK Skills - Meta-Skill Template

# How to Create a Skill

Skills are markdown files in the `skills/` directory. They extend iTaK's knowledge without requiring code changes.

## File Format

```markdown
# Skill: [Name]
Category: [category]
Tags: [tag1, tag2, tag3]

## Description
What this skill does.

## When to Use
When the agent should activate this skill.

## Steps
1. Step one
2. Step two
3. Step three

## Examples
Example usage scenarios.

## Common Errors
Known issues and solutions.
```

## Categories

| Category | Description |
|----------|-------------|
| `code` | Programming languages, frameworks |
| `devops` | Docker, deployment, infrastructure |
| `research` | Web research, data analysis |
| `trading` | Polymarket, market analysis |
| `os` | Operating system commands |
| `tool` | Tool-specific instructions |

## Discovery Pipeline

When iTaK needs a skill:
1. **Check memory** - Neo4j → SQLite → Weaviate
2. **Check skills directory** - keyword match on filenames and content
3. **Search web** - if not found locally
4. **Create and save** - if learned from web, save as new skill file

## Security

All skills are scanned by the security module before execution.
Dangerous patterns (eval, exec, subprocess with pipes) are flagged.
