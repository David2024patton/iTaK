"""
iTaK GogCLI Tool - Run gogcli (gog) commands safely.
"""

import asyncio
import shlex
from tools.base import BaseTool, ToolResult


class GogcliTool(BaseTool):
    """Execute gogcli commands through the `gog` binary.

    This provides iTaK integration with gogcli by executing the external CLI
    in non-interactive mode and returning stdout/stderr to the agent.
    """

    name = "gogcli_tool"
    description = "Run gogcli (gog) commands for Google Workspace operations."

    async def execute(
        self,
        action: str = "run",
        command: str = "",
        json_output: bool = True,
        no_input: bool = True,
        account: str = "",
        client: str = "",
        timeout: int = 60,
        **kwargs,
    ) -> ToolResult:
        """Execute gogcli commands.

        Args:
            action: One of run, help, version.
            command: gog subcommand string for action=run (without leading `gog`).
            json_output: Add --json for machine-parseable output.
            no_input: Add --no-input to avoid interactive prompts.
            account: Optional GOG_ACCOUNT override.
            client: Optional GOG_CLIENT override.
            timeout: Command timeout in seconds.
        """
        cfg = self.agent.config.get("gogcli", {})
        binary = cfg.get("binary", "gog")
        default_timeout = int(cfg.get("timeout_seconds", 60))
        effective_timeout = max(1, int(timeout or default_timeout))

        if action not in {"run", "help", "version"}:
            return ToolResult(
                output="Unknown action. Supported: run, help, version",
                error=True,
            )

        if action == "help":
            argv = [binary, "--help"]
        elif action == "version":
            argv = [binary, "version"]
        else:
            if not command.strip():
                return ToolResult(
                    output="Error: 'command' is required when action='run'.",
                    error=True,
                )
            try:
                parsed = shlex.split(command)
            except ValueError as exc:
                return ToolResult(output=f"Invalid command syntax: {exc}", error=True)

            argv = [binary] + parsed
            if json_output and "--json" not in parsed:
                argv.append("--json")
            if no_input and "--no-input" not in parsed:
                argv.append("--no-input")

        env = None
        if account or client:
            import os

            env = os.environ.copy()
            if account:
                env["GOG_ACCOUNT"] = account
            if client:
                env["GOG_CLIENT"] = client

        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=effective_timeout
            )

            stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr = stderr_bytes.decode("utf-8", errors="replace").strip()

            if process.returncode != 0:
                details = stderr or stdout or "No output"
                return ToolResult(
                    output=f"gog command failed (exit {process.returncode}):\n{details}",
                    error=True,
                )

            if stdout:
                if stderr:
                    return ToolResult(output=f"{stdout}\n\n[stderr]\n{stderr}")
                return ToolResult(output=stdout)

            if stderr:
                return ToolResult(output=f"Command completed with stderr:\n{stderr}")

            return ToolResult(output="gog command completed successfully.")

        except FileNotFoundError:
            return ToolResult(
                output=(
                    f"gog binary not found: '{binary}'. Install gogcli or set "
                    "config.gogcli.binary to the full executable path."
                ),
                error=True,
            )
        except asyncio.TimeoutError:
            return ToolResult(
                output=f"gog command timed out after {effective_timeout} seconds.",
                error=True,
            )
        except Exception as exc:
            return ToolResult(output=f"gog execution error: {exc}", error=True)
