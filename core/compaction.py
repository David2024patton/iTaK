"""
iTaK Compaction Guard - Prevents duplicate/concurrent context compaction.

Ensures that transcript compaction only runs once per threshold crossing,
even if multiple triggers fire simultaneously (cache TTL bypass, etc.).
"""

import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class CompactionGuard:
    """Prevents double-compaction of conversation context.

    Inspired by OpenClaw fix #13514 which addressed double compaction
    caused by cache TTL bypassing the guard flag.

    Usage:
        guard = CompactionGuard(threshold_tokens=80000)
        if guard.should_compact(current_tokens):
            async with guard.compacting():
                await do_compaction()
    """

    def __init__(
        self,
        threshold_tokens: int = 80000,
        cooldown_seconds: float = 60.0,
    ):
        self._threshold = threshold_tokens
        self._cooldown = cooldown_seconds
        self._lock = asyncio.Lock()
        self._last_compaction: float = 0
        self._compaction_count: int = 0

    def should_compact(self, current_tokens: int) -> bool:
        """Check if compaction is needed AND allowed.

        Returns True only if:
        1. Current token count exceeds threshold
        2. Not currently compacting (lock is free)
        3. Cooldown period has elapsed since last compaction
        """
        if current_tokens < self._threshold:
            return False

        if self._lock.locked():
            logger.debug("Compaction skipped: already in progress")
            return False

        if time.time() - self._last_compaction < self._cooldown:
            logger.debug("Compaction skipped: cooldown active")
            return False

        return True

    class _CompactionContext:
        """Async context manager for compaction."""

        def __init__(self, guard: "CompactionGuard"):
            self._guard = guard

        async def __aenter__(self):
            await self._guard._lock.acquire()
            logger.info("Compaction started")
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            self._guard._last_compaction = time.time()
            self._guard._compaction_count += 1
            self._guard._lock.release()
            if exc_type:
                logger.error(f"Compaction failed: {exc_val}")
            else:
                logger.info(
                    f"Compaction #{self._guard._compaction_count} complete"
                )
            return False  # Don't suppress exceptions

    def compacting(self) -> "_CompactionContext":
        """Return an async context manager that holds the compaction lock."""
        return self._CompactionContext(self)

    def get_status(self) -> dict:
        """Get compaction guard status."""
        return {
            "threshold_tokens": self._threshold,
            "cooldown_seconds": self._cooldown,
            "compaction_count": self._compaction_count,
            "last_compaction_ago": round(
                time.time() - self._last_compaction, 1
            ) if self._last_compaction else None,
            "is_compacting": self._lock.locked(),
        }
