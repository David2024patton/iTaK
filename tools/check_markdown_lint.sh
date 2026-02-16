#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${REPO_ROOT}"

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required to run markdown lint checks." >&2
  echo "Install Node.js (includes npx) and try again." >&2
  exit 2
fi

echo "Running markdownlint across all Markdown files..."
npx -y markdownlint-cli "**/*.md"
