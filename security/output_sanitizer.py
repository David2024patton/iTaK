"""
iTaK Output Guard - Strips local file paths and sensitive patterns from agent output.

Prevents leaking internal paths (screenshots, downloads, temp files) as visible
text in messages sent to users via adapters.
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Patterns that indicate local file paths that should be stripped
_PATH_PATTERNS = [
    # Windows absolute paths: C:\Users\...,  D:\folder\...
    re.compile(r'[A-Za-z]:\\(?:Users|home|tmp|temp|var|data|logs)\\[^\s"\'<>|]+', re.IGNORECASE),
    # Unix absolute paths: /home/..., /tmp/..., /var/...
    re.compile(r'/(?:home|tmp|temp|var|data|logs|Users)/[^\s"\'<>|]+', re.IGNORECASE),
    # MEDIA: prefix lines that reference local files
    re.compile(r'^MEDIA:\s*[A-Za-z]?:?[/\\].+$', re.MULTILINE),
    # file:// URIs
    re.compile(r'file:///[^\s"\'<>|]+', re.IGNORECASE),
]

# Sensitive patterns that should never appear in output
_SENSITIVE_PATTERNS = [
    # .env file contents
    re.compile(r'(?:^|\s)(?:API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE_KEY)\s*=\s*\S+', re.MULTILINE | re.IGNORECASE),
]


def strip_local_paths(text: str, replacement: str = "[local file]") -> str:
    """Strip local file system paths from text.

    Args:
        text: The text to sanitize.
        replacement: What to replace paths with.

    Returns:
        Text with local paths replaced.
    """
    result = text
    for pattern in _PATH_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def strip_sensitive(text: str) -> str:
    """Strip sensitive patterns (API keys, tokens) from text.

    Args:
        text: The text to sanitize.

    Returns:
        Text with sensitive values redacted.
    """
    result = text
    for pattern in _SENSITIVE_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


def sanitize_output(text: str, config: dict | None = None) -> str:
    """Full sanitization pipeline for agent output.

    Applies all stripping in order:
    1. Local file paths
    2. Sensitive patterns (API keys, tokens)
    3. MEDIA: lines with local paths

    Args:
        text: The raw agent output.
        config: Optional config dict for customization.

    Returns:
        Sanitized text safe for user-facing output.
    """
    if not text:
        return text

    config = config or {}

    # Strip local paths
    result = strip_local_paths(text)

    # Strip sensitive patterns
    result = strip_sensitive(result)

    # Strip empty MEDIA: lines that were partially cleaned
    result = re.sub(r'^MEDIA:\s*\[local file\]\s*$', '', result, flags=re.MULTILINE)

    # Collapse multiple blank lines left by stripping
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result.strip()
