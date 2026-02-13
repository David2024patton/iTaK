# Tool: response

## Usage

Call this tool to send your final response to the user.

**This is the ONLY way to end your current task.** If you don't call this tool, the user will never see your answer and your loop will continue until timeout.

## Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `message` | string | Yes | Your final response to the user |

## Example

```json
{
    "thoughts": ["I've completed the analysis and have all the information needed."],
    "headline": "Analysis complete",
    "tool_name": "response",
    "tool_args": {
        "message": "Here's what I found: ..."
    }
}
```

## Rules

- Always call this tool when you have your final answer
- Include all relevant information in the message
- Format with Markdown (headers, code blocks, lists)
- If the task required code, include the code in the response
- If the task required a file, mention the file path
