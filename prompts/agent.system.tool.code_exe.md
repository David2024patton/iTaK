# Tool: code_execution

## Usage

Execute code in Python, Node.js, or terminal (bash/PowerShell).

## Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `runtime` | string | Yes | `python`, `nodejs`, or `terminal` |
| `code` | string | Yes | The code to execute |
| `timeout` | int | No | Timeout in seconds (default: 60, max: 300) |
| `workdir` | string | No | Working directory (defaults to current) |

## Examples

```json
{
    "thoughts": ["I need to check what Python version is installed."],
    "headline": "Checking Python version",
    "tool_name": "code_execution",
    "tool_args": {
        "runtime": "terminal",
        "code": "python --version"
    }
}
```

```json
{
    "thoughts": ["Let me write and run a Python script to process the data."],
    "headline": "Processing data",
    "tool_name": "code_execution",
    "tool_args": {
        "runtime": "python",
        "code": "import json\ndata = {'key': 'value'}\nprint(json.dumps(data, indent=2))"
    }
}
```

## Rules

- **ALWAYS run `--help` first** when using a CLI tool you haven't used before
- Check the exit code - non-zero means an error occurred
- Read stderr carefully for error messages
- For long-running processes, set a higher timeout
- Never use `eval()` or `exec()` directly - always use this tool
