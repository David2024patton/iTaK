"""
iTaK MemU Store Adapter - Extraction-only enrichment pipeline.
Self-hosted by default, cloud API opt-in.

This adapter handles fire-and-forget ingestion to MemU for fact extraction.
MemU is NOT used as a search layer - extracted facts are routed to existing stores.
"""

import asyncio
import hashlib
import json
import logging
import time

import aiohttp

logger = logging.getLogger(__name__)


class MemUStore:
    """Adapter for MemU self-hosted enrichment pipeline.
    
    Key behaviors:
    - Self-hosted by default (memu-server sidecar)
    - Cloud API is opt-in via mode="cloud"
    - Extraction-only: memorize() for ingestion, NO retrieval
    - Async fire-and-forget with timeout controls
    - Throttling: min length, dedup window, cost cap, opt-out flag
    """

    def __init__(self, config: dict):
        """Initialize MemU adapter.
        
        Args:
            config: MemU config dict with keys:
                - enabled (bool): Enable MemU integration (default: False)
                - mode (str): "self-hosted" or "cloud" (default: "self-hosted")
                - base_url (str): MemU server URL (default: "http://localhost:8080")
                - api_key (str): Optional API key for cloud mode
                - timeout (int): Request timeout in seconds (default: 30)
                - memorize_endpoint (str): Custom memorize path (default: "/memory/memorize")
                - min_conversation_length (int): Min chars to process (default: 100)
                - dedup_window_minutes (int): Skip if similar within N minutes (default: 15)
                - cost_cap_per_hour (float): Max USD cost per hour (default: 1.0)
                - max_turns (int): Number of turns to send (default: 5)
                - memu_weight (float): Weight for memu-extracted items (default: 0.8)
        """
        self.config = config
        self.enabled = config.get("enabled", False)
        self.mode = config.get("mode", "self-hosted")
        self.base_url = config.get("base_url", "http://localhost:8080").rstrip("/")
        self.api_key = config.get("api_key", "")
        self.timeout = config.get("timeout", 30)
        self.memorize_endpoint = config.get("memorize_endpoint", "/memory/memorize")
        
        # Throttling settings
        self.min_conversation_length = config.get("min_conversation_length", 100)
        self.dedup_window_minutes = config.get("dedup_window_minutes", 15)
        self.cost_cap_per_hour = config.get("cost_cap_per_hour", 1.0)
        self.max_turns = config.get("max_turns", 5)
        self.memu_weight = config.get("memu_weight", 0.8)
        
        # Internal state for throttling
        self._dedup_cache = {}  # hash -> timestamp
        self._hourly_costs = []  # (timestamp, cost) tuples
        
        logger.info(
            f"MemU adapter initialized: enabled={self.enabled}, mode={self.mode}, "
            f"base_url={self.base_url}"
        )

    def _check_opt_out(self, messages: list[dict]) -> bool:
        """Check if conversation has opt-out flag (#no-memory)."""
        for msg in messages[-3:]:  # Check last 3 messages
            content = msg.get("content", "")
            if isinstance(content, str) and "#no-memory" in content.lower():
                logger.info("MemU: opt-out flag detected (#no-memory)")
                return True
        return False

    def _check_min_length(self, messages: list[dict]) -> bool:
        """Check if conversation meets minimum length threshold."""
        total_chars = sum(len(str(m.get("content", ""))) for m in messages)
        if total_chars < self.min_conversation_length:
            logger.debug(
                f"MemU: skipping - conversation too short ({total_chars} < "
                f"{self.min_conversation_length} chars)"
            )
            return False
        return True

    def _check_dedup(self, messages: list[dict]) -> bool:
        """Check deduplication window - skip if similar content recently processed."""
        # Create hash of conversation content
        content = json.dumps([m.get("content", "") for m in messages], sort_keys=True)
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        now = time.time()
        
        # Clean old entries
        cutoff = now - (self.dedup_window_minutes * 60)
        self._dedup_cache = {
            h: t for h, t in self._dedup_cache.items() if t > cutoff
        }
        
        # Check if recently processed
        if content_hash in self._dedup_cache:
            age_minutes = (now - self._dedup_cache[content_hash]) / 60
            logger.debug(
                f"MemU: skipping - similar conversation processed {age_minutes:.1f} "
                f"minutes ago (within {self.dedup_window_minutes} minute window)"
            )
            return False
        
        # Record this conversation
        self._dedup_cache[content_hash] = now
        return True

    def _check_cost_cap(self, estimated_cost: float = 0.01) -> bool:
        """Check if hourly cost cap would be exceeded."""
        now = time.time()
        hour_ago = now - 3600
        
        # Clean old entries
        self._hourly_costs = [(t, c) for t, c in self._hourly_costs if t > hour_ago]
        
        # Calculate current hourly cost
        current_cost = sum(c for _, c in self._hourly_costs)
        
        if current_cost + estimated_cost > self.cost_cap_per_hour:
            logger.warning(
                f"MemU: skipping - cost cap reached (${current_cost:.4f} + "
                f"${estimated_cost:.4f} > ${self.cost_cap_per_hour})"
            )
            return False
        
        # Record this cost
        self._hourly_costs.append((now, estimated_cost))
        return True

    async def memorize(
        self,
        messages: list[dict],
        metadata: dict | None = None,
        skip_throttle: bool = False,
    ) -> dict | None:
        """Send conversation to MemU for fact extraction (fire-and-forget).
        
        Args:
            messages: List of message dicts (role, content)
            metadata: Optional metadata to include
            skip_throttle: Skip throttling checks (for testing)
            
        Returns:
            dict: MemU response with extracted facts, or None if throttled/failed
        """
        if not self.enabled:
            logger.debug("MemU: disabled in config")
            return None
        
        # Throttling checks
        if not skip_throttle:
            if self._check_opt_out(messages):
                return None
            if not self._check_min_length(messages):
                return None
            if not self._check_dedup(messages):
                return None
            if not self._check_cost_cap():
                return None
        
        # Prepare request
        url = f"{self.base_url}{self.memorize_endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Take last N turns
        recent_messages = messages[-self.max_turns:] if len(messages) > self.max_turns else messages
        
        payload = {
            "messages": recent_messages,
            "metadata": metadata or {},
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(
                            f"MemU: successfully memorized {len(recent_messages)} turns"
                        )
                        return result
                    else:
                        error_text = await response.text()
                        logger.warning(
                            f"MemU: memorize failed with status {response.status}: "
                            f"{error_text[:200]}"
                        )
                        return None
        except asyncio.TimeoutError:
            logger.warning(f"MemU: memorize timeout after {self.timeout}s")
            return None
        except aiohttp.ClientError as e:
            logger.warning(f"MemU: memorize client error: {e}")
            return None
        except Exception as e:
            logger.error(f"MemU: memorize unexpected error: {e}")
            return None

    def get_memu_weight(self) -> float:
        """Get configured weight for MemU-extracted items."""
        return self.memu_weight
