# CodeQL Configuration Fix

## Current Status ✅ RESOLVED

**The advanced CodeQL workflow has been disabled** to resolve the conflict with GitHub's default CodeQL setup.

The repository now uses **GitHub's default CodeQL analysis**, which automatically scans:
- Python code
- JavaScript/TypeScript code

The default setup runs automatically on every push and pull request.

---

## Background: The Conflict Issue

The repository previously had both **default** and **advanced** CodeQL setups configured, which causes a conflict. GitHub does not allow both configurations to run simultaneously.

Error message (now resolved):
```
CodeQL analyses from advanced configurations cannot be processed when the default setup is enabled
```

## Current Solution

✅ **Fixed:** The advanced workflow file has been renamed to `.github/workflows/codeql.yml.disabled`

This allows the default CodeQL setup to work without conflicts.

---

## If You Want Advanced Setup (Optional)

To switch back to the advanced CodeQL configuration:

### Steps:

1. **Disable default CodeQL setup in GitHub:**
   - Go to your repository on GitHub
   - Navigate to **Settings** → **Code security and analysis**
   - Find **CodeQL analysis** section
   - Click the **...** (three dots) menu next to "CodeQL analysis"
   - Select **Disable**
   - Confirm the change

2. **Re-enable the advanced workflow:**
   ```bash
   cd .github/workflows
   git mv codeql.yml.disabled codeql.yml
   git commit -m "Re-enable advanced CodeQL workflow"
   git push
   ```

3. **Verify it works:**
   - Go to **Actions** tab
   - Check that "CodeQL Advanced" workflow runs successfully

### Benefits of Advanced Setup:

- **Extended security queries** for better vulnerability detection
- **Quality queries** for code improvement suggestions  
- **Multiple language support** with custom configurations
- **Scheduled daily scans** at 02:00 UTC (customizable)
- **Customizable query suites** for future enhancements

---

## Recommended Setup: Use Default

For most users, **GitHub's default CodeQL setup is recommended** because:
- ✅ Zero configuration required
- ✅ Automatically updates with latest security queries
- ✅ Works out-of-the-box
- ✅ No workflow file maintenance needed
- ✅ Fully managed by GitHub

The advanced setup is only needed if you require:
- Custom query suites
- Specific scan schedules
- Fine-grained language configurations
- Integration with custom tooling

---

## References

- [GitHub Docs: Configuring Code Scanning](https://docs.github.com/en/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors/configuring-code-scanning-for-a-repository)
- [GitHub Docs: About CodeQL](https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql)
- [Troubleshooting Default Setup Overrides](https://docs.github.com/en/enterprise-cloud@latest/code-security/securing-your-organization/troubleshooting-security-configurations/unexpected-default-setup)
