# Prompts & Skills Reference

> How iTaK's prompt engineering and skill system works.

## Prompts

All prompt files live in `prompts/`. They form the agent's "personality" and instructions.

### Prompt Assembly

When the agent builds its system prompt, it concatenates files in this order:

```
1. agent.system.main.md         --> Core instructions
2. agent.system.main.role.md    --> Personality & tone
3. agent.system.main.solving.md --> Problem-solving approach
4. agent.system.tool.*.md       --> Per-tool instructions
5. Memory context               --> SOUL.md, USER.md, MEMORY.md, AGENTS.md
6. Extension injections         --> system_prompt hook extensions
```

The result is a single massive system prompt that tells the LLM everything it needs to know.

---

### File-by-File Breakdown

#### `agent.system.main.md`
The core system prompt. Tells the agent WHAT it is and HOW to respond.

Key sections:
- **Core Architecture**: "You operate in a monologue loop"
- **Response Format**: JSON with `thoughts`, `headline`, `tool_name`, `tool_args`
- **Memory System**: "You have a 4-layer brain"
- **Rules**: Never expose secrets, test your work, etc.

Example of the JSON format the LLM must produce:
```json
{
    "thoughts": [
        "The user wants to search for something",
        "Let me check memory first",
        "Nothing relevant, I'll search the web"
    ],
    "headline": "Searching the web...",
    "tool_name": "web_search",
    "tool_args": {
        "query": "Python async patterns",
        "num_results": 5
    }
}
```

#### `agent.system.main.role.md`
Personality and communication style.

Key rules:
- Talk naturally, like a friend who knows tech
- Use contractions (you're, it's, don't)
- **NEVER use em dashes** - always use regular hyphens
- No corporate AI language (no "certainly", "I'd be happy to", "delve")
- Keep it concise - say what needs to be said, then stop

#### `agent.system.main.solving.md`
Problem-solving methodology. Teaches the LLM how to:
- Break down complex tasks
- Handle ambiguity
- When to ask vs. when to act
- Multi-step planning

#### `agent.system.tool.*.md`
Each tool has its own prompt file with detailed usage instructions:
- `agent.system.tool.code_exe.md` - Code execution guide
- `agent.system.tool.browser.md` - Browser usage guide
- `agent.system.tool.memory.md` - Memory usage guide
- `agent.system.tool.response.md` - Response formatting
- `agent.system.tool.search_engine.md` - Web search guide

#### `profiles/`
Specialized persona overrides. Example:
- `profiles/coder.md` - Focused on writing code
- Can add more for researcher, devops, etc.

---

## Skills

Skills are downloadable knowledge files that teach the agent how to do specific things.

### Skill Format

Each skill is a Markdown file in `skills/`:

```markdown
# Skill: Docker Operations

## When to Use
Use this skill when the user asks about Docker, containers, or deployment.

## Commands

### Build and run
docker build -t myapp .
docker run -d --name myapp -p 8080:8080 myapp

### Docker Compose
docker compose up -d
docker compose logs -f
docker compose down
...
```

### Available Skills

| Skill | File | Covers |
|-------|------|--------|
| Code Execution | `code_execution.md` | Python, Node.js, Shell patterns |
| Web Research | `web_research.md` | Search strategies, source evaluation |
| Docker Ops | `docker_ops.md` | Build, deploy, compose, troubleshoot |
| Linux | `os_linux.md` | Commands, package management |
| macOS | `os_macos.md` | Homebrew, system preferences |
| Windows | `os_windows.md` | PowerShell, package managers |
| Skill Spec | `SKILL.md` | How to write new skills |

### How Skills Load

The OS detection extension (`extensions/agent_init/os_detect.py`) detects the host OS and loads the appropriate skill guide into the system prompt at startup.

### Creating Custom Skills

Just add a `.md` file to `skills/`:

```markdown
# Skill: My Custom Workflow

## When to Use
When the user asks about [specific task].

## Steps
1. First, do this...
2. Then, do that...
3. Finally, verify by...

## Common Issues
- If X happens, try Y
- If Z fails, check W
```

The agent will include it in its context when relevant.
