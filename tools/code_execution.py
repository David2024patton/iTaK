"""
iTaK Code Execution Tool — Run Python, Node.js, or Shell commands.
Supports local execution and Docker sandbox.
"""

import asyncio
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from tools.base import BaseTool, ToolResult


class CodeExecutionTool(BaseTool):
    """Execute code in Python, Node.js, or Shell environments.

    Supports:
    - python: Execute Python code/scripts
    - nodejs: Execute JavaScript with Node.js
    - terminal: Execute shell commands (bash/PowerShell)

    Code runs locally by default. When sandbox_enabled=True in config,
    it runs inside a Docker container for safety.
    """

    name = "code_execution"
    description = "Execute code in Python, Node.js, or terminal."

    # Timeout cascade (from Agent Zero)
    DEFAULT_TIMEOUT = 60
    MAX_TIMEOUT = 300
    NO_OUTPUT_TIMEOUT = 30

    async def execute(
        self,
        runtime: str = "terminal",
        code: str = "",
        timeout: int | None = None,
        workdir: str | None = None,
        **kwargs,
    ) -> ToolResult:
        """Execute code in the specified runtime."""
        if not code:
            return ToolResult(output="Error: 'code' is required.", error=True)

        runtime = runtime.lower()
        if runtime not in ("python", "nodejs", "terminal"):
            return ToolResult(
                output=f"Error: Invalid runtime '{runtime}'. Use: python, nodejs, terminal",
                error=True,
            )

        timeout = timeout or self.DEFAULT_TIMEOUT
        timeout = min(timeout, self.MAX_TIMEOUT)

        # Check if sandbox is enabled
        sandbox = self.agent.config.get("security", {}).get("sandbox_enabled", False)

        try:
            if sandbox:
                result = await self._execute_sandbox(runtime, code, timeout, workdir)
            else:
                result = await self._execute_local(runtime, code, timeout, workdir)

            return result

        except asyncio.TimeoutError:
            return ToolResult(
                output=f"Execution timed out after {timeout} seconds.",
                error=True,
            )
        except Exception as e:
            return ToolResult(output=f"Execution error: {e}", error=True)

    async def _execute_local(
        self,
        runtime: str,
        code: str,
        timeout: int,
        workdir: str | None,
    ) -> ToolResult:
        """Execute code locally on the host machine."""
        # Build command
        if runtime == "python":
            cmd = ["python", "-c", code]
        elif runtime == "nodejs":
            cmd = ["node", "-e", code]
        elif runtime == "terminal":
            # Detect OS for shell
            if os.name == "nt":
                cmd = ["powershell", "-Command", code]
            else:
                cmd = ["bash", "-c", code]
        else:
            return ToolResult(output=f"Unknown runtime: {runtime}", error=True)

        # Set working directory
        cwd = workdir or str(Path.cwd())

        # Run the process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return ToolResult(
                output=f"Process killed after {timeout}s timeout.",
                error=True,
            )

        exit_code = process.returncode
        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()

        # Format output
        output_parts = []
        if stdout_text:
            output_parts.append(f"STDOUT:\n{stdout_text}")
        if stderr_text:
            output_parts.append(f"STDERR:\n{stderr_text}")
        if not output_parts:
            output_parts.append("(no output)")

        output = "\n\n".join(output_parts)
        output += f"\n\nExit code: {exit_code}"

        return ToolResult(
            output=output,
            error=exit_code != 0,
        )

    async def _execute_sandbox(
        self,
        runtime: str,
        code: str,
        timeout: int,
        workdir: str | None,
    ) -> ToolResult:
        """Execute code inside a Docker sandbox container."""
        sandbox_image = self.agent.config.get("docker", {}).get(
            "sandbox_image", "itak-sandbox:latest"
        )

        # Map runtime to Docker command
        if runtime == "python":
            docker_cmd = f'python -c "{code}"'
        elif runtime == "nodejs":
            docker_cmd = f'node -e "{code}"'
        elif runtime == "terminal":
            docker_cmd = code
        else:
            return ToolResult(output=f"Unknown runtime: {runtime}", error=True)

        # Build Docker run command
        cmd = [
            "docker", "run", "--rm",
            "--network=none",  # No network access by default
            "--memory=512m",   # Memory limit
            "--cpus=1",        # CPU limit
            f"--timeout={timeout}",
            sandbox_image,
            "bash", "-c", docker_cmd,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout + 10
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return ToolResult(output="Docker sandbox timed out.", error=True)

        exit_code = process.returncode
        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()

        output_parts = []
        if stdout_text:
            output_parts.append(f"STDOUT:\n{stdout_text}")
        if stderr_text:
            output_parts.append(f"STDERR:\n{stderr_text}")
        if not output_parts:
            output_parts.append("(no output)")

        output = "\n\n".join(output_parts)
        output += f"\n\n[Sandbox] Exit code: {exit_code}"

        return ToolResult(output=output, error=exit_code != 0)
