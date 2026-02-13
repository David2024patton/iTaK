"""
iTaK CLI Adapter - Terminal interface with spinner progress.
"""

import asyncio
import sys

from adapters.base import BaseAdapter


class CLIAdapter(BaseAdapter):
    """Terminal-based adapter for local development and testing.

    Features:
    - Simple input/output loop
    - Spinner progress indicator
    - Colored output (ANSI)
    - Type 'quit' or 'exit' to stop
    """

    name = "cli"

    def __init__(self, agent, config: dict):
        super().__init__(agent, config)
        self._spinner_task = None

    async def start(self):
        """Start the CLI input loop."""
        self._running = True
        self.agent.context.room_id = "cli-local"
        self.agent.context.adapter_name = "cli"

        print("\n" + "="*60)
        print("  🧠 iTaK - Intelligent Task Automation Kernel")
        print("  Type your message. 'quit' to exit.")
        print("="*60 + "\n")

        while self._running:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("\033[96m You:\033[0m ")
                )
            except (EOFError, KeyboardInterrupt):
                break

            if user_input.lower() in ("quit", "exit", "q"):
                print("\n👋 iTaK shutting down.")
                break

            if not user_input.strip():
                continue

            # Handle the message
            print()
            await self.handle_message(user_id="owner", content=user_input)
            print()

    async def send_message(self, content: str, **kwargs):
        """Print a message to the terminal."""
        # Format with ANSI colors
        print(f"\033[93m iTaK:\033[0m {content}")

    async def _on_progress(self, event_type: str, data: dict):
        """Handle progress events with terminal formatting."""
        if event_type == "plan":
            text = data.get("text", "")
            print(f"\033[90m  📋 {text}\033[0m")
        elif event_type == "progress":
            step = data.get("step", 0)
            message = data.get("message", "")
            print(f"\033[90m  ⚙️  Step {step}: {message}\033[0m")
        elif event_type == "complete":
            elapsed = data.get("elapsed_seconds", 0)
            print(f"\033[90m  ✅ Done ({elapsed:.1f}s)\033[0m")
        elif event_type == "error":
            message = data.get("message", "")
            print(f"\033[91m  ❌ {message}\033[0m")

    async def stop(self):
        self._running = False
