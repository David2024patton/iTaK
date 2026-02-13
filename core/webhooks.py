"""
iTaK Webhook Engine - Bidirectional n8n / Zapier integration.

Inbound:  External services POST tasks to iTaK
Outbound: iTaK fires webhooks on events (task_completed, error_critical, etc.)

Gameplan §21 - "Workflow Automation"
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("itak.webhooks")


class WebhookEvent(str, Enum):
    """Events that can trigger outbound webhooks."""
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    ERROR_CRITICAL = "error_critical"
    DAILY_REPORT = "daily_report"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"


@dataclass
class WebhookTarget:
    """An outbound webhook target."""
    name: str                       # "n8n", "zapier", "custom"
    url: str                        # Webhook URL
    events: list[str]               # Which events trigger this target
    headers: dict = field(default_factory=dict)  # Extra headers
    enabled: bool = True
    last_fired: float = 0.0
    last_status: int = 0
    failures: int = 0


@dataclass
class InboundPayload:
    """Parsed inbound webhook request."""
    title: str
    message: str
    source: str = "webhook"
    priority: str = "medium"
    callback_url: str = ""           # Optional URL to POST results back to
    metadata: dict = field(default_factory=dict)


class WebhookEngine:
    """
    Bidirectional webhook system for external automation integration.

    Inbound (POST /api/webhook):
      - Receives task payloads from n8n/Zapier
      - Creates a task on the Mission Control board
      - Runs the agent on the task
      - Returns the result (or fires callback)

    Outbound (event-driven):
      - Fires HTTP POSTs to configured URLs on events
      - Non-blocking: failures logged, don't block agent
      - Configurable per-target event filtering
    """

    def __init__(self, agent, config: dict | None = None):
        self.agent = agent
        self.config = config or {}
        self.targets: dict[str, WebhookTarget] = {}
        self.inbound_secret = ""
        self._stats = {
            "inbound_received": 0,
            "inbound_processed": 0,
            "inbound_errors": 0,
            "outbound_fired": 0,
            "outbound_failures": 0,
        }

        self._load_config()

    def _load_config(self):
        """Load webhook configuration from config."""
        integrations = self.config.get("integrations", {})
        self.inbound_secret = integrations.get("inbound_webhook_secret", "")

        # Load outbound targets
        for name, target_config in integrations.get("outbound", {}).items():
            if isinstance(target_config, dict) and target_config.get("url"):
                self.targets[name] = WebhookTarget(
                    name=name,
                    url=target_config["url"],
                    events=target_config.get("events", ["task_completed"]),
                    headers=target_config.get("headers", {}),
                    enabled=target_config.get("enabled", True),
                )

        if self.targets:
            logger.info(
                f"Webhook Engine: {len(self.targets)} outbound targets configured"
            )

    # ── Inbound ────────────────────────────────────────────────

    def verify_secret(self, provided: str) -> bool:
        """Verify the inbound webhook secret."""
        if not self.inbound_secret:
            return True  # No secret configured = open
        return provided == self.inbound_secret

    def parse_inbound(self, data: dict) -> InboundPayload:
        """Parse and validate an inbound webhook payload."""
        return InboundPayload(
            title=data.get("title", data.get("subject", "Webhook task")),
            message=data.get("message", data.get("body", data.get("text", ""))),
            source=data.get("source", "webhook"),
            priority=data.get("priority", "medium"),
            callback_url=data.get("callback_url", ""),
            metadata=data.get("metadata", {}),
        )

    async def process_inbound(self, payload: InboundPayload) -> dict:
        """
        Process an inbound webhook payload.

        Creates a task, (optionally) runs the agent, returns result.
        """
        self._stats["inbound_received"] += 1

        try:
            # Create task on board
            task = None
            if hasattr(self.agent, 'task_board') and self.agent.task_board:
                task = self.agent.task_board.create(
                    title=payload.title,
                    description=payload.message,
                    priority=payload.priority,
                    source=payload.source,
                )

            # Process through agent
            result = ""
            if payload.message:
                try:
                    result = await self.agent.monologue(payload.message)
                except Exception as e:
                    logger.error(f"Webhook agent processing failed: {e}")
                    result = f"Error: {e}"
                    self._stats["inbound_errors"] += 1

                    if task:
                        self.agent.task_board.fail(task.id, str(e))

                    return {
                        "status": "error",
                        "task_id": task.id if task else None,
                        "error": str(e),
                    }

            # Mark task done
            if task:
                self.agent.task_board.complete(task.id)

            self._stats["inbound_processed"] += 1

            response = {
                "status": "completed",
                "task_id": task.id if task else None,
                "result": result,
                "timestamp": time.time(),
            }

            # Fire callback if requested
            if payload.callback_url:
                asyncio.create_task(
                    self._fire_callback(payload.callback_url, response)
                )

            return response

        except Exception as e:
            self._stats["inbound_errors"] += 1
            logger.error(f"Inbound webhook processing failed: {e}")
            return {"status": "error", "error": str(e)}

    # ── Outbound ───────────────────────────────────────────────

    async def fire(self, event: str | WebhookEvent, data: dict):
        """
        Fire outbound webhooks for an event.

        Non-blocking: runs in background, failures are logged.
        """
        event_str = event.value if isinstance(event, WebhookEvent) else event

        for target in self.targets.values():
            if not target.enabled:
                continue
            if event_str not in target.events:
                continue

            # Fire in background - don't block agent
            asyncio.create_task(
                self._fire_target(target, event_str, data)
            )

    async def _fire_target(self, target: WebhookTarget, event: str, data: dict):
        """Fire a single outbound webhook target."""
        import aiohttp

        payload = {
            "event": event,
            "timestamp": time.time(),
            "agent": "iTaK",
            "data": data,
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "iTaK-Webhook/1.0",
            **target.headers,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    target.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    target.last_fired = time.time()
                    target.last_status = resp.status

                    if resp.status >= 400:
                        target.failures += 1
                        self._stats["outbound_failures"] += 1
                        logger.warning(
                            f"Webhook {target.name} returned {resp.status}: "
                            f"{await resp.text()}"
                        )
                    else:
                        self._stats["outbound_fired"] += 1
                        logger.info(
                            f"Webhook {target.name} fired: {event} → {resp.status}"
                        )

        except ImportError:
            # aiohttp not installed - fall back to urllib
            await self._fire_target_urllib(target, payload, headers)
        except Exception as e:
            target.failures += 1
            self._stats["outbound_failures"] += 1
            logger.error(f"Webhook {target.name} failed: {e}")

    async def _fire_target_urllib(self, target: WebhookTarget,
                                  payload: dict, headers: dict):
        """Fallback webhook firing using urllib (no aiohttp dependency)."""
        import urllib.request

        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                target.url, data=data, headers=headers, method="POST"
            )
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: urllib.request.urlopen(req, timeout=30)
            )
            target.last_fired = time.time()
            target.last_status = resp.status
            self._stats["outbound_fired"] += 1
            logger.info(f"Webhook {target.name} fired (urllib): {resp.status}")
        except Exception as e:
            target.failures += 1
            self._stats["outbound_failures"] += 1
            logger.error(f"Webhook {target.name} urllib fallback failed: {e}")

    async def _fire_callback(self, url: str, data: dict):
        """Fire a callback URL with result data."""
        target = WebhookTarget(name="callback", url=url, events=[])
        await self._fire_target(target, "callback", data)

    # ── Stats & Status ─────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get webhook statistics."""
        return {
            **self._stats,
            "targets": {
                name: {
                    "url": t.url,
                    "enabled": t.enabled,
                    "events": t.events,
                    "last_fired": t.last_fired,
                    "last_status": t.last_status,
                    "failures": t.failures,
                }
                for name, t in self.targets.items()
            }
        }

    def get_target_count(self) -> int:
        """Get number of active webhook targets."""
        return sum(1 for t in self.targets.values() if t.enabled)
