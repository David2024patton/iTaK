#!/usr/bin/env bash

set -euo pipefail

echo "Running memory smoke test (save/search/delete)..."

/bin/python3 - <<'PY'
import asyncio
import json
import time
from memory.manager import MemoryManager


async def main() -> int:
    cfg = json.load(open("config.json", "r", encoding="utf-8"))
    mem_cfg = cfg.get("memory", {})
    manager = MemoryManager(config=mem_cfg, full_config=cfg)

    marker = f"memory-smoke-{int(time.time())}"
    content = f"Memory smoke test entry: {marker}"

    memory_id = await manager.save(
        content=content,
        category="test",
        metadata={"source": "memory-smoke-script"},
    )

    results = await manager.search(query=marker, limit=5)
    found = any(marker in (item.get("content") or "") for item in results)

    deleted = await manager.delete(memory_id)

    print(
        {
            "memory_id": memory_id,
            "results": len(results),
            "found": found,
            "deleted": deleted,
        }
    )

    if not found or deleted < 1:
        return 2
    return 0


raise SystemExit(asyncio.run(main()))
PY

echo "Memory smoke test passed."
