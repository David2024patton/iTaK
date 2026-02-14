#!/usr/bin/env python3
"""
Test script to verify iTaK WebUI can initialize.
"""
import sys
import asyncio
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

async def test_webui_launch():
    """Test that iTaK WebUI can initialize."""
    print("\n🧪 Testing iTaK WebUI Launch...")
    print("=" * 50)

    # Load environment and config
    from main import load_env, load_config, setup_logging

    load_env()
    config = load_config()
    setup_logging(config)

    print("✅ Configuration loaded")

    # Initialize agent
    from core.agent import Agent
    agent = Agent(config=config)
    await agent.startup()
    print("✅ Agent initialized")

    # Test WebUI import
    try:
        from webui.server import start_webui
        print("✅ WebUI server module imports successfully")
    except Exception as e:
        print(f"❌ Failed to import WebUI: {e}")
        await agent.shutdown()
        return False

    # Try to start WebUI briefly (just to test initialization)
    try:
        # We'll start it and immediately cancel to test initialization
        webui_task = asyncio.create_task(start_webui(agent, host="127.0.0.1", port=48920))
        print("✅ WebUI server task created")

        # Give it a moment to initialize
        await asyncio.sleep(2)

        # Cancel the task
        webui_task.cancel()
        try:
            await webui_task
        except asyncio.CancelledError:
            print("✅ WebUI server task cancelled cleanly")

        # Clean shutdown
        await agent.shutdown()
        print("✅ Agent shutdown completed")

        return True

    except Exception as e:
        print(f"⚠️  WebUI startup issue: {e}")
        import traceback
        traceback.print_exc()
        await agent.shutdown()
        return False

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    result = asyncio.run(test_webui_launch())

    print("\n" + "=" * 50)
    if result:
        print("✅ WEBUI LAUNCH TEST PASSED")
    else:
        print("⚠️  WEBUI LAUNCH TEST COMPLETED WITH WARNINGS")
    print("=" * 50)

    sys.exit(0 if result else 1)
