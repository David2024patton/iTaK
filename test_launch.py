#!/usr/bin/env python3
"""
Test script to verify iTaK can initialize without actually running.
"""
import sys
import asyncio
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

async def test_launch():
    """Test that iTaK can initialize."""
    print("\n🧪 Testing iTaK Launch...")
    print("=" * 50)

    # Load environment and config
    from main import load_env, load_config, setup_logging

    load_env()
    config = load_config()
    setup_logging(config)

    print("✅ Configuration loaded")

    # Test imports
    try:
        from core.agent import Agent
        print("✅ Core agent module imports successfully")
    except Exception as e:
        print(f"❌ Failed to import Agent: {e}")
        return False

    try:
        from core.logger import EventType
        print("✅ Logger module imports successfully")
    except Exception as e:
        print(f"❌ Failed to import Logger: {e}")
        return False

    # Try to initialize agent (but don't start it)
    try:
        agent = Agent(config=config)
        print("✅ Agent instance created")
    except Exception as e:
        print(f"❌ Failed to create Agent: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Try async startup (this might fail without API keys but let's see)
    try:
        await agent.startup()
        print("✅ Agent startup completed")

        # Get subsystem status
        status = agent.get_subsystem_status()
        print("\n📊 Subsystem Status:")
        print(f"  - Memory: {status['memory']}")
        print(f"  - Security: {status['security']}")
        print(f"  - Rate Limiter: {status['rate_limiter']}")
        print(f"  - Heartbeat: {status['heartbeat']}")
        print(f"  - Sub-agents: {status['sub_agents']}")
        print(f"  - Self-Heal: {status['self_heal']}")
        print(f"  - Task Board: {status['task_board']}")
        print(f"  - MCP Client: {status['mcp_client']}")
        print(f"  - Linter: {status['linter']}")
        print(f"  - Tools: {status['tools']}")
        print(f"  - Extensions: {status['extensions']}")

        # Test adapter imports
        from adapters.cli import CLIAdapter
        print("\n✅ CLI adapter imports successfully")

        # Clean shutdown
        await agent.shutdown()
        print("\n✅ Agent shutdown completed")

        return True

    except Exception as e:
        print(f"⚠️  Agent startup issue: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    result = asyncio.run(test_launch())

    print("\n" + "=" * 50)
    if result:
        print("✅ LAUNCH TEST PASSED - iTaK can initialize successfully")
    else:
        print("⚠️  LAUNCH TEST COMPLETED WITH WARNINGS")
    print("=" * 50)

    sys.exit(0 if result else 1)
