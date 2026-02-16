# Tool: knowledge_tool

## When to Use

Use this tool to store and query RELATIONSHIPS between entities (people, projects, tools, servers). Best for "what's connected to X?" questions.

## Arguments

| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| action | str | Yes | `search`, `save_entity`, `save_relationship`, `get_context` |
| entity | str | Yes | Entity name |
| entity_type | str | For save | Type: person, project, tool, server, service, concept |
| related_to | str | For relationships | Related entity name |
| relationship | str | For relationships | Relationship type: uses, built_by, runs_on, depends_on |
| properties | dict | No | Extra properties for the relationship |

## Examples

### Save a relationship

```json
{
    "tool_name": "knowledge_tool",
    "tool_args": {
        "action": "save_relationship",
        "entity": "iTaK",
        "entity_type": "project",
        "related_to": "Python",
        "relationship": "uses"
    }
}
```

### Get all connections for an entity

```json
{
    "tool_name": "knowledge_tool",
    "tool_args": {
        "action": "get_context",
        "entity": "iTaK"
    }
}
```

## Tips

- Use `get_context` before saving to avoid duplicates
- Entity names are case-sensitive
- Requires Neo4j to be configured in config.json
