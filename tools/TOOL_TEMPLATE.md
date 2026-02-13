# iTaK Tool Template

Tools are Python classes in `tools/`. They give the agent the ability to DO things (run code, search, save memory). Auto-loaded at startup.

## Template

```python
"""
iTaK Tool: [Name] - [one-line description].
"""

from tools.base import BaseTool, ToolResult


class MyTool(BaseTool):
    """What this tool does.

    The LLM reads this docstring to understand when to use it.
    Be specific about what the tool does and what args it takes.
    """

    name = "my_tool"  # This is the tool_name the LLM uses in JSON
    description = "One-line description for the tool list."

    async def execute(
        self,
        required_arg: str = "",
        optional_arg: int = 10,
        **kwargs,
    ) -> ToolResult:
        """Execute the tool."""

        # Validate input
        if not required_arg:
            return ToolResult(output="Error: 'required_arg' is required.", error=True)

        # Do the work
        try:
            result = f"Processed: {required_arg} with {optional_arg}"
            return ToolResult(output=result)
        except Exception as e:
            return ToolResult(output=f"Error: {e}", error=True)
```

## Steps to Create a New Tool

1. **Create the Python file:** `tools/my_tool.py`
2. **Create the prompt file:** `prompts/agent.system.tool.my_tool.md`
3. Done. The agent auto-discovers it at next startup.

## The Prompt File

Every tool needs a matching prompt in `prompts/`. This tells the LLM WHEN and HOW to use it:

```markdown
# Tool: my_tool

## When to Use
Use this tool when the user asks to [specific task].

## Arguments
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| required_arg | str | Yes | What to process |
| optional_arg | int | No | Processing depth (default: 10) |

## Examples

### Example 1
User: "Process the data"
```json
{
    "tool_name": "my_tool",
    "tool_args": {"required_arg": "data.csv", "optional_arg": 20}
}
```

## Tips
- Always validate input before processing
- Return clear error messages on failure
```

## Key Rules

| Rule | Why |
|------|-----|
| `name` must match the filename (minus `.py`) | Auto-loader expects `tools/my_tool.py` to contain a class with `name = "my_tool"` |
| Always accept `**kwargs` | Future-proofs against extra args |
| Return `ToolResult` | The agent expects this dataclass |
| Set `error=True` on failure | The self-heal engine looks at this |
| Set `break_loop=True` ONLY in the response tool | This stops the monologue. Only `response.py` should do this. |

## ToolResult Fields

```python
@dataclass
class ToolResult:
    output: str = ""          # Result text shown to the LLM
    break_loop: bool = False  # True = stop monologue (response tool only)
    error: bool = False       # True = tool failed (triggers self-heal)
```

## Accessing the Agent

Every tool has `self.agent` which gives you access to everything:

```python
# Memory
await self.agent.memory.search("query")
await self.agent.memory.save("content", category="devops")

# Config
timeout = self.agent.config.get("tools", {}).get("my_tool", {}).get("timeout", 60)

# Logging
self.agent.logger.log("tool_call", {"tool": self.name, "status": "success"})

# Progress updates
await self.agent.progress.update(step=1, message="Working on it...")
```

> **Need to add knowledge instead of code?** See `skills/SKILL.md` for the skill template.
