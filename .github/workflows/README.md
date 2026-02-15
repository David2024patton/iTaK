# GitHub Workflows

## CodeQL Analysis

**Note:** The advanced CodeQL workflow (`codeql.yml`) has been temporarily disabled because GitHub's default CodeQL setup is currently enabled for this repository.

### Current Setup

GitHub's **default CodeQL analysis** is active and automatically scans:
- Python code
- JavaScript/TypeScript code

The default setup runs automatically on:
- Every push to main/develop branches
- Every pull request to main
- Scheduled scans

### To Re-enable Advanced Workflow

If you want to use the advanced CodeQL configuration (`codeql.yml.disabled`):

1. **Disable default CodeQL in GitHub:**
   - Go to Settings → Code security and analysis
   - Find "CodeQL analysis"
   - Click "..." menu → Disable

2. **Re-enable the advanced workflow:**
   ```bash
   git mv .github/workflows/codeql.yml.disabled .github/workflows/codeql.yml
   ```

3. **Benefits of advanced setup:**
   - Extended security queries
   - Customizable scan configuration
   - Multiple language support with custom settings
   - Scheduled scans at specific times

### Why This Matters

GitHub does not allow both default and advanced CodeQL setups to run simultaneously. Running both causes this error:
```
CodeQL analyses from advanced configurations cannot be processed when the default setup is enabled
```

See `CODEQL_SETUP.md` in the repository root for more details.

## Current Active Workflows

- `ci.yml` - Continuous Integration (linting, type checking, tests)
- Default CodeQL (managed in GitHub Settings, not visible here)
