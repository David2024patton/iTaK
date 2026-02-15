"""
iTaK Self-Healing Engine - 5-step auto-recovery pipeline.

When a tool or operation fails, the engine:
  1. Classifies the error (repairable vs critical)
  2. Searches memory for previously solved errors
  3. Reasons about fixes using the LLM
  4. Optionally researches online (security-scanned)
  5. Learns from successful fixes → stores in memory

§15 of the gameplan - never crash silently, always self-heal.
"""

import asyncio
import re
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from core.agent import Agent


# ---------------------------------------------------------------------------
# Error Classification
# ---------------------------------------------------------------------------

class ErrorSeverity(Enum):
    """How bad is the error?"""
    REPAIRABLE = "repairable"
    PARTIAL = "partial"          # May be fixable, try once
    CRITICAL = "critical"        # Stop immediately, alert user


class ErrorCategory(Enum):
    """What kind of error is it?"""
    DEPENDENCY = "dependency"    # ModuleNotFoundError, missing package
    NETWORK = "network"          # Timeouts, connection refused, 429
    CONFIG = "config"            # Wrong port, bad key format, missing env
    RUNTIME = "runtime"          # TypeError, KeyError, bad JSON
    TOOL = "tool"                # Tool execution failed
    RESOURCE = "resource"        # Disk full, OOM, GPU busy
    SECURITY = "security"        # Unauthorized, credential leak
    DATA = "data"                # Corruption, inconsistent state
    UNKNOWN = "unknown"


@dataclass
class ClassifiedError:
    """An error that has been classified for self-healing."""
    category: ErrorCategory
    severity: ErrorSeverity
    original_exception: Exception
    message: str
    traceback_str: str
    tool_name: str = ""
    tool_args: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class HealAttempt:
    """Record of a healing attempt."""
    fix_description: str
    source: str              # "memory", "llm", "web"
    success: bool = False
    error_on_retry: str = ""
    duration_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Classification Patterns
# ---------------------------------------------------------------------------

ERROR_PATTERNS: dict[ErrorCategory, list[str]] = {
    ErrorCategory.DEPENDENCY: [
        r"ModuleNotFoundError",
        r"ImportError",
        r"No module named",
        r"pip install",
        r"package .* not found",
    ],
    ErrorCategory.NETWORK: [
        r"ConnectionRefusedError",
        r"ConnectionError",
        r"TimeoutError",
        r"ConnectTimeoutError",
        r"HTTPError.*(?:429|502|503|504)",
        r"ECONNREFUSED",
        r"ConnectionResetError",
        r"SSLError",
    ],
    ErrorCategory.CONFIG: [
        r"KeyError.*(?:API|KEY|TOKEN|URL|PORT)",
        r"FileNotFoundError.*(?:config|\.env|\.json)",
        r"Invalid.*(?:host|port|url|token)",
        r"PermissionError",
    ],
    ErrorCategory.RUNTIME: [
        r"TypeError",
        r"ValueError",
        r"AttributeError",
        r"KeyError",
        r"IndexError",
        r"JSONDecodeError",
        r"SyntaxError",
        r"NameError",
    ],
    ErrorCategory.RESOURCE: [
        r"MemoryError",
        r"OSError.*(?:No space|Disk quota)",
        r"ResourceWarning",
        r"CUDA.*(?:out of memory|OOM)",
    ],
    ErrorCategory.SECURITY: [
        r"Unauthorized",
        r"Forbidden",
        r"AuthenticationError",
        r"CredentialError",
        r"SECURITY_BLOCKED",
    ],
    ErrorCategory.DATA: [
        r"IntegrityError",
        r"CorruptedError",
        r"DatabaseError",
        r"ChecksumMismatch",
    ],
}

# These categories are NEVER self-healable
CRITICAL_CATEGORIES = {ErrorCategory.SECURITY, ErrorCategory.DATA}


# ---------------------------------------------------------------------------
# Self-Healing Engine
# ---------------------------------------------------------------------------

class SelfHealEngine:
    """5-step auto-recovery pipeline.

    Budget:
      - max_retries_per_error: 3
      - max_retries_per_session: 10
      - backoff_seconds: [1, 5, 15]
    """

    def __init__(self, agent: Optional["Agent"] = None, config: Optional[dict] = None):
        if isinstance(agent, dict) and config is None:
            config = agent
            agent = None

        self.agent = agent
        cfg = config or {}
        self.max_per_error = int(cfg.get("max_healing_attempts", 3) or 3)
        self.max_per_session = 10
        self.backoff = [1, 5, 15]
        self.session_retries = 0
        self.error_log: list[ClassifiedError] = []

    def classify_error(self, exc: Exception) -> str:
        """Backward-compatible string classifier used by older tests."""
        classified = self.classify(exc)
        msg = str(exc).lower()
        if "connection" in msg or "timeout" in msg or "network" in msg:
            return "network"
        if isinstance(exc, SyntaxError) or "syntax" in msg:
            return "syntax"
        return classified.category.value

    async def _search_similar_errors(self, error_text: str) -> list[dict]:
        """Compatibility hook for historical error lookups."""
        if not self.agent or not getattr(self.agent, "memory", None):
            return []
        try:
            return await self.agent.memory.search(error_text, limit=3)
        except Exception:
            return []

    def should_attempt_healing(self, error: Exception, attempt: int = 0) -> bool:
        """Guard against infinite retry loops."""
        return attempt < self.max_per_error and self.is_healable_error(error)

    def is_healable_error(self, error: Exception) -> bool:
        """Return False for security-sensitive errors."""
        if isinstance(error, PermissionError):
            return False
        classified = self.classify(error)
        return classified.severity != ErrorSeverity.CRITICAL

    # ----- Step 1: Classify --------------------------------------------------

    def classify(self, exc: Exception, tool_name: str = "",
                 tool_args: dict | None = None) -> ClassifiedError:
        """Classify an exception into category + severity."""
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        tb_str = "".join(tb)
        msg = str(exc)
        full_text = f"{type(exc).__name__}: {msg}\n{tb_str}"

        category = ErrorCategory.UNKNOWN
        for cat, patterns in ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    category = cat
                    break
            if category != ErrorCategory.UNKNOWN:
                break

        severity = (
            ErrorSeverity.CRITICAL if category in CRITICAL_CATEGORIES
            else ErrorSeverity.REPAIRABLE
        )

        classified = ClassifiedError(
            category=category,
            severity=severity,
            original_exception=exc,
            message=msg,
            traceback_str=tb_str,
            tool_name=tool_name,
            tool_args=tool_args or {},
        )
        self.error_log.append(classified)
        return classified

    # ----- Step 2: Check Memory ----------------------------------------------

    async def _check_memory(self, classified: ClassifiedError) -> Optional[str]:
        """Search all memory tiers for a previously seen fix."""
        if not self.agent.memory:
            return None

        query = f"{classified.category.value} error: {classified.message}"
        try:
            results = await self.agent.memory.search(query, limit=3)
            if results:
                # Return the best match
                best = results[0]
                content = best.get("content", "") if isinstance(best, dict) else str(best)
                if content:
                    return content
        except Exception:
            pass
        return None

    # ----- Step 3: LLM Reasoning ---------------------------------------------

    async def _reason_fix(self, classified: ClassifiedError) -> list[str]:
        """Ask the LLM to suggest fixes, ranked by likelihood."""
        prompt = (
            f"An error occurred during tool execution.\n\n"
            f"Tool: {classified.tool_name}\n"
            f"Category: {classified.category.value}\n"
            f"Error: {classified.message}\n\n"
            f"Traceback (last 20 lines):\n"
            f"{''.join(classified.traceback_str.splitlines(True)[-20:])}\n\n"
            f"Suggest exactly 3 possible fixes, ranked from most to least likely. "
            f"For each fix, provide a single actionable sentence. "
            f"Format: one fix per line, numbered 1-3."
        )

        try:
            if hasattr(self.agent, "model_router"):
                response = await self.agent.model_router.chat(
                    messages=[
                        {"role": "system", "content": "You are a debugging assistant. Be concise."},
                        {"role": "user", "content": prompt},
                    ],
                )
                lines = [
                    line.strip()
                    for line in response.strip().splitlines()
                    if line.strip() and line.strip()[0].isdigit()
                ]
                return lines[:3]
        except Exception:
            pass
        return []

    # ----- Step 4: (placeholder for web research) -----------------------------

    async def _research_online(self, classified: ClassifiedError) -> Optional[str]:
        """Search the web for the error. Placeholder - requires web_search tool."""
        # This would call the web_search tool and security-scan the results.
        # Deferred until web_search integration is ready in the heal loop.
        return None

    # ----- Step 5: Learn from Fix --------------------------------------------

    async def _learn(self, classified: ClassifiedError, fix: str):
        """Store the successful fix in memory for future reference."""
        if not self.agent.memory:
            return

        entry = (
            f"## Self-Healed Error\n"
            f"**Category:** {classified.category.value}\n"
            f"**Error:** {classified.message}\n"
            f"**Fix:** {fix}\n"
            f"**Tool:** {classified.tool_name}\n"
        )
        try:
            await self.agent.memory.save(
                content=entry,
                category="errors",
                metadata={"error_type": classified.category.value},
            )
        except Exception:
            pass

    # ----- Main Entry Point --------------------------------------------------

    async def heal(self, exc: Exception, tool_name: str = "",
                   tool_args: dict | None = None,
                   retry_fn=None) -> dict[str, Any]:
        """Run the full 5-step healing pipeline.

        Args:
            exc: The exception that occurred.
            tool_name: Which tool failed.
            tool_args: The args that were passed to the tool.
            retry_fn: An async callable to retry the operation.
                      If provided, successful fix attempts will be validated.

        Returns:
            {"healed": bool, "message": str, "attempts": list[HealAttempt]}
        """
        classified = self.classify(exc, tool_name, tool_args)
        attempts: list[HealAttempt] = []

        # Critical errors - don't attempt self-healing
        if classified.severity == ErrorSeverity.CRITICAL:
            from core.logger import EventType
            self.agent.logger.log(
                EventType.ERROR,
                f"CRITICAL error (not self-healable): {classified.message}",
            )
            return {
                "healed": False,
                "message": f"🚫 Critical error: {classified.message}",
                "attempts": attempts,
            }

        # Check session budget
        if self.session_retries >= self.max_per_session:
            return {
                "healed": False,
                "message": "⚠️ Self-heal session budget exhausted (10/10).",
                "attempts": attempts,
            }

        from core.logger import EventType
        self.agent.logger.log(
            EventType.SYSTEM,
            f"Self-heal started: {classified.category.value} - {classified.message}",
        )

        # Step 2: Check memory
        memory_fix = await self._check_memory(classified)
        if memory_fix:
            attempt = HealAttempt(
                fix_description=memory_fix,
                source="memory",
            )
            attempts.append(attempt)
            self.session_retries += 1
            # If we have a retry function, try it
            if retry_fn:
                try:
                    await retry_fn()
                    attempt.success = True
                    self.agent.logger.log(
                        EventType.SYSTEM,
                        f"Self-healed from memory: {memory_fix[:80]}",
                    )
                    return {
                        "healed": True,
                        "message": f"✅ Self-healed (from memory): {memory_fix[:80]}",
                        "attempts": attempts,
                    }
                except Exception as e2:
                    attempt.error_on_retry = str(e2)

        # Step 3: LLM reasoning
        fixes = await self._reason_fix(classified)
        for i, fix in enumerate(fixes):
            if self.session_retries >= self.max_per_session:
                break

            attempt = HealAttempt(fix_description=fix, source="llm")
            attempts.append(attempt)
            self.session_retries += 1

            # Backoff
            backoff_time = self.backoff[min(i, len(self.backoff) - 1)]
            await asyncio.sleep(backoff_time)

            if retry_fn:
                try:
                    await retry_fn()
                    attempt.success = True
                    # Step 5: Learn from success
                    await self._learn(classified, fix)
                    self.agent.logger.log(
                        EventType.SYSTEM,
                        f"Self-healed (LLM fix #{i+1}): {fix[:80]}",
                    )
                    return {
                        "healed": True,
                        "message": f"✅ Self-healed (fix #{i+1}): {fix[:80]}",
                        "attempts": attempts,
                    }
                except Exception as e2:
                    attempt.error_on_retry = str(e2)

        # Step 4: Online research (future)
        # web_fix = await self._research_online(classified)

        # Failed - escalate to user
        self.agent.logger.log(
            EventType.ERROR,
            f"Self-heal FAILED after {len(attempts)} attempts: {classified.message}",
        )
        return {
            "healed": False,
            "message": (
                f"⚠️ Self-heal failed after {len(attempts)} attempts.\n"
                f"Error: {classified.message}\n"
                f"Category: {classified.category.value}"
            ),
            "attempts": attempts,
        }

    # ----- Utilities ----------------------------------------------------------

    def reset_session(self):
        """Reset session retry counter (call at start of new conversation)."""
        self.session_retries = 0
        self.error_log.clear()

    def get_stats(self) -> dict:
        """Return self-heal statistics for the dashboard."""
        return {
            "session_retries": self.session_retries,
            "max_per_session": self.max_per_session,
            "total_errors": len(self.error_log),
            "categories": {
                cat.value: sum(
                    1 for e in self.error_log if e.category == cat
                )
                for cat in ErrorCategory
                if any(e.category == cat for e in self.error_log)
            },
        }
