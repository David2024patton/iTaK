# Skill: Code Execution Reference

Category: tool
Tags: code, python, nodejs, shell, docker

## Overview

The `code_execution` tool runs code in Python, Node.js, or shell environments.

## Languages

| Runtime | How to specify |
|---------|---------------|
| Python | `"runtime": "python"` |
| Node.js | `"runtime": "nodejs"` |
| Shell/Bash | `"runtime": "terminal"` |

## Best Practices

1. **Always use Python by default** - it's the most powerful runtime
2. **Use `subprocess.run()`** instead of `os.system()` - safer and gives stdout/stderr
3. **Set timeouts** - script hangs will block the whole agent
4. **Never use shell=True** with user-provided input - injection risk
5. **Install packages at runtime** - use `pip install` or `npm install` within the code

## Common Patterns

### Run a Python script

```json
{
  "tool_name": "code_execution",
  "arguments": {
    "runtime": "python",
    "code": "import json\nresult = {'hello': 'world'}\nprint(json.dumps(result))"
  }
}
```

### Run a shell command

```json
{
  "tool_name": "code_execution",
  "arguments": {
    "runtime": "terminal",
    "code": "ls -la /workspace"
  }
}
```

### Install a package then use it

```json
{
  "tool_name": "code_execution",
  "arguments": {
    "runtime": "python",
    "code": "import subprocess\nsubprocess.run(['pip', 'install', 'requests'], capture_output=True)\nimport requests\nprint(requests.get('https://httpbin.org/ip').json())"
  }
}
```

## Docker Sandbox

When `sandbox_enabled` is true in config.json, code runs inside a Docker container.
This provides:

- **Isolation** - code can't access host filesystem
- **Timeout enforcement** - containers are killed after timeout
- **Clean environment** - each execution starts fresh
- **Network isolation** - optional network restrictions

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError` | Package not installed | Install with `pip install` in the code |
| `TimeoutError` | Code ran too long | Optimize or increase timeout |
| `PermissionError` | File access denied | Check sandbox permissions |
| `SyntaxError` | Invalid Python/JS | Fix the code syntax |
