#!/usr/bin/env python3
"""Container bootstrap for iTaK deploys (Dokploy/Coolify/etc)."""

from __future__ import annotations

import json
import secrets
from pathlib import Path


def ensure_dirs() -> None:
    for path in (
        Path("data"),
        Path("data/db"),
        Path("data/logs"),
        Path("data/media"),
    ):
        path.mkdir(parents=True, exist_ok=True)


def ensure_env_from_example() -> None:
    env_file = Path(".env")
    example = Path(".env.example")
    if not env_file.exists() and example.exists():
        env_file.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")


def ensure_config_from_example() -> None:
    config_file = Path("config.json")
    example = Path("install/config/config.json.example")
    if not config_file.exists() and example.exists():
        config_file.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")


def ensure_webui_auth_token() -> None:
    config_file = Path("config.json")
    if not config_file.exists():
        return

    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except Exception:
        return

    webui = data.get("webui")
    if not isinstance(webui, dict):
        webui = {}
        data["webui"] = webui

    current = str(webui.get("auth_token", "")).strip()
    if current:
        return

    webui["auth_token"] = secrets.token_hex(24)
    try:
        config_file.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")
    except Exception:
        return


def main() -> None:
    ensure_dirs()
    ensure_env_from_example()
    ensure_config_from_example()
    ensure_webui_auth_token()


if __name__ == "__main__":
    main()
