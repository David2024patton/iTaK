# Skill: Knowledge Graph
Category: tool
Tags: neo4j, graph, relationships, entities, context

## When to Use
When you need to store or recall RELATIONSHIPS between things - people, projects, tools, concepts. The graph is best for "what's connected to X?" questions.

## Steps
1. Identify entities (people, projects, tools, services)
2. Identify relationships between them (uses, built_by, runs_on, depends_on)
3. Save relationships with `action: "save_relationship"`
4. Query context with `action: "get_context"` to see all connections

## Examples

### Example 1: Save a project relationship
```json
{
    "tool_name": "knowledge_tool",
    "tool_args": {
        "action": "save_relationship",
        "entity": "iTaK",
        "entity_type": "project",
        "related_to": "FastAPI",
        "relationship": "uses"
    }
}
```

### Example 2: Map infrastructure
```json
{
    "tool_name": "knowledge_tool",
    "tool_args": {
        "action": "save_relationship",
        "entity": "VPS",
        "entity_type": "server",
        "related_to": "Neo4j",
        "relationship": "runs"
    }
}
```

### Example 3: Recall everything about a project
```json
{
    "tool_name": "knowledge_tool",
    "tool_args": {
        "action": "get_context",
        "entity": "iTaK"
    }
}
```

## Relationship Types
| Type | Example |
|------|---------|
| `uses` | iTaK uses FastAPI |
| `built_by` | iTaK built_by David |
| `runs_on` | Neo4j runs_on VPS |
| `depends_on` | WebUI depends_on FastAPI |
| `related_to` | Polymarket related_to trading |

## Common Errors
| Error | Fix |
|-------|-----|
| Neo4j not connected | Check NEO4J_URI and NEO4J_PASSWORD in .env |
| Entity not found | Use `get_context` first to check spelling |
| Too many results | Be more specific with entity names |
