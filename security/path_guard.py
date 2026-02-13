"""
iTaK Path Guard - Prevent path traversal attacks.

Validates file paths to ensure they stay within allowed roots.
Blocks directory traversal (../), null bytes, and absolute paths
that escape the sandbox.

Inspired by OpenClaw's session path hardening (Feb 2026 update).
"""

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Characters that should never appear in path components
DANGEROUS_CHARS = re.compile(r"[\x00-\x1f\x7f]")  # Control characters including null

# Patterns that indicate traversal attempts
TRAVERSAL_PATTERNS = [
    "..",
    "~",
    "%2e%2e",       # URL-encoded ..
    "%252e%252e",   # Double-encoded ..
    "..%2f",        # Mixed encoding
    "%2f..",
    "..\\",
    "..%5c",
]


def validate_path(
    path: str,
    allowed_roots: list[str | Path] | None = None,
    allow_absolute: bool = False,
) -> tuple[bool, str]:
    """Validate a file path for safety.

    Args:
        path: The path to validate.
        allowed_roots: If set, the resolved path must be under one of these roots.
        allow_absolute: If False, reject absolute paths entirely.

    Returns:
        (safe: bool, reason: str)
    """
    if not path or not path.strip():
        return False, "Empty path"

    # 1. Check for null bytes (classic attack vector)
    if "\x00" in path:
        logger.warning(f"PATH_TRAVERSAL null byte in path: {path!r}")
        return False, "Null byte in path"

    # 2. Check for control characters
    if DANGEROUS_CHARS.search(path):
        logger.warning(f"PATH_TRAVERSAL control character in path: {path!r}")
        return False, "Control character in path"

    # 3. Check for traversal patterns (case-insensitive)
    path_lower = path.lower()
    for pattern in TRAVERSAL_PATTERNS:
        if pattern in path_lower:
            logger.warning(f"PATH_TRAVERSAL pattern '{pattern}' in path: {path}")
            return False, f"Path traversal detected: contains '{pattern}'"

    # 4. Check absolute paths
    if not allow_absolute:
        if os.path.isabs(path):
            logger.warning(f"PATH_TRAVERSAL absolute path rejected: {path}")
            return False, "Absolute paths not allowed"

    # 5. Resolve and check against allowed roots
    if allowed_roots:
        try:
            resolved = Path(path).resolve()
            in_root = False
            for root in allowed_roots:
                root_resolved = Path(root).resolve()
                try:
                    resolved.relative_to(root_resolved)
                    in_root = True
                    break
                except ValueError:
                    continue

            if not in_root:
                root_list = ", ".join(str(r) for r in allowed_roots)
                logger.warning(
                    f"PATH_TRAVERSAL path escapes allowed roots: {path} "
                    f"(resolved: {resolved}, roots: {root_list})"
                )
                return False, f"Path escapes allowed directory"
        except (OSError, RuntimeError) as e:
            return False, f"Cannot resolve path: {e}"

    return True, "OK"


def validate_session_id(session_id: str) -> tuple[bool, str]:
    """Validate a session ID for use as a directory/file name.

    Session IDs must be alphanumeric with hyphens/underscores only.
    No path separators, no dots, no special characters.
    """
    if not session_id or not session_id.strip():
        return False, "Empty session ID"

    # Only allow safe characters
    if not re.match(r"^[a-zA-Z0-9_-]+$", session_id):
        logger.warning(f"PATH_TRAVERSAL unsafe session ID: {session_id!r}")
        return False, "Session ID contains unsafe characters"

    # Length limit
    if len(session_id) > 128:
        return False, "Session ID too long (max 128 chars)"

    return True, "OK"


def safe_join(root: str | Path, *parts: str) -> Path | None:
    """Safely join path components, ensuring result stays under root.

    Returns None if the result would escape the root directory.
    """
    root_path = Path(root).resolve()

    for part in parts:
        safe, reason = validate_path(part, allowed_roots=None, allow_absolute=False)
        if not safe:
            logger.warning(f"PATH_GUARD safe_join rejected component: {part} ({reason})")
            return None

    joined = root_path.joinpath(*parts).resolve()

    try:
        joined.relative_to(root_path)
        return joined
    except ValueError:
        logger.warning(f"PATH_GUARD safe_join escaped root: {joined} not under {root_path}")
        return None
