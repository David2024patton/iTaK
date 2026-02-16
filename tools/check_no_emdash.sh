#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: tools/check_no_emdash.sh [--staged] [--paths <path> [<path> ...]]

Checks files for em-dash characters (U+2014, "—").

Options:
  --staged              Check staged markdown files only
  --paths <...>         Check specific files/directories (markdown files only)
  -h, --help            Show this help message
EOF
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

mode="default"
declare -a path_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --staged)
      mode="staged"
      shift
      ;;
    --paths)
      mode="paths"
      shift
      while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do
        path_args+=("$1")
        shift
      done
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

declare -a files=()

if [[ "${mode}" == "staged" ]]; then
  while IFS= read -r file; do
    [[ -n "${file}" ]] && files+=("${file}")
  done < <(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.md$' || true)
elif [[ "${mode}" == "paths" ]]; then
  if [[ ${#path_args[@]} -eq 0 ]]; then
    echo "--paths requires one or more file/directory arguments" >&2
    exit 2
  fi

  for path in "${path_args[@]}"; do
    if [[ -d "${path}" ]]; then
      while IFS= read -r file; do
        [[ -n "${file}" ]] && files+=("${file}")
      done < <(find "${path}" -type f -name '*.md' | sed 's#^\./##' | sort)
    elif [[ -f "${path}" && "${path}" =~ \.md$ ]]; then
      files+=("${path}")
    fi
  done
else
  while IFS= read -r file; do
    [[ -n "${file}" ]] && files+=("${file}")
  done < <(find prompts memory -type f -name '*.md' | sed 's#^\./##' | sort)
fi

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No markdown files to check for em-dashes."
  exit 0
fi

violations=0

for file in "${files[@]}"; do
  [[ -f "${file}" ]] || continue
  if grep -n "—" "${file}" >/tmp/emdash_hits.$$ 2>/dev/null; then
    if [[ ${violations} -eq 0 ]]; then
      echo "Em-dash usage detected (use '-' instead):"
    fi
    echo ""
    echo "${file}:"
    cat /tmp/emdash_hits.$$
    violations=$((violations + 1))
  fi
done

rm -f /tmp/emdash_hits.$$

if [[ ${violations} -gt 0 ]]; then
  echo ""
  echo "FAIL: Found em-dash characters in ${violations} file(s)."
  exit 1
fi

echo "PASS: No em-dash characters found."
