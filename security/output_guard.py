"""
iTaK Output Guard - PII & Secret Redaction Layer

Sits between the agent's brain and the user. Every piece of text
goes through this before it leaves the system. Catches stuff like
SSNs, credit cards, phone numbers, addresses, API keys, passwords,
private keys, etc and redacts them.

This is basically a DLP (Data Loss Prevention) layer but for AI output.
Nothing gets past this without being scrubbed first.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PIICategory(str, Enum):
    """Categories of personally identifiable information."""
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    PHONE = "phone_number"
    EMAIL = "email"
    ADDRESS = "street_address"
    IP_ADDRESS = "ip_address"
    API_KEY = "api_key"
    PASSWORD = "password"
    PRIVATE_KEY = "private_key"
    AWS_KEY = "aws_key"
    JWT_TOKEN = "jwt_token"
    DISCORD_TOKEN = "discord_token"
    CRYPTO_KEY = "crypto_private_key"
    BANK_ACCOUNT = "bank_account"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    DOB = "date_of_birth"


@dataclass
class Redaction:
    """A single redaction that was applied."""
    category: PIICategory
    original_length: int
    position: int
    replacement: str


@dataclass
class GuardResult:
    """Result of running text through the output guard."""
    original_text: str
    sanitized_text: str
    redactions: list[Redaction] = field(default_factory=list)
    was_modified: bool = False

    @property
    def redaction_count(self) -> int:
        return len(self.redactions)

    @property
    def categories_found(self) -> list[str]:
        # Deduplicate categories while preserving order
        seen = set()
        result = []
        for r in self.redactions:
            cat = r.category.value
            if cat not in seen:
                seen.add(cat)
                result.append(cat)
        return result


class OutputGuard:
    """Output sanitization engine - scrubs PII and secrets from agent output.

    This runs on EVERY piece of text before it reaches the user.
    It uses regex patterns to detect sensitive data and replaces it
    with redacted placeholders like [SSN REDACTED] or [API KEY REDACTED].

    The guard operates in layers:
    1. Known secrets (from SecretManager) - exact match replacement
    2. Pattern-based PII detection - regex matching
    3. Custom patterns - user-defined rules
    """

    # --- Pattern definitions ---
    # Each tuple: (compiled_regex, category, replacement_text)

    PII_PATTERNS: list[tuple[re.Pattern, PIICategory, str]] = [
        # Social Security Numbers (XXX-XX-XXXX, XXXXXXXXX, XXX XX XXXX)
        (re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"), PIICategory.SSN, "[SSN REDACTED]"),

        # Credit card numbers (major formats with optional separators)
        (re.compile(
            r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))"
            r"[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{1,4}\b"
        ), PIICategory.CREDIT_CARD, "[CARD REDACTED]"),

        # Phone numbers (US formats - 10/11 digit with various separators)
        (re.compile(
            r"\b(?:\+?1[-.\s]?)?"
            r"(?:\(?\d{3}\)?[-.\s]?)"
            r"\d{3}[-.\s]?\d{4}\b"
        ), PIICategory.PHONE, "[PHONE REDACTED]"),

        # Email addresses
        (re.compile(
            r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
        ), PIICategory.EMAIL, "[EMAIL REDACTED]"),

        # US Street addresses (basic pattern - number + street name + type)
        (re.compile(
            r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,3}"
            r"(?:St(?:reet)?|Ave(?:nue)?|Blvd|Boulevard|Dr(?:ive)?|"
            r"Ln|Lane|Rd|Road|Ct|Court|Pl|Place|Way|Cir(?:cle)?|"
            r"Pkwy|Parkway|Ter(?:race)?|Trail|Trl)\b",
            re.IGNORECASE
        ), PIICategory.ADDRESS, "[ADDRESS REDACTED]"),

        # IP addresses (IPv4)
        (re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ), PIICategory.IP_ADDRESS, "[IP REDACTED]"),

        # Date of birth patterns (MM/DD/YYYY, MM-DD-YYYY, etc.)
        (re.compile(
            r"\b(?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])[-/]"
            r"(?:19|20)\d{2}\b"
        ), PIICategory.DOB, "[DOB REDACTED]"),
    ]

    SECRET_PATTERNS: list[tuple[re.Pattern, PIICategory, str]] = [
        # OpenAI API keys
        (re.compile(r"sk-[a-zA-Z0-9]{20,}"), PIICategory.API_KEY, "[API KEY REDACTED]"),

        # Anthropic API keys
        (re.compile(r"sk-ant-[a-zA-Z0-9_-]{20,}"), PIICategory.API_KEY, "[API KEY REDACTED]"),

        # Google API keys
        (re.compile(r"AIza[a-zA-Z0-9_-]{35}"), PIICategory.API_KEY, "[API KEY REDACTED]"),

        # GitHub tokens
        (re.compile(r"gh[ps]_[a-zA-Z0-9]{36,}"), PIICategory.API_KEY, "[GITHUB TOKEN REDACTED]"),

        # AWS access keys
        (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), PIICategory.AWS_KEY, "[AWS KEY REDACTED]"),

        # AWS secret keys (40 char base64)
        (re.compile(r"\b[A-Za-z0-9/+=]{40}\b"), PIICategory.AWS_KEY, None),  # Too many false positives alone

        # Discord bot tokens
        (re.compile(
            r"[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27,}"
        ), PIICategory.DISCORD_TOKEN, "[DISCORD TOKEN REDACTED]"),

        # JWT tokens
        (re.compile(
            r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b"
        ), PIICategory.JWT_TOKEN, "[JWT REDACTED]"),

        # Private keys (RSA, EC, etc.)
        (re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
            r"[\s\S]*?"
            r"-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
        ), PIICategory.PRIVATE_KEY, "[PRIVATE KEY REDACTED]"),

        # Ethereum/crypto private keys (64 hex chars)
        (re.compile(r"\b0x[a-fA-F0-9]{64}\b"), PIICategory.CRYPTO_KEY, "[CRYPTO KEY REDACTED]"),

        # Generic password in key=value format
        (re.compile(
            r"(?:password|passwd|pwd|pass)\s*[:=]\s*['\"]?([^\s'\"]{4,})['\"]?",
            re.IGNORECASE
        ), PIICategory.PASSWORD, "[PASSWORD REDACTED]"),

        # Generic secret/token/key in key=value format
        (re.compile(
            r"(?:secret|token|api_key|apikey|auth_token|access_token)"
            r"\s*[:=]\s*['\"]?([^\s'\"]{8,})['\"]?",
            re.IGNORECASE
        ), PIICategory.API_KEY, "[SECRET REDACTED]"),

        # Slack tokens
        (re.compile(r"xox[baprs]-[0-9a-zA-Z-]{10,}"), PIICategory.API_KEY, "[SLACK TOKEN REDACTED]"),

        # Telegram bot tokens
        (re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"), PIICategory.API_KEY, "[TELEGRAM TOKEN REDACTED]"),
    ]

    def __init__(self, config: dict | None = None, secret_manager=None):
        """Initialize the output guard.

        Args:
            config: Optional config dict with guard settings
            secret_manager: Optional SecretManager instance for known secret matching
        """
        self.config = config or {}
        self.secret_manager = secret_manager
        self.enabled = self.config.get("output_guard", {}).get("enabled", True)
        self.log_redactions = self.config.get("output_guard", {}).get("log_redactions", True)
        self.strict_mode = self.config.get("output_guard", {}).get("strict_mode", True)

        # Categories to skip (some users might want emails to pass through)
        skip_list = self.config.get("output_guard", {}).get("skip_categories", [])
        self.skip_categories = set(PIICategory(c) for c in skip_list if c in PIICategory.__members__.values())

        # Custom patterns added at runtime
        self.custom_patterns: list[tuple[re.Pattern, str, str]] = []

        # Stats
        self.total_scans = 0
        self.total_redactions = 0
        self.redaction_log: list[dict] = []

        logger.info(f"Output Guard initialized (enabled={self.enabled}, strict={self.strict_mode})")

    def add_custom_pattern(self, pattern: str, label: str, replacement: str | None = None):
        """Add a custom regex pattern to detect and redact.

        Args:
            pattern: Regex pattern string
            label: Human-readable label for the pattern
            replacement: Replacement text (defaults to [LABEL REDACTED])
        """
        replacement = replacement or f"[{label.upper()} REDACTED]"
        self.custom_patterns.append((re.compile(pattern), label, replacement))
        logger.info(f"Added custom output guard pattern: {label}")

    def sanitize(self, text: str) -> GuardResult:
        """Run text through all detection layers and return sanitized output.

        This is the main method - call this on every piece of output.

        Args:
            text: The raw text from the agent

        Returns:
            GuardResult with sanitized text and redaction details
        """
        if not self.enabled or not text:
            return GuardResult(original_text=text, sanitized_text=text)

        self.total_scans += 1
        redactions = []
        working_text = text

        # Layer 1: Known secrets from SecretManager (exact match)
        if self.secret_manager:
            working_text = self.secret_manager.mask_in_text(working_text)
            if working_text != text:
                redactions.append(Redaction(
                    category=PIICategory.API_KEY,
                    original_length=len(text) - len(working_text),
                    position=0,
                    replacement="[KNOWN SECRET MASKED]"
                ))

        # Layer 2: Secret patterns (API keys, tokens, passwords, private keys)
        for pattern, category, replacement in self.SECRET_PATTERNS:
            if category in self.skip_categories:
                continue
            if replacement is None:
                continue  # Skip patterns marked as too many false positives

            matches = list(pattern.finditer(working_text))
            for match in reversed(matches):  # Reverse to preserve positions
                redactions.append(Redaction(
                    category=category,
                    original_length=len(match.group()),
                    position=match.start(),
                    replacement=replacement
                ))
                working_text = (
                    working_text[:match.start()] +
                    replacement +
                    working_text[match.end():]
                )

        # Layer 3: PII patterns (SSN, credit cards, phone, email, address)
        for pattern, category, replacement in self.PII_PATTERNS:
            if category in self.skip_categories:
                continue

            matches = list(pattern.finditer(working_text))
            for match in reversed(matches):
                redactions.append(Redaction(
                    category=category,
                    original_length=len(match.group()),
                    position=match.start(),
                    replacement=replacement
                ))
                working_text = (
                    working_text[:match.start()] +
                    replacement +
                    working_text[match.end():]
                )

        # Layer 4: Custom patterns
        for pattern, label, replacement in self.custom_patterns:
            matches = list(pattern.finditer(working_text))
            for match in reversed(matches):
                redactions.append(Redaction(
                    category=PIICategory.PASSWORD,  # Generic category for custom
                    original_length=len(match.group()),
                    position=match.start(),
                    replacement=replacement
                ))
                working_text = (
                    working_text[:match.start()] +
                    replacement +
                    working_text[match.end():]
                )

        was_modified = working_text != text
        self.total_redactions += len(redactions)

        # Log redactions if enabled
        if was_modified and self.log_redactions:
            # Use set directly instead of list + set conversion
            categories = {r.category.value for r in redactions}
            log_entry = {
                "scan_number": self.total_scans,
                "redaction_count": len(redactions),
                "categories": list(categories),
            }
            self.redaction_log.append(log_entry)
            logger.warning(
                f"Output Guard redacted {len(redactions)} items: {list(categories)}"
            )

        return GuardResult(
            original_text=text,
            sanitized_text=working_text,
            redactions=redactions,
            was_modified=was_modified,
        )

    def get_stats(self) -> dict:
        """Return guard statistics."""
        return {
            "enabled": self.enabled,
            "strict_mode": self.strict_mode,
            "total_scans": self.total_scans,
            "total_redactions": self.total_redactions,
            "pattern_count": {
                "pii": len(self.PII_PATTERNS),
                "secrets": len(self.SECRET_PATTERNS),
                "custom": len(self.custom_patterns),
            },
            "skip_categories": [c.value for c in self.skip_categories],
            "recent_redactions": self.redaction_log[-10:],
        }
