#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${1:-${WEBUI_BASE_URL:-http://127.0.0.1:43067}}"

echo "Running chat smoke test against: ${BASE_URL}"

ctx_id="$(
  curl --max-time 15 -sS \
    -H 'Content-Type: application/json' \
    -d '{}' \
    "${BASE_URL}/chat_create" \
  | /bin/python3 -c "import sys,json; print(json.load(sys.stdin).get('ctxid',''))"
)"

if [[ -z "${ctx_id}" ]]; then
  echo "FAIL chat_create did not return ctxid"
  exit 1
fi

curl --max-time 45 -sS \
  -H 'Content-Type: application/json' \
  -d "{\"text\":\"hello from chat smoke\",\"context\":\"${ctx_id}\"}" \
  "${BASE_URL}/message_async" >/tmp/chat_smoke_send.out

poll_json="$(
  curl --max-time 15 -sS \
    -H 'Content-Type: application/json' \
    -d "{\"log_from\":0,\"notifications_from\":0,\"context\":\"${ctx_id}\"}" \
    "${BASE_URL}/poll"
)"

echo "${poll_json}" | /bin/python3 -c "import sys,json; d=json.load(sys.stdin); logs=d.get('logs',[]); has_user=any((x.get('type') or '').lower()=='user' for x in logs); has_resp=any((x.get('type') or '').lower()=='response' for x in logs); print({'ctxid':'${ctx_id}','log_count':len(logs),'has_user':has_user,'has_response':has_resp}); raise SystemExit(0 if (has_user and has_resp) else 2)"

echo "Chat smoke test passed."
