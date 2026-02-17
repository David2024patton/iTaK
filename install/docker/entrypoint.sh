#!/usr/bin/env sh
set -e

python /app/install/docker/bootstrap.py

if [ "$#" -gt 0 ]; then
  exec python -m app.main "$@"
fi

if [ -n "${ITAK_ARGS:-}" ]; then
  exec python -m app.main ${ITAK_ARGS}
fi

exec python -m app.main --webui-only
