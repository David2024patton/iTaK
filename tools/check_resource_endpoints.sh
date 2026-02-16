#!/usr/bin/env bash

set -u

BASE_URL="${1:-${WEBUI_BASE_URL:-http://127.0.0.1:43067}}"
ENDPOINTS=(
  "resource_hub"
  "launchpad_apps"
  "catalog_refresh"
  "catalog_sync_from_cherry"
)

ok_count=0
fail_count=0

echo "Checking endpoints against: ${BASE_URL}"

for endpoint in "${ENDPOINTS[@]}"; do
  tmp_file="$(mktemp)"
  status_code="$(curl --max-time 20 -s -o "${tmp_file}" -w '%{http_code}' \
    -H 'Content-Type: application/json' \
    -d '{}' \
    "${BASE_URL}/${endpoint}" || true)"

  if [[ "${status_code}" == "200" ]]; then
    echo "PASS ${endpoint} -> ${status_code}"
    ok_count=$((ok_count + 1))
  else
    echo "FAIL ${endpoint} -> ${status_code}"
    head -c 240 "${tmp_file}" | tr '\n' ' '
    echo
    fail_count=$((fail_count + 1))
  fi

  rm -f "${tmp_file}"
done

echo "Summary: ${ok_count} passed, ${fail_count} failed"

if [[ ${fail_count} -gt 0 ]]; then
  exit 1
fi

exit 0
