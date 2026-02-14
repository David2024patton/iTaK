"""
iTaK Helpers - Utility functions used across the codebase.
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any

# ============================================================
# Text Utilities
# ============================================================

def truncate(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """Truncate text to max_length, appending suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_json(text: str) -> dict | list | None:
    """Extract JSON from text, even if wrapped in markdown code blocks.
    
    Uses dirtyjson to handle malformed JSON gracefully.
    """
    # Try to find JSON in code blocks
    patterns = [
        r"```json\s*\n(.*?)\n```",
        r"```\s*\n(.*?)\n```",
        r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                # Try dirtyjson first for better handling of malformed JSON
                try:
                    import dirtyjson
                    return dirtyjson.loads(match.group(1) if match.lastindex else match.group(0))
                except Exception:
                    return json.loads(match.group(1) if match.lastindex else match.group(0))
            except (json.JSONDecodeError, IndexError):
                continue

    # Try parsing the entire text
    try:
        # Try dirtyjson first for better handling of malformed JSON
        try:
            import dirtyjson
            return dirtyjson.loads(text)
        except Exception:
            return json.loads(text)
    except json.JSONDecodeError:
        return None


def clean_markdown(text: str) -> str:
    """Remove markdown formatting to get plain text."""
    text = re.sub(r"#+\s*", "", text)  # Headers
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Bold
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # Italic
    text = re.sub(r"`(.*?)`", r"\1", text)  # Inline code
    text = re.sub(r"```[\s\S]*?```", "", text)  # Code blocks
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # Links
    text = re.sub(r"^[>\-*] ", "", text, flags=re.MULTILINE)  # Lists/quotes
    return text.strip()


# ============================================================
# Hashing / Dedup
# ============================================================

def content_hash(text: str) -> str:
    """Generate a short hash for deduplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def is_duplicate(text: str, existing_hashes: set, threshold_length: int = 50) -> bool:
    """Check if text is a duplicate of something we've seen."""
    if len(text) < threshold_length:
        return text.strip() in existing_hashes
    return content_hash(text) in existing_hashes


# ============================================================
# File Utilities
# ============================================================

def safe_read(filepath: str | Path, encoding: str = "utf-8") -> str:
    """Read a file safely, returning empty string on error."""
    try:
        return Path(filepath).read_text(encoding=encoding)
    except Exception:
        return ""


def safe_write(filepath: str | Path, content: str, encoding: str = "utf-8"):
    """Write to a file safely, creating directories as needed."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding=encoding)


def atomic_write(filepath: str | Path, content: str, encoding: str = "utf-8"):
    """Atomic write: write to .tmp file then rename (crash safe)."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = filepath.with_suffix(filepath.suffix + ".tmp")
    tmp_path.write_text(content, encoding=encoding)
    tmp_path.replace(filepath)


# ============================================================
# Timing Utilities
# ============================================================

def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    return f"{hrs}h {mins}m"


class Timer:
    """Context manager for timing operations."""

    def __init__(self, label: str = ""):
        self.label = label
        self.elapsed = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self._start

    def __str__(self):
        return f"{self.label}: {format_duration(self.elapsed)}" if self.label else format_duration(self.elapsed)


# ============================================================
# Token Estimation
# ============================================================

def estimate_tokens(text: str) -> int:
    """Rough token count estimation (4 chars ≈ 1 token)."""
    return len(text) // 4


def estimate_cost(tokens: int, model: str = "gpt-4o-mini") -> float:
    """Estimate API cost based on token count and model."""
    # Approximate $/1K tokens (input)
    costs = {
        "gpt-4o": 0.005,
        "gpt-4o-mini": 0.00015,
        "gpt-4-turbo": 0.01,
        "claude-3-5-sonnet": 0.003,
        "claude-3-haiku": 0.00025,
        "gemini-2.0-flash": 0.0001,
        "deepseek-chat": 0.0007,
    }
    rate = costs.get(model, 0.001)
    return (tokens / 1000) * rate
