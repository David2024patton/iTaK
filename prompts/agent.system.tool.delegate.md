# Tool: delegate_task

## When to Use
Use this tool when a task is complex and can be split into independent subtasks, or when a specialized role (researcher, coder, tester) would be more effective.

## Arguments
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| task | str | Yes | Clear description of what the sub-agent should do |
| role | str | No | Specialized role: researcher, coder, tester, devops |
| tools | list | No | Tools the sub-agent can use (default: all) |

## Examples

### Research task
```json
{
    "tool_name": "delegate_task",
    "tool_args": {
        "task": "Find the top 5 Python async frameworks and compare them",
        "role": "researcher",
        "tools": ["web_search", "memory_save"]
    }
}
```

### Code task
```json
{
    "tool_name": "delegate_task",
    "tool_args": {
        "task": "Write unit tests for the MemoryManager class",
        "role": "coder",
        "tools": ["code_execution", "memory_load"]
    }
}
```

## Tips
- Be specific in the task description - the sub-agent doesn't have your conversation context
- Limit tools to only what's needed for the specific subtask
- Don't delegate simple one-step tasks - do them yourself
