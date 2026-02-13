"""
iTaK Secret Manager - Two-store secrets with placeholder replacement.
Loads from .env and config.json, replaces {{placeholders}} in prompts/code.
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SecretManager:
    """Two-store secret management system from Agent Zero's pattern.

    Store 1: .env file (actual values, never committed)
    Store 2: config.json (placeholder references like "$ENV_VAR")

    The placeholder syntax `{{secret_name}}` in prompts and code
    gets replaced with the actual value at runtime. This ensures
    secrets are never hardcoded anywhere.
    """

    PLACEHOLDER_PATTERN = re.compile(r"\{\{(\w+)\}\}")

    def __init__(self, env_file: str = ".env"):
        self._secrets: dict[str, str] = {}
        self._env_file = Path(env_file)
        self._load_env()
        self._load_os_env()

    def _load_env(self):
        """Load secrets from .env file."""
        if not self._env_file.exists():
            logger.warning(f".env file not found at {self._env_file}")
            return

        for line in self._env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if value:
                    self._secrets[key] = value

        logger.info(f"Loaded {len(self._secrets)} secrets from .env")

    def _load_os_env(self):
        """Load additional secrets from OS environment (Docker, etc)."""
        env_keys = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
            "OPENROUTER_API_KEY", "GROQ_API_KEY",
            "DISCORD_TOKEN", "TELEGRAM_TOKEN", "SLACK_TOKEN", "SLACK_APP_TOKEN",
            "NEO4J_PASSWORD", "WEAVIATE_API_KEY",
        ]
        for key in env_keys:
            val = os.environ.get(key)
            if val and key not in self._secrets:
                self._secrets[key] = val

    def get(self, key: str, default: str = "") -> str:
        """Get a secret value by key."""
        return self._secrets.get(key, os.environ.get(key, default))

    def resolve_config_value(self, value: str) -> str:
        """Resolve a config value that may reference an env var.

        In config.json, values like "$OPENAI_API_KEY" reference
        environment variables. This method resolves them.
        """
        if isinstance(value, str) and value.startswith("$"):
            env_key = value[1:]
            return self.get(env_key, value)
        return value

    def replace_placeholders(self, text: str) -> str:
        """Replace {{placeholder}} patterns with actual secret values.

        Used in prompt templates and code before sending to LLM.
        Unresolved placeholders are left as-is (safer than exposing errors).
        """
        def replacer(match):
            key = match.group(1)
            value = self.get(key)
            if value:
                return value
            logger.warning(f"Unresolved placeholder: {{{{{key}}}}}")
            return match.group(0)  # Leave as-is

        return self.PLACEHOLDER_PATTERN.sub(replacer, text)

    def mask_in_text(self, text: str) -> str:
        """Mask all known secrets in a text string (for logging)."""
        for key, value in self._secrets.items():
            if value and len(value) > 3 and value in text:
                masked = value[:3] + "***" + (value[-2:] if len(value) > 5 else "")
                text = text.replace(value, masked)
        return text

    def register_with_logger(self, itak_logger):
        """Register all secrets with the iTaK logger for masking."""
        for key, value in self._secrets.items():
            if value and len(value) > 3:
                itak_logger.register_secret(value)

    @property
    def available_keys(self) -> list[str]:
        """List available secret key names (not values!)."""
        return list(self._secrets.keys())

    def has(self, key: str) -> bool:
        """Check if a secret is available."""
        return key in self._secrets or key in os.environ
