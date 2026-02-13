"""
iTaK Rate Limiter - Prevents abuse and controls API costs.
Token-bucket algorithm with per-adapter and per-model limits.
"""

import time
import logging
from collections import defaultdict
from typing import Optional

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

        # Request tracking
        self._requests: dict[str, list[float]] = defaultdict(list)

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

        # Clean old entries
        self._requests[category] = [t for t in self._requests[category] if now - t < 3600]

        # Per-minute check
        max_pm = limits.get("max_per_minute", 120)
        recent_minute = sum(1 for t in self._requests[category] if now - t < 60)
        if recent_minute >= max_pm:
            wait = 60 - (now - self._requests[category][-max_pm])
            return False, f"Rate limit ({category}): {recent_minute}/{max_pm} per minute. Wait {wait:.0f}s."

        # Per-hour check
        max_ph = limits.get("max_per_hour")
        if max_ph:
            recent_hour = len(self._requests[category])
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
            recent = sum(1 for t in self._requests.get(category, []) if now - t < 60)
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
