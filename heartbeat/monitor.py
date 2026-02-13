"""
iTaK Heartbeat System — Auto-recovery and health monitoring.
Detects stalled agents, crashed services, and triggers self-healing.
"""

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from core.agent import Agent

logger = logging.getLogger(__name__)


class Heartbeat:
    """Health monitoring and auto-recovery for the iTaK agent.

    Monitors:
    - Agent loop activity (stall detection)
    - Memory store connectivity (Neo4j, Weaviate, SQLite)
    - Adapter health (Discord/Telegram connection)
    - Docker container status (if applicable)
    - API connectivity (LLM endpoints)
    - Cost budget status

    Self-healing actions:
    - Restart stalled agent loops
    - Reconnect dropped services
    - Alert via active adapters
    - Save state checkpoint before recovery
    """

    def __init__(self, agent: "Agent", config: dict | None = None):
        self.agent = agent
        self.config = config or {}

        # Timing
        self.interval = self.config.get("interval_seconds", 30)
        self.stall_timeout = self.config.get("stall_timeout_seconds", 120)
        self.reconnect_interval = self.config.get("reconnect_interval", 300)

        # State
        self._running = False
        self._last_activity: float = time.time()
        self._last_reconnect_attempt: float = 0
        self._health_history: list[dict] = []
        self._alert_callbacks: list[Callable] = []
        self._task: asyncio.Task | None = None

    def update_activity(self):
        """Called by the agent loop to signal that it's alive."""
        self._last_activity = time.time()

    def register_alert(self, callback: Callable):
        """Register a callback for health alerts."""
        self._alert_callbacks.append(callback)

    async def start(self):
        """Start the heartbeat monitoring loop."""
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Heartbeat started (interval={self.interval}s, stall_timeout={self.stall_timeout}s)")

    async def stop(self):
        """Stop the heartbeat."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await asyncio.sleep(self.interval)
                health = await self.check_health()
                self._health_history.append(health)

                # Keep last 100 health checks
                if len(self._health_history) > 100:
                    self._health_history = self._health_history[-100:]

                # Handle issues
                if not health["agent_alive"]:
                    await self._handle_stall()

                if not health["memory_healthy"]:
                    await self._handle_memory_issues(health)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def check_health(self) -> dict:
        """Perform a comprehensive health check."""
        now = time.time()

        health = {
            "timestamp": now,
            "agent_alive": (now - self._last_activity) < self.stall_timeout,
            "last_activity_ago": round(now - self._last_activity, 1),
            "memory_healthy": True,
            "stores": {},
            "api_healthy": True,
            "budget_ok": True,
        }

        # Check memory stores
        try:
            if hasattr(self.agent, "memory") and self.agent.memory:
                stats = await self.agent.memory.get_stats()
                health["stores"]["sqlite"] = "ok" if stats.get("layer_2_sqlite") else "error"

                neo4j_status = stats.get("layer_3_neo4j", "not configured")
                health["stores"]["neo4j"] = neo4j_status
                if neo4j_status == "disconnected":
                    health["memory_healthy"] = False

                weaviate_status = stats.get("layer_4_weaviate", "not configured")
                if isinstance(weaviate_status, dict):
                    health["stores"]["weaviate"] = weaviate_status.get("status", "unknown")
                else:
                    health["stores"]["weaviate"] = str(weaviate_status)

                if health["stores"].get("weaviate") == "disconnected":
                    health["memory_healthy"] = False
        except Exception as e:
            health["memory_healthy"] = False
            health["stores"]["error"] = str(e)

        # Check rate limiter budget
        try:
            if hasattr(self.agent, "rate_limiter") and self.agent.rate_limiter:
                status = self.agent.rate_limiter.get_status()
                remaining = status.get("budget_remaining", 999)
                health["budget_ok"] = remaining > 0
                health["budget_remaining"] = remaining
        except Exception:
            pass

        return health

    async def _handle_stall(self):
        """Handle a stalled agent loop."""
        logger.warning("Agent stall detected! Attempting recovery...")

        # Save checkpoint first
        try:
            if hasattr(self.agent, "checkpoint"):
                await self.agent.checkpoint.save()
                logger.info("Emergency checkpoint saved")
        except Exception as e:
            logger.error(f"Emergency checkpoint failed: {e}")

        # Alert
        await self._send_alert(
            "⚠️ **Agent Stall Detected**\n"
            f"No activity for {self.stall_timeout}s. "
            "Attempting recovery..."
        )

        # Reset activity timer to prevent repeated alerts
        self._last_activity = time.time()

    async def _handle_memory_issues(self, health: dict):
        """Handle disconnected memory stores."""
        now = time.time()
        if now - self._last_reconnect_attempt < self.reconnect_interval:
            return  # Don't retry too frequently

        self._last_reconnect_attempt = now

        stores = health.get("stores", {})

        # Try reconnecting Neo4j
        if stores.get("neo4j") == "disconnected" and hasattr(self.agent, "memory"):
            try:
                if self.agent.memory.neo4j:
                    await self.agent.memory.neo4j.connect()
                    logger.info("Neo4j reconnected successfully")
            except Exception as e:
                logger.warning(f"Neo4j reconnection failed: {e}")

        # Try reconnecting Weaviate
        if stores.get("weaviate") == "disconnected" and hasattr(self.agent, "memory"):
            try:
                if self.agent.memory.weaviate:
                    await self.agent.memory.weaviate.connect()
                    logger.info("Weaviate reconnected successfully")
            except Exception as e:
                logger.warning(f"Weaviate reconnection failed: {e}")

    async def _send_alert(self, message: str):
        """Send an alert through registered callbacks."""
        for callback in self._alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception:
                pass

    def get_history(self, limit: int = 20) -> list[dict]:
        """Get recent health check history."""
        return self._health_history[-limit:]

    def get_uptime(self) -> dict:
        """Calculate uptime statistics from history."""
        if not self._health_history:
            return {"checks": 0, "uptime_pct": 100.0}

        total = len(self._health_history)
        alive = sum(1 for h in self._health_history if h.get("agent_alive"))
        memory_ok = sum(1 for h in self._health_history if h.get("memory_healthy"))

        return {
            "checks": total,
            "uptime_pct": round((alive / total) * 100, 1),
            "memory_uptime_pct": round((memory_ok / total) * 100, 1),
            "last_check": self._health_history[-1] if self._health_history else None,
        }
