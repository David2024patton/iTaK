"""
iTaK SSRF Guard - Prevent Server-Side Request Forgery attacks.

Validates URLs before the agent makes HTTP requests, blocking:
- Private/internal IP ranges (127.x, 10.x, 172.16-31.x, 192.168.x)
- Loopback and link-local addresses
- Dangerous URL schemes (file://, ftp://, gopher://)
- Non-allowlisted hostnames (optional)

Inspired by OpenClaw's SSRF deny policy (Feb 2026 update).
"""

import ipaddress
import logging
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# Private/internal IP networks that should never be accessed by agent tools
DENIED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),         # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),      # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),     # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local
    ipaddress.ip_network("0.0.0.0/8"),          # "This" network
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),           # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),          # IPv6 link-local
]

# Schemes that should never be allowed
DENIED_SCHEMES = {"file", "ftp", "gopher", "data", "javascript", "vbscript"}

# Only these schemes are allowed
ALLOWED_SCHEMES = {"http", "https"}


class SSRFGuard:
    """Validates URLs to prevent SSRF attacks.

    Features:
    - Block requests to private/internal IPs
    - Block dangerous URL schemes
    - Optional hostname allowlist (restrict to known-good domains)
    - Audit logging for all blocked requests
    """

    def __init__(self, config: dict | None = None):
        config = config or {}
        security = config.get("security", {})

        # Optional allowlist - if set, ONLY these hostnames are allowed
        self.url_allowlist: list[str] = security.get("url_allowlist", [])

        # Additional denylist - these hostnames are always blocked
        self.url_denylist: list[str] = security.get("url_denylist", [])

        # Whether to block private IPs (default: True, disable for local dev only)
        self.block_private_ips: bool = security.get("block_private_ips", True)

        # Audit log
        self._blocked_count: int = 0
        self._blocked_log: list[dict] = []

    def validate_url(self, url: str, source: str = "unknown") -> tuple[bool, str]:
        """Validate a URL before fetching.

        Args:
            url: The URL to validate.
            source: Who requested this URL (for audit logging).

        Returns:
            (allowed: bool, reason: str)
        """
        try:
            parsed = urlparse(url)
        except Exception as e:
            self._log_blocked(url, source, f"Invalid URL: {e}")
            return False, f"Invalid URL: {e}"

        # 1. Scheme check
        scheme = (parsed.scheme or "").lower()
        if scheme in DENIED_SCHEMES:
            self._log_blocked(url, source, f"Blocked scheme: {scheme}://")
            return False, f"Blocked scheme: {scheme}://"

        if scheme not in ALLOWED_SCHEMES:
            self._log_blocked(url, source, f"Unknown scheme: {scheme}://")
            return False, f"Unknown scheme: {scheme}://"

        # 2. Hostname check
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            self._log_blocked(url, source, "No hostname in URL")
            return False, "No hostname in URL"

        # Check denylist
        for denied in self.url_denylist:
            if hostname == denied.lower() or hostname.endswith(f".{denied.lower()}"):
                self._log_blocked(url, source, f"Hostname in denylist: {hostname}")
                return False, f"Hostname blocked: {hostname}"

        # Check allowlist (if configured)
        if self.url_allowlist:
            allowed = False
            for permitted in self.url_allowlist:
                if hostname == permitted.lower() or hostname.endswith(f".{permitted.lower()}"):
                    allowed = True
                    break
            if not allowed:
                self._log_blocked(url, source, f"Hostname not in allowlist: {hostname}")
                return False, f"Hostname not in allowlist: {hostname}"

        # 3. IP resolution check (prevent DNS rebinding to private IPs)
        if self.block_private_ips:
            try:
                resolved_ips = socket.getaddrinfo(hostname, parsed.port or 443)
                for family, type_, proto, canonname, sockaddr in resolved_ips:
                    ip_str = sockaddr[0]
                    try:
                        ip = ipaddress.ip_address(ip_str)
                        for network in DENIED_NETWORKS:
                            if ip in network:
                                self._log_blocked(
                                    url, source,
                                    f"Resolves to private IP: {hostname} -> {ip_str} ({network})"
                                )
                                return False, f"URL resolves to private IP: {ip_str}"
                    except ValueError:
                        pass  # Invalid IP string, skip
            except socket.gaierror:
                # DNS resolution failed - hostname doesn't exist
                self._log_blocked(url, source, f"DNS resolution failed: {hostname}")
                return False, f"Cannot resolve hostname: {hostname}"

        return True, "OK"

    def _log_blocked(self, url: str, source: str, reason: str):
        """Log a blocked URL request for audit."""
        self._blocked_count += 1
        entry = {
            "url": url[:200],  # Truncate long URLs
            "source": source,
            "reason": reason,
        }
        self._blocked_log.append(entry)
        # Keep only last 100 entries
        if len(self._blocked_log) > 100:
            self._blocked_log = self._blocked_log[-100:]

        logger.warning(f"SSRF_BLOCKED [{source}] {reason} | URL: {url[:120]}")

    def get_stats(self) -> dict:
        """Get SSRF guard statistics."""
        return {
            "blocked_total": self._blocked_count,
            "recent_blocks": self._blocked_log[-10:],
            "allowlist_active": bool(self.url_allowlist),
            "allowlist_count": len(self.url_allowlist),
            "denylist_count": len(self.url_denylist),
            "block_private_ips": self.block_private_ips,
        }
