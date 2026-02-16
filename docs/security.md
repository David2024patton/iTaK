# Security Module Reference

## At a Glance
- Audience: Users, operators, developers, and contributors working with iTaK.
- Scope: This page explains `Security Module Reference`.
- Last reviewed: 2026-02-16.

## Quick Start
- Docs hub: [WIKI.md](WIKI.md)
- Beginner path: [NOOBS_FIRST_DAY.md](NOOBS_FIRST_DAY.md)
- AI-oriented project map: [AI_CONTEXT.md](AI_CONTEXT.md)

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Use explicit file paths and exact command examples from this page when automating tasks.
- Treat scale/compliance statements as environment-dependent unless paired with test or audit evidence.


> Every security component in iTaK explained with examples.

## Overview

iTaK has 4 security modules that form a defense-in-depth strategy:

```
INPUT                                     OUTPUT
  |                                         ^
  v                                         |
RateLimiter --> Scanner --> SecretManager --> OutputGuard
(throttle)    (analyze)    (mask in logs)    (scrub PII)
```

---

## output_guard.py - PII/Secret Redaction

**Lines:** ~290 | **The "bouncer" for all agent output.**

This is the module that runs BEFORE any text leaves the system. Every message the agent sends passes through the Output Guard first.

### 4-Layer Detection

```
Layer 1: Known Secrets     --> Exact-match from SecretManager
Layer 2: Secret Patterns   --> API keys, tokens, passwords
Layer 3: PII Patterns      --> SSNs, credit cards, phones, emails
Layer 4: Custom Patterns   --> User-defined regex rules
```

### What it catches

| Category | Pattern Example | Redacted As |
|----------|----------------|-------------|
| SSN | `123-45-6789` | `[SSN REDACTED]` |
| Credit Card | `4111-1111-1111-1111` | `[CARD REDACTED]` |
| Phone | `(555) 123-4567` | `[PHONE REDACTED]` |
| Email | `user@example.com` | `[EMAIL REDACTED]` |
| Street Address | `123 Main Street` | `[ADDRESS REDACTED]` |
| IP Address | `192.168.1.100` | `[IP REDACTED]` |
| Date of Birth | `01/15/1990` | `[DOB REDACTED]` |
| OpenAI Key | `sk-abc123...` | `[API KEY REDACTED]` |
| GitHub Token | `ghp_abc...` | `[GITHUB TOKEN REDACTED]` |
| AWS Key | `AKIAIOSFODNN7EXAMPLE` | `[AWS KEY REDACTED]` |
| Discord Token | `MTQ3MD...` | `[DISCORD TOKEN REDACTED]` |
| JWT | `eyJhbG...` | `[JWT REDACTED]` |
| Private Key | `-----BEGIN RSA...` | `[PRIVATE KEY REDACTED]` |
| Crypto Key | `0xabcdef...` | `[CRYPTO KEY REDACTED]` |
| Password | `password=Secret123` | `[PASSWORD REDACTED]` |

### Usage

```python
from security.output_guard import OutputGuard

guard = OutputGuard()

# Basic sanitization
result = guard.sanitize("My SSN is 123-45-6789")
print(result.sanitized_text)
# Output: "My SSN is [SSN REDACTED]"

# Check what was found
print(result.was_modified)        # True
print(result.redaction_count)     # 1
print(result.categories_found)   # ["ssn"]

# Add custom patterns
guard.add_custom_pattern(
    pattern=r"PROJ-\d{6}",
    label="project_id",
    replacement="[PROJECT ID REDACTED]"
)
```

### Where it's integrated

1. **`adapters/base.py`** - `_sanitize_output()` method on all outgoing messages
2. **`tools/response.py`** - Scrubs the final response before breaking the loop
3. **`core/agent.py`** - Initialized at startup with SecretManager reference

### Configuration

```json
{
    "output_guard": {
        "enabled": true,
        "log_redactions": true,
        "strict_mode": true,
        "skip_categories": ["email"]  // Optional: let emails through
    }
}
```

---

## secrets.py - Secret Management

**Lines:** 117 | **Two-store secret system.**

### How it works

```
Store 1: .env file          --> Actual secret values
Store 2: config.json        --> References like "$OPENAI_API_KEY"
Prompts: {{placeholder}}    --> Gets replaced at runtime
```

### Example

**.env file:**
```bash
OPENAI_API_KEY=sk-abc123...
DISCORD_TOKEN=MTQ3MD...
NEO4J_PASSWORD=mypassword
```

**config.json:**
```json
{
    "models": {
        "chat": {
            "api_key": "$OPENAI_API_KEY"
        }
    }
}
```

**Prompt template:**
```markdown
Use the API key: {{OPENAI_API_KEY}} to connect.
```

At runtime:
```python
secrets = SecretManager(env_file=".env")

# Resolve config values
api_key = secrets.resolve_config_value("$OPENAI_API_KEY")
# Returns: "sk-abc123..."

# Replace placeholders in text
text = secrets.replace_placeholders("Use key {{OPENAI_API_KEY}}")
# Returns: "Use key sk-abc123..."

# Mask secrets for logging
masked = secrets.mask_in_text("Key is sk-abc123def456")
# Returns: "Key is sk-***56"
```

---

## scanner.py - Security Scanner

**Lines:** 252 | **Static analysis for dangerous patterns.**

Scans generated code BEFORE execution. Three severity levels:

### Dangerous Patterns

| Severity | Pattern | Why |
|----------|---------|-----|
| CRITICAL | `os.system()` | Shell injection risk |
| CRITICAL | `eval()`, `exec()` | Arbitrary code execution |
| CRITICAL | `pickle.loads()` | Deserialization attack |
| CRITICAL | `rm -rf /` | Data destruction |
| WARNING | `subprocess.*` | Verify arguments |
| WARNING | `requests.get()` | Verify URL |
| WARNING | `open("w")` | File write, verify path |
| INFO | `import os` | Audit trail |

### Secret Patterns (also detected)

| Pattern | Type |
|---------|------|
| `sk-[a-zA-Z0-9]{20,}` | OpenAI API key |
| `ghp_[a-zA-Z0-9]{36}` | GitHub token |
| `-----BEGIN PRIVATE KEY-----` | Private key |
| `password = "..."` | Hardcoded password |

### Usage

```python
scanner = SecurityScanner()

# Scan a code string
result = scanner.scan_code("""
import os
os.system("rm -rf /")
password = "hunter2"
""")

print(result["safe"])           # False
print(result["blocked"])        # True
print(result["findings"])       # [CRITICAL: os.system, CRITICAL: rm -rf /]
print(result["secrets_found"])  # [Hardcoded password on line 3]

# Deep AST analysis (Python only)
findings = scanner.scan_python_ast(code)

# Scan a whole directory
result = scanner.scan_directory("./tools/", extensions=[".py"])
```

---

## rate_limiter.py - Rate Limiting

**Lines:** ~130 | **Per-user, per-tool, and global rate limits.**

Prevents abuse across all 3 dimensions:

```python
limiter = RateLimiter(config={
    "global": {"requests_per_minute": 60},
    "per_user": {"requests_per_minute": 20},
    "per_tool": {
        "code_execution": {"requests_per_minute": 10},
        "web_search": {"requests_per_minute": 30}
    }
})

# Check if a request is allowed
allowed = limiter.check("user_123", "code_execution")
if not allowed:
    # Rate limited - reject or queue
    pass
```

### Configuration
```json
{
    "security": {
        "rate_limit": {
            "global_rpm": 60,
            "per_user_rpm": 20,
            "per_tool": {
                "code_execution": 10,
                "web_search": 30
            }
        }
    }
}
```
