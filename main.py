"""
iTaK — Main Entry Point (v2)
Launch the agent with the specified adapter + optional WebUI.

Usage:
    python main.py                      # CLI adapter (default)
    python main.py --adapter cli        # CLI adapter
    python main.py --adapter discord    # Discord bot
    python main.py --adapter telegram   # Telegram bot
    python main.py --adapter slack      # Slack bot
    python main.py --webui              # Also start the WebUI dashboard
    python main.py --webui-only         # Only start WebUI (no adapter)
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))


def load_config() -> dict:
    """Load configuration from config.json."""
    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ config.json not found. Copy config.json.example and configure.")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_env():
    """Load environment variables from .env file if it exists."""
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def setup_logging(config: dict):
    """Configure Python logging."""
    level = config.get("logging", {}).get("level", "INFO")
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )


async def main(adapter_name: str = "cli", enable_webui: bool = False, webui_only: bool = False):
    """Initialize and run iTaK."""
    print("\n🧠 iTaK — Intelligent Task Automation Kernel v4")
    print("─" * 50)

    # Load configuration
    load_env()
    config = load_config()
    setup_logging(config)

    logger = logging.getLogger("itak")
    logger.info(f"Starting iTaK with adapter: {adapter_name}")

    # Import core
    from core.agent import Agent
    from core.logger import EventType

    # Initialize agent
    agent = Agent(config=config)

    # Async startup (connect stores, start heartbeat, MCP servers)
    await agent.startup()

    # Check for crash recovery
    if agent.checkpoint.has_checkpoint():
        age = agent.checkpoint.get_checkpoint_age()
        if age and age < 3600:  # Less than 1 hour old
            logger.info(f"Found checkpoint ({age:.0f}s old). Attempting restore...")
            restored = await agent.checkpoint.restore()
            if restored:
                logger.info("✅ Agent state restored from checkpoint")

    # Print subsystem status
    status = agent.get_subsystem_status()
    print(f"✅ Secret keys loaded: {len(agent.secrets.available_keys) if agent.secrets else 0}")
    print(f"✅ Memory layers: {'4-layer' if status['memory'] else 'none'}")
    print(f"✅ Security scanner: {'active' if status['security'] else 'disabled'}")
    print(f"✅ Rate limiter: {'active' if status['rate_limiter'] else 'disabled'}")
    print(f"✅ Heartbeat: {'active' if status['heartbeat'] else 'disabled'}")
    print(f"✅ Sub-agent manager: {'ready' if status['sub_agents'] else 'disabled'}")
    print(f"✅ Self-Heal Engine: {'active' if status['self_heal'] else 'disabled'}")
    print(f"✅ Mission Control: {'active' if status['task_board'] else 'disabled'}")
    print(f"✅ MCP Client: {'active' if status['mcp_client'] else 'disabled'}")
    print(f"✅ Code Quality Gate: {'active' if status['linter'] else 'disabled'}")
    print(f"✅ MCP Server: {'active' if status.get('mcp_server') else 'disabled'}")
    print(f"✅ Webhooks: {agent.webhooks.get_target_count() if agent.webhooks else 0} targets")
    print(f"✅ Swarm: {len(agent.swarm.profiles) if agent.swarm else 0} profiles")
    print(f"✅ User Registry: {len(agent.user_registry.users) if agent.user_registry else 0} users")
    print(f"✅ Presence: {'active' if status.get('presence') else 'disabled'}")
    print(f"✅ Media Pipeline: {'active' if status.get('media') else 'disabled'}")
    print(f"✅ Tools ({status['tools']}): {agent.get_tool_names()}")
    print(f"✅ Extensions: {status['extensions']} loaded")

    # Start WebUI if requested
    webui_task = None
    if enable_webui or webui_only:
        try:
            from webui.server import start_webui
            webui_port = config.get("webui", {}).get("port", 48920)
            webui_host = config.get("webui", {}).get("host", "0.0.0.0")
            webui_task = asyncio.create_task(start_webui(agent, host=webui_host, port=webui_port))
            print(f"✅ WebUI: http://{webui_host}:{webui_port}")
        except ImportError as e:
            logger.warning(f"WebUI not available: {e}")

    print("─" * 50)

    if webui_only:
        print("🌐 Running in WebUI-only mode.")
        agent.logger.log(EventType.SYSTEM, {"event": "startup", "mode": "webui-only"})
        if webui_task:
            await webui_task
        return

    # Load the adapter
    adapter = None
    adapter_config = config.get("adapters", {}).get(adapter_name, {})

    if adapter_name == "cli":
        from adapters.cli import CLIAdapter
        adapter = CLIAdapter(agent, adapter_config)
    elif adapter_name == "discord":
        from adapters.discord import DiscordAdapter
        adapter = DiscordAdapter(agent, adapter_config)
    elif adapter_name == "telegram":
        from adapters.telegram import TelegramAdapter
        adapter = TelegramAdapter(agent, adapter_config)
    elif adapter_name == "slack":
        from adapters.slack import SlackAdapter
        adapter = SlackAdapter(agent, adapter_config)
    else:
        logger.error(f"Unknown adapter: {adapter_name}")
        print(f"❌ Unknown adapter: {adapter_name}")
        print(f"   Available: cli, discord, telegram, slack")
        sys.exit(1)

    # Log startup
    agent.logger.log(
        EventType.SYSTEM,
        {
            "event": "startup",
            "adapter": adapter_name,
            "webui": enable_webui,
            "models": list(config.get("models", {}).keys()),
            "tools": agent.get_tool_names(),
        },
    )

    print(f"✅ Adapter: {adapter_name}")

    # Start the adapter (this blocks until stopped)
    try:
        await adapter.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Adapter error: {e}")
    finally:
        await adapter.stop()
        await agent.shutdown()
        agent.logger.log(EventType.SYSTEM, "iTaK shutdown")
        logger.info("iTaK shut down gracefully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="iTaK — Intelligent Task Automation Kernel")
    parser.add_argument(
        "--adapter",
        "-a",
        type=str,
        default="cli",
        choices=["cli", "discord", "telegram", "slack"],
        help="Communication adapter to use (default: cli)",
    )
    parser.add_argument(
        "--webui",
        action="store_true",
        help="Also start the WebUI monitoring dashboard",
    )
    parser.add_argument(
        "--webui-only",
        action="store_true",
        help="Only start WebUI (no adapter)",
    )
    args = parser.parse_args()

    # Windows event loop policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main(
        adapter_name=args.adapter,
        enable_webui=args.webui,
        webui_only=args.webui_only,
    ))
