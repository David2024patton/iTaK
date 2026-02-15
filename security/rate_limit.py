from security.rate_limiter import RateLimiter as _RateLimiter


class RateLimiter(_RateLimiter):
    def __init__(self, requests_per_minute: int | None = None, cost_limit: float | None = None, **kwargs):
        config = kwargs.pop("config", {}) or {}
        if requests_per_minute is not None:
            config["global_rpm"] = requests_per_minute
        if cost_limit is not None:
            config["daily_budget_usd"] = cost_limit
        super().__init__(config=config)

    def check(self, category: str = "global") -> bool:
        allowed, _ = _RateLimiter.check(self, "global")
        if allowed:
            _RateLimiter.record(self, "global")
        return allowed

    def check_cost(self, category: str, cost: float) -> bool:
        allowed, _ = _RateLimiter.check(self, "global")
        if not allowed:
            return False
        _RateLimiter.record(self, "global", cost_usd=cost)
        return True
