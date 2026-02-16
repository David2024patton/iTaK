# Contributing to iTaK

## Style Rules (Required)

These writing rules are enforced for project documentation and prompt files.

- Never use em dashes (U+2014).
- Always use a regular hyphen-minus (`-`) instead.
- Keep language simple and easy to follow.

## Checks Before Commit

Run these commands before pushing:

```bash
tools/check_markdown_lint.sh
tools/check_no_emdash.sh --paths prompts memory
```

For local automatic checks on staged markdown files:

```bash
tools/install_git_hooks.sh
```

## Pull Request Expectations

- Keep changes focused and minimal.
- Update docs when behavior changes.
- Verify no-em-dash and markdown checks pass.
