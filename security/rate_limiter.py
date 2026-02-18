"""
iTaK Rate Limiter - Prevents abuse and controls API costs.
Token-bucket algorithm with per-adapter and per-model limits.
"""

import time
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token-bucket rate limiter for API calls, messages, and tool executions.

    Supports:
    - Per-adapter limits (e.g., Discord max 10 msgs/min)
    - Per-model limits (e.g., GPT-4 max 60 calls/min)
    - Per-tool limits (e.g., code_execution max 20/min)
    - Global rate limit across all operations
    - Cost-based throttling (daily budget)
    """

    def __init__(self, config: dict | None = None):
        config = config or {}

        # Default limits
        self.limits: dict[str, dict] = {
            "global": {"max_per_minute": config.get("global_rpm", 120), "max_per_hour": config.get("global_rph", 3600)},
            "chat_model": {"max_per_minute": config.get("chat_rpm", 30)},
            "utility_model": {"max_per_minute": config.get("utility_rpm", 60)},
            "browser_model": {"max_per_minute": config.get("browser_rpm", 20)},
            "code_execution": {"max_per_minute": config.get("code_rpm", 30)},
            "web_search": {"max_per_minute": config.get("search_rpm", 20)},
            "browser_agent": {"max_per_minute": config.get("browser_tool_rpm", 10)},
        }

        # Cost budget
        self.daily_budget_usd: float = config.get("daily_budget_usd", 5.0)
        self._daily_cost: float = 0.0
        self._cost_reset_time: float = time.time()

        # Request tracking (using deque for O(1) operations)
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self, category: str = "global") -> tuple[bool, str]:
        """Check if a request is allowed.

        Returns:
            (allowed: bool, reason: str)
        """
        now = time.time()

        # Check daily budget
        self._maybe_reset_daily_cost(now)
        if self._daily_cost >= self.daily_budget_usd:
            return False, f"Daily budget exhausted (${self._daily_cost:.2f}/${self.daily_budget_usd:.2f})"

        # Check category-specific limits
        limits = self.limits.get(category, self.limits.get("global", {}))

        # Clean old entries (O(k) where k is expired entries, not O(n))
        requests_deque = self._requests[category]
        cutoff_hour = now - 3600
        while requests_deque and requests_deque[0] < cutoff_hour:
            requests_deque.popleft()

        # Per-minute check
        max_pm = limits.get("max_per_minute", 120)
        cutoff_minute = now - 60
        recent_minute = sum(1 for t in requests_deque if t >= cutoff_minute)
        if recent_minute >= max_pm:
            # Find the oldest request in the last minute using generator
            first_in_minute = next((t for t in requests_deque if t >= cutoff_minute), None)
            if first_in_minute:
                wait = 60 - (now - first_in_minute)
                return False, f"Rate limit ({category}): {recent_minute}/{max_pm} per minute. Wait {wait:.0f}s."

        # Per-hour check
        max_ph = limits.get("max_per_hour")
        if max_ph:
            recent_hour = len(requests_deque)
            if recent_hour >= max_ph:
                return False, f"Rate limit ({category}): {recent_hour}/{max_ph} per hour."

        # Also check global
        if category != "global":
            allowed, reason = self.check("global")
            if not allowed:
                return allowed, reason

        return True, "OK"

    def record(self, category: str = "global", cost_usd: float = 0.0):
        """Record a request for rate tracking."""
        now = time.time()
        self._requests[category].append(now)
        self._requests["global"].append(now)
        self._daily_cost += cost_usd

    def _maybe_reset_daily_cost(self, now: float):
        """Reset daily cost counter at midnight."""
        if now - self._cost_reset_time > 86400:
            self._daily_cost = 0.0
            self._cost_reset_time = now

    def get_status(self) -> dict:
        """Get current rate limiter status."""
        now = time.time()
        status = {
            "daily_cost": round(self._daily_cost, 4),
            "daily_budget": self.daily_budget_usd,
            "budget_remaining": round(self.daily_budget_usd - self._daily_cost, 4),
        }

        for category in self.limits:
            cutoff = now - 60
            recent = sum(1 for t in self._requests.get(category, deque()) if t >= cutoff)
            max_pm = self.limits[category].get("max_per_minute", "∞")
            status[f"{category}_rpm"] = f"{recent}/{max_pm}"

        return status

    def set_limit(self, category: str, max_per_minute: int | None = None, max_per_hour: int | None = None):
        """Dynamically update rate limits."""
        if category not in self.limits:
            self.limits[category] = {}
        if max_per_minute is not None:
            self.limits[category]["max_per_minute"] = max_per_minute
        if max_per_hour is not None:
            self.limits[category]["max_per_hour"] = max_per_hour

    # ── Auth-failure lockout (OpenClaw-inspired) ──────────────

    def record_auth_failure(self, client_id: str):
        """Record a failed authentication attempt for a client.

        After max_auth_failures within the lockout window, the client
        is locked out and subsequent requests get 429 + Retry-After.
        """
        now = time.time()
        if not hasattr(self, "_auth_failures"):
            self._auth_failures: dict[str, deque[float]] = defaultdict(deque)
            self._auth_lockout_attempts = 5
            self._auth_lockout_seconds = 900  # 15 minutes

        self._auth_failures[client_id].append(now)
        # Keep only recent failures within the lockout window (O(k) cleanup)
        cutoff = now - self._auth_lockout_seconds
        failures_deque = self._auth_failures[client_id]
        while failures_deque and failures_deque[0] <= cutoff:
            failures_deque.popleft()

        count = len(self._auth_failures[client_id])
        if count >= self._auth_lockout_attempts:
            logger.warning(
                f"AUTH_LOCKOUT client={client_id} failures={count} "
                f"locked_for={self._auth_lockout_seconds}s"
            )

    def check_auth_lockout(self, client_id: str) -> tuple[bool, int]:
        """Check if a client is locked out from auth failures.

        Returns:
            (locked_out: bool, retry_after_seconds: int)
        """
        if not hasattr(self, "_auth_failures"):
            return False, 0

        now = time.time()
        lockout_seconds = getattr(self, "_auth_lockout_seconds", 900)
        cutoff = now - lockout_seconds
        failures_deque = self._auth_failures.get(client_id, deque())
        
        # Clean up old failures
        while failures_deque and failures_deque[0] <= cutoff:
            failures_deque.popleft()

        max_attempts = getattr(self, "_auth_lockout_attempts", 5)
        if len(failures_deque) >= max_attempts:
            # Calculate retry-after from the oldest relevant failure
            oldest = failures_deque[0]
            retry_after = int(lockout_seconds - (now - oldest))
            return True, max(retry_after, 1)

        return False, 0

    def record_auth_success(self, client_id: str):
        """Clear auth failure history on successful authentication."""
        if hasattr(self, "_auth_failures") and client_id in self._auth_failures:
            del self._auth_failures[client_id]
