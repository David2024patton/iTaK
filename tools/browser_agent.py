"""
iTaK Browser Agent Tool - AI-driven browser via browser-use + Playwright.
Dedicated browser model handles vision, clicks, navigation.
"""

from tools.base import BaseTool, ToolResult


class BrowserAgentTool(BaseTool):
    """AI-driven browser automation using browser-use + Playwright.

    This is NOT raw Playwright. It's a full AI browser agent with its own
    dedicated LLM model (the 'browser' model from the 4-model architecture).

    The browser agent:
    - Sees the page via screenshots (vision model)
    - Reasons about what to click/type
    - Executes actions via Playwright Chromium
    - Reports results back to the main agent
    """

    name = "browser_agent"
    description = "Browse the web using an AI-powered browser agent."

    async def execute(
        self,
        task: str = "",
        url: str = "",
        **kwargs,
    ) -> ToolResult:
        """Send a task to the browser agent."""
        if not task:
            return ToolResult(output="Error: 'task' is required.", error=True)

        try:
            from browser_use import Agent as BrowserUseAgent
            from browser_use import BrowserSession, BrowserProfile
            from playwright.async_api import async_playwright

            # SSRF guard: validate the target URL before browsing
            if url:
                try:
                    from security.ssrf_guard import SSRFGuard
                    guard = SSRFGuard(self.agent.config)
                    safe, reason = guard.validate_url(url, source="browser_agent")
                    if not safe:
                        return ToolResult(
                            output=f"SSRF blocked: {reason}",
                            error=True,
                        )
                except ImportError:
                    pass  # Guard not available, proceed without check

            # Configure browser profile
            profile = BrowserProfile(
                headless=True,
                disable_security=True,
                accept_downloads=True,
                keep_alive=True,
            )

            session = BrowserSession(browser_profile=profile)

            # Combine URL with task if provided
            full_task = task
            if url:
                full_task = f"Navigate to {url} and then: {task}"

            # Create browser agent with dedicated browser model
            browser_config = self.agent.config.get("models", {}).get("browser", {})
            model_name = browser_config.get("model", "gemini/gemini-2.0-flash")

            import litellm

            browser_agent = BrowserUseAgent(
                task=full_task,
                browser_session=session,
                llm=litellm,
                use_vision=browser_config.get("use_vision", True),
            )

            # Run the browser agent
            result = await browser_agent.run()

            # Close session
            await session.close()

            return ToolResult(
                output=f"Browser task completed:\n{str(result)}"
            )

        except ImportError:
            return ToolResult(
                output=(
                    "browser-use is not installed. "
                    "Install with: pip install browser-use playwright && playwright install chromium"
                ),
                error=True,
            )
        except Exception as e:
            return ToolResult(output=f"Browser error: {e}", error=True)
