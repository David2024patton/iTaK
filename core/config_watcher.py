"""
iTaK Config Watcher - Hot-reload config.json on meaningful changes.

Watches config.json for modifications and reloads when substantive values change.
Ignores meta-only changes (whitespace, comments, formatting) to avoid unnecessary restarts.
"""

import hashlib
import json
import logging
import os
import time
import threading
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Fields to ignore during change comparison (meta / cosmetic)
META_FIELDS = {"_comment", "_comments", "meta", "_meta", "$schema", "version"}


def _normalize_config(config: dict) -> dict:
    """Remove meta-only fields and produce a canonical representation.

    This ensures that cosmetic changes (comments, formatting) don't
    trigger a reload.
    """
    if not isinstance(config, dict):
        return config

    normalized = {}
    for key, value in sorted(config.items()):
        if key in META_FIELDS:
            continue
        if isinstance(value, dict):
            normalized[key] = _normalize_config(value)
        elif isinstance(value, list):
            normalized[key] = [
                _normalize_config(v) if isinstance(v, dict) else v
                for v in value
            ]
        else:
            normalized[key] = value
    return normalized


def _config_hash(config: dict) -> str:
    """Produce a stable hash of the meaningful config content."""
    normalized = _normalize_config(config)
    canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class ConfigWatcher:
    """Watch config.json and trigger callback on meaningful changes.

    Usage:
        def on_config_change(new_config):
            agent.reload_config(new_config)

        watcher = ConfigWatcher("config.json", on_config_change)
        watcher.start()
        ...
        watcher.stop()
    """

    def __init__(
        self,
        config_path: str | Path = "config.json",
        on_change: Optional[Callable[[dict], None]] = None,
        poll_interval: float = 5.0,
    ):
        self._path = Path(config_path)
        self._on_change = on_change
        self._poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_hash: str = ""
        self._last_mtime: float = 0

        # Initialize with current config hash
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self._last_hash = _config_hash(config)
                self._last_mtime = self._path.stat().st_mtime
            except Exception:
                pass

    def start(self):
        """Start watching in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop,
            name="config-watcher",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"Config watcher started: {self._path}")

    def stop(self):
        """Stop watching."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._poll_interval + 1)

    def _poll_loop(self):
        """Poll for config changes."""
        while self._running:
            try:
                time.sleep(self._poll_interval)
                if not self._path.exists():
                    continue

                # Quick check: did the file modification time change?
                mtime = self._path.stat().st_mtime
                if mtime == self._last_mtime:
                    continue

                self._last_mtime = mtime

                # Read and hash the config
                with open(self._path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                new_hash = _config_hash(config)
                if new_hash == self._last_hash:
                    logger.debug("Config file changed but content is equivalent (meta-only)")
                    continue

                # Meaningful change detected
                logger.info(f"Config change detected (hash: {self._last_hash[:8]}→{new_hash[:8]})")
                self._last_hash = new_hash

                if self._on_change:
                    try:
                        self._on_change(config)
                    except Exception as e:
                        logger.error(f"Config reload callback failed: {e}")

            except json.JSONDecodeError as e:
                logger.warning(f"Config file has invalid JSON, skipping: {e}")
            except Exception as e:
                logger.error(f"Config watcher error: {e}")

    def check_now(self) -> bool:
        """Manually trigger a config check. Returns True if config changed."""
        if not self._path.exists():
            return False

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                config = json.load(f)
            new_hash = _config_hash(config)
            if new_hash != self._last_hash:
                self._last_hash = new_hash
                if self._on_change:
                    self._on_change(config)
                return True
        except Exception:
            pass
        return False
