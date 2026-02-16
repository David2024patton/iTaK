# Skill: Task Delegation

Category: tool
Tags: delegation, sub-agent, parallel, swarm

## When to Use

When the task is complex and can be broken into independent subtasks, or when a specialized role (researcher, coder, tester) would do a better job on a piece of the work.

## Steps

1. Identify which part of the task can be delegated
2. Choose the right role for the sub-agent
3. Limit the sub-agent's tool access to what it needs
4. Delegate with a clear, specific task description
5. Wait for the result and integrate it into your work

## Examples

### Example 1: Delegate research

```json
{
    "tool_name": "delegate_task",
    "tool_args": {
        "task": "Research the top 5 Python web frameworks for building REST APIs. Compare performance, community size, and learning curve.",
        "role": "researcher",
        "tools": ["web_search", "memory_save"]
    }
}
```

### Example 2: Delegate testing

```json
{
    "tool_name": "delegate_task",
    "tool_args": {
        "task": "Write pytest tests for the UserManager class in core/users.py. Cover all CRUD operations.",
        "role": "coder",
        "tools": ["code_execution"]
    }
}
```

## When NOT to Delegate

- Simple tasks that take one tool call
- Tasks that need your full conversation context
- Tasks where the user expects YOU to do it (personal preference)

## Common Errors

| Error | Fix |
|-------|-----|
| Sub-agent loops forever | Set max_iterations lower for sub-agents |
| Sub-agent lacks context | Include more details in the task description |
| Wrong tools given | Match tools to the role (researchers need web_search, coders need code_execution) |
