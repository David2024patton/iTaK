"""
iTaK Input Guard - inbound sensitive-data protection layer.

Applies the existing OutputGuard redaction engine to inbound user/API payloads
before they are persisted, logged, or forwarded deeper into the system.
"""

from __future__ import annotations

from typing import Any


def sanitize_inbound_text(text: str, output_guard: Any | None) -> str:
    """Sanitize inbound text using OutputGuard when available."""
    if not text:
        return text
    if not output_guard:
        return text

    try:
        result = output_guard.sanitize(text)
        return result.sanitized_text
    except Exception:
        return text


def sanitize_inbound_payload(value: Any, output_guard: Any | None) -> Any:
    """Recursively sanitize inbound payload values.

    Strings are sanitized through OutputGuard. Dict/list containers are
    traversed recursively. Non-string primitive values are returned unchanged.
    """
    if isinstance(value, str):
        return sanitize_inbound_text(value, output_guard)
    if isinstance(value, dict):
        return {
            key: sanitize_inbound_payload(val, output_guard)
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [sanitize_inbound_payload(item, output_guard) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_inbound_payload(item, output_guard) for item in value)
    return value
