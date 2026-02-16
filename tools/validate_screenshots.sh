#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCREENSHOT_DIR="${SCREENSHOT_DIR:-${REPO_ROOT}/screenshots}"
CHECKLIST_FILE="${CHECKLIST_FILE:-${SCREENSHOT_DIR}/CAPTURE_CHECKLIST.md}"
ALLOW_EXTRA=false

usage() {
  cat <<'EOF'
Usage: tools/validate_screenshots.sh [--allow-extra] [--dir <path>] [--checklist <path>]

Validates screenshot files against names listed in screenshots/CAPTURE_CHECKLIST.md.

Options:
  --allow-extra        Allow PNG files not listed in checklist
  --dir <path>         Override screenshots directory (default: screenshots/)
  --checklist <path>   Override checklist file path
  -h, --help           Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --allow-extra)
      ALLOW_EXTRA=true
      shift
      ;;
    --dir)
      SCREENSHOT_DIR="$2"
      shift 2
      ;;
    --checklist)
      CHECKLIST_FILE="$2"
      shift 2
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

if [[ ! -f "${CHECKLIST_FILE}" ]]; then
  echo "Checklist not found: ${CHECKLIST_FILE}" >&2
  exit 2
fi

if [[ ! -d "${SCREENSHOT_DIR}" ]]; then
  echo "Screenshot directory not found: ${SCREENSHOT_DIR}" >&2
  exit 2
fi

mapfile -t expected < <(sed -n 's/^- \[ \] `\([^`]*\.png\)`.*/\1/p' "${CHECKLIST_FILE}")

if [[ ${#expected[@]} -eq 0 ]]; then
  echo "No expected PNG filenames found in checklist: ${CHECKLIST_FILE}" >&2
  exit 2
fi

mapfile -t actual_png < <(find "${SCREENSHOT_DIR}" -maxdepth 1 -type f -name '*.png' -printf '%f\n' | sort)
mapfile -t non_png < <(find "${SCREENSHOT_DIR}" -maxdepth 1 -type f ! -name '*.png' ! -name 'CAPTURE_CHECKLIST.md' -printf '%f\n' | sort)

declare -A actual_set=()
declare -A expected_set=()

for file in "${actual_png[@]}"; do
  actual_set["$file"]=1
done

for file in "${expected[@]}"; do
  expected_set["$file"]=1
done

missing=()
for file in "${expected[@]}"; do
  if [[ -z "${actual_set[$file]:-}" ]]; then
    missing+=("$file")
  fi
done

extra=()
if [[ "${ALLOW_EXTRA}" != "true" ]]; then
  for file in "${actual_png[@]}"; do
    if [[ -z "${expected_set[$file]:-}" ]]; then
      extra+=("$file")
    fi
  done
fi

status=0

echo "Screenshot validation"
echo "- Checklist: ${CHECKLIST_FILE}"
echo "- Directory: ${SCREENSHOT_DIR}"
echo "- Expected PNGs: ${#expected[@]}"
echo "- Actual PNGs: ${#actual_png[@]}"

if [[ ${#missing[@]} -gt 0 ]]; then
  status=1
  echo
  echo "Missing (${#missing[@]}):"
  for file in "${missing[@]}"; do
    echo "  - ${file}"
  done
fi

if [[ ${#extra[@]} -gt 0 ]]; then
  status=1
  echo
  echo "Unexpected PNGs (${#extra[@]}):"
  for file in "${extra[@]}"; do
    echo "  - ${file}"
  done
fi

if [[ ${#non_png[@]} -gt 0 ]]; then
  status=1
  echo
  echo "Non-PNG files in screenshots/ (${#non_png[@]}):"
  for file in "${non_png[@]}"; do
    echo "  - ${file}"
  done
fi

if [[ ${status} -eq 0 ]]; then
  echo
  echo "PASS: Screenshot set matches checklist."
else
  echo
  echo "FAIL: Screenshot set does not match checklist."
fi

exit ${status}
