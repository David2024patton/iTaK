#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${1:-${WEBUI_BASE_URL:-http://127.0.0.1:43067}}"

echo "Running full system smoke against: ${BASE_URL}"

failures=0

run_step() {
  local name="$1"
  shift
  echo "---- ${name} ----"
  if "$@"; then
    echo "PASS ${name}"
  else
    echo "FAIL ${name}"
    failures=$((failures + 1))
  fi
  echo
}

run_step "resource-endpoints" /bin/bash tools/check_resource_endpoints.sh "${BASE_URL}"
run_step "memory-smoke" /bin/bash tools/check_memory_smoke.sh
run_step "chat-smoke" /bin/bash tools/check_chat_smoke.sh "${BASE_URL}"

if [[ ${failures} -gt 0 ]]; then
  echo "System smoke failed: ${failures} step(s) failed"
  exit 1
fi

echo "System smoke passed."
