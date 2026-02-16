# Tool: gogcli_tool

## When to Use

Use this tool when the user needs Google Workspace operations through gogcli (`gog`), including Gmail, Calendar, Drive, Docs, Sheets, Tasks, People, Groups, or related account/config commands.

## Arguments

| Arg | Type | Required | Description |
| --- | --- | --- | --- |
| action | str | No | One of `run`, `help`, `version` (default: `run`) |
| command | str | Yes* | gog subcommand string without `gog` prefix (required for `action=run`) |
| json_output | bool | No | Add `--json` automatically for parseable output (default: true) |
| no_input | bool | No | Add `--no-input` automatically to avoid prompts (default: true) |
| account | str | No | Sets `GOG_ACCOUNT` for this call |
| client | str | No | Sets `GOG_CLIENT` for this call |
| timeout | int | No | Timeout in seconds (default: 60) |

## Examples

### Example 1: List task lists

```json
{
    "tool_name": "gogcli_tool",
    "tool_args": {
        "action": "run",
        "command": "tasks lists --max 10"
    }
}
```

### Example 2: Search unread Gmail

```json
{
    "tool_name": "gogcli_tool",
    "tool_args": {
        "action": "run",
        "command": "gmail search 'is:unread' --max 20",
        "account": "work@example.com"
    }
}
```

### Example 3: Check gog version

```json
{
    "tool_name": "gogcli_tool",
    "tool_args": {
        "action": "version"
    }
}
```

## Tips

- Do not include the leading `gog` in `command`.
- Prefer JSON output for downstream parsing.
- Use `account` when the user has multiple Google identities.
