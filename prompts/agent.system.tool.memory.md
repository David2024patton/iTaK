# Tool: memory_load / memory_save

## memory_load — Search Memory

Search across all 4 memory layers for relevant information.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `query` | string | Yes | Natural language search query |
| `category` | string | No | Filter by category |
| `limit` | int | No | Max results (default: 10) |

```json
{
    "thoughts": ["Let me check if I've solved this Docker issue before."],
    "headline": "Checking memory",
    "tool_name": "memory_load",
    "tool_args": {
        "query": "Docker container port conflict resolution"
    }
}
```

## memory_save — Store Memory

Save new knowledge, facts, or decisions to the brain.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `content` | string | Yes | What to remember |
| `category` | string | No | general, fact, decision, lesson, solution, preference |
| `metadata` | object | No | Additional context |

```json
{
    "thoughts": ["This Neo4j fix worked — I should save it for next time."],
    "headline": "Saving solution to memory",
    "tool_name": "memory_save",
    "tool_args": {
        "content": "Neo4j bolt connection fails when using localhost — must use 127.0.0.1 instead.",
        "category": "solution"
    }
}
```

## Rules

- **Always check memory BEFORE searching the web**
- Save solutions that took effort to find
- Save user preferences when they mention them
- Save architecture decisions for future reference
