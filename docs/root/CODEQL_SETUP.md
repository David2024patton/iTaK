# CodeQL Configuration Fix

## At a Glance

- Audience: Security-conscious operators and developers implementing hardening controls.
- Scope: Document hardening controls, secure defaults, and verification steps before deployment.
- Last reviewed: 2026-02-16.

## Quick Start

- Apply hardening controls before exposing services to external networks.
- Follow deployment guardrails from [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md).
- Validate findings with repeatable scans before closing security tasks.

## Deep Dive

The detailed content for this topic starts below.

## AI Notes

- Preserve threat-model assumptions and include guardrail checks in runbooks.
- Avoid absolute compliance claims without independent audit evidence.

## Issue

The repository currently has both **default** and **advanced** CodeQL setups configured, which causes a conflict. GitHub does not allow both configurations to run simultaneously.

Error message:

```
CodeQL analyses from advanced configurations cannot be processed when the default setup is enabled
```

## Solution

To fix this issue and use the advanced CodeQL configuration (`.github/workflows/codeql.yml`), you need to disable the default setup:

### Steps to Disable Default Setup

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Code security and analysis**
3. Find **CodeQL analysis** section
4. Click the **...** (three dots) menu next to "CodeQL analysis"
5. Select **Disable** or **Switch to advanced setup**
6. Confirm the change

### Benefits of Advanced Setup

The advanced configuration in `.github/workflows/codeql.yml` provides:

- **Extended security queries** for better vulnerability detection
- **Quality queries** for code improvement suggestions
- **Multiple language support** (Python, JavaScript/TypeScript)
- **Scheduled daily scans** at 02:00 UTC
- **Customizable configuration** for future enhancements

### Verification

After disabling the default setup:

1. The workflow will automatically run on the next push or pull request
2. You can manually trigger it from the **Actions** tab
3. Check the **Security** → **Code scanning** tab for results

## Alternative: Keep Default Setup

If you prefer to keep the default setup instead:

1. Delete or disable `.github/workflows/codeql.yml`
2. The default setup will continue to work automatically

Note: The default setup is simpler but provides less control and fewer customization options compared to the advanced setup.

## References

- [GitHub Docs: Configuring Code Scanning](https://docs.github.com/en/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors/configuring-code-scanning-for-a-repository)
- [GitHub Docs: About CodeQL](https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql)
- [Troubleshooting Default Setup Overrides](https://docs.github.com/en/enterprise-cloud@latest/code-security/securing-your-organization/troubleshooting-security-configurations/unexpected-default-setup)
