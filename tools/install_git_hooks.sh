#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="${REPO_ROOT}/.git/hooks"
PRE_COMMIT_HOOK="${HOOKS_DIR}/pre-commit"

if [[ ! -d "${HOOKS_DIR}" ]]; then
  echo "Git hooks directory not found. Are you in a git repository?" >&2
  exit 2
fi

cat > "${PRE_COMMIT_HOOK}" <<'HOOK'
#!/usr/bin/env bash

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

if ! command -v npx >/dev/null 2>&1; then
  echo "Skipping markdown lint pre-commit check (npx not found)." >&2
  echo "Install Node.js to enforce markdown checks locally." >&2
  exit 0
fi

staged_md_files="$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.md$' || true)"

if [[ -z "${staged_md_files}" ]]; then
  exit 0
fi

echo "Running markdownlint on staged markdown files..."
echo "${staged_md_files}" | xargs -r npx -y markdownlint-cli

if [[ -x "tools/check_no_emdash.sh" ]]; then
  echo "Running no-em-dash check on staged markdown files..."
  tools/check_no_emdash.sh --staged
fi
HOOK

chmod +x "${PRE_COMMIT_HOOK}"

echo "Installed pre-commit hook: ${PRE_COMMIT_HOOK}"
echo "This hook runs markdownlint on staged .md files."
