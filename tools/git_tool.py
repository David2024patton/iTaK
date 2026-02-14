"""
iTaK Git Tool - Git/GitHub operations.
"""

import subprocess
from typing import Optional
from tools.base import BaseTool, ToolResult


class GitTool(BaseTool):
    """Interact with Git repositories and GitHub.

    Supports common Git operations like clone, commit, push, pull,
    status, diff, and more. Can also interact with GitHub API for
    issues, PRs, releases, etc.
    """

    name = "git_tool"
    description = "Perform Git and GitHub operations."

    async def execute(
        self,
        action: str = "",
        repo: str = "",
        message: str = "",
        branch: str = "",
        files: Optional[list] = None,
        **kwargs,
    ) -> ToolResult:
        """Execute a Git operation.

        Args:
            action: The Git action to perform (clone, commit, push, pull, status, diff, etc.)
            repo: Repository URL or path
            message: Commit message (for commit action)
            branch: Branch name (for checkout, push, pull actions)
            files: List of files to add (for commit action)
        """
        if not action:
            return ToolResult(output="Error: 'action' is required.", error=True)

        try:
            if action == "clone":
                return await self._git_clone(repo)
            elif action == "status":
                return await self._git_status(repo)
            elif action == "diff":
                return await self._git_diff(repo)
            elif action == "add":
                return await self._git_add(repo, files or [])
            elif action == "commit":
                return await self._git_commit(repo, message)
            elif action == "push":
                return await self._git_push(repo, branch)
            elif action == "pull":
                return await self._git_pull(repo, branch)
            elif action == "checkout":
                return await self._git_checkout(repo, branch)
            elif action == "log":
                return await self._git_log(repo)
            else:
                return ToolResult(
                    output=f"Unknown Git action: {action}. Supported: clone, status, diff, add, commit, push, pull, checkout, log",
                    error=True,
                )
        except Exception as e:
            return ToolResult(output=f"Git error: {e}", error=True)

    async def _run_git_command(self, command: list, cwd: str = None) -> tuple:
        """Run a Git command and return output."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out after 30 seconds"
        except Exception as e:
            return 1, "", str(e)

    async def _git_clone(self, repo: str) -> ToolResult:
        """Clone a Git repository."""
        if not repo:
            return ToolResult(output="Error: 'repo' URL is required for clone.", error=True)

        returncode, stdout, stderr = await self._run_git_command(["git", "clone", repo])
        if returncode != 0:
            return ToolResult(output=f"Clone failed: {stderr}", error=True)
        return ToolResult(output=f"Successfully cloned: {repo}\n{stdout}")

    async def _git_status(self, repo: str = ".") -> ToolResult:
        """Get Git repository status."""
        returncode, stdout, stderr = await self._run_git_command(["git", "status"], cwd=repo)
        if returncode != 0:
            return ToolResult(output=f"Status failed: {stderr}", error=True)
        return ToolResult(output=f"Repository status:\n{stdout}")

    async def _git_diff(self, repo: str = ".") -> ToolResult:
        """Get Git diff."""
        returncode, stdout, stderr = await self._run_git_command(["git", "diff"], cwd=repo)
        if returncode != 0:
            return ToolResult(output=f"Diff failed: {stderr}", error=True)
        return ToolResult(output=f"Changes:\n{stdout}" if stdout else "No changes to show.")

    async def _git_add(self, repo: str = ".", files: list = None) -> ToolResult:
        """Add files to Git staging."""
        files = files or ["."]
        returncode, stdout, stderr = await self._run_git_command(
            ["git", "add"] + files, cwd=repo
        )
        if returncode != 0:
            return ToolResult(output=f"Add failed: {stderr}", error=True)
        return ToolResult(output=f"Added files: {', '.join(files)}")

    async def _git_commit(self, repo: str = ".", message: str = "") -> ToolResult:
        """Commit changes."""
        if not message:
            return ToolResult(output="Error: 'message' is required for commit.", error=True)

        returncode, stdout, stderr = await self._run_git_command(
            ["git", "commit", "-m", message], cwd=repo
        )
        if returncode != 0:
            return ToolResult(output=f"Commit failed: {stderr}", error=True)
        return ToolResult(output=f"Committed: {message}\n{stdout}")

    async def _git_push(self, repo: str = ".", branch: str = "") -> ToolResult:
        """Push changes to remote."""
        cmd = ["git", "push"]
        if branch:
            cmd.extend(["origin", branch])
        
        returncode, stdout, stderr = await self._run_git_command(cmd, cwd=repo)
        if returncode != 0:
            return ToolResult(output=f"Push failed: {stderr}", error=True)
        return ToolResult(output=f"Pushed successfully\n{stdout}")

    async def _git_pull(self, repo: str = ".", branch: str = "") -> ToolResult:
        """Pull changes from remote."""
        cmd = ["git", "pull"]
        if branch:
            cmd.extend(["origin", branch])
        
        returncode, stdout, stderr = await self._run_git_command(cmd, cwd=repo)
        if returncode != 0:
            return ToolResult(output=f"Pull failed: {stderr}", error=True)
        return ToolResult(output=f"Pulled successfully\n{stdout}")

    async def _git_checkout(self, repo: str = ".", branch: str = "") -> ToolResult:
        """Checkout a branch."""
        if not branch:
            return ToolResult(output="Error: 'branch' is required for checkout.", error=True)

        returncode, stdout, stderr = await self._run_git_command(
            ["git", "checkout", branch], cwd=repo
        )
        if returncode != 0:
            return ToolResult(output=f"Checkout failed: {stderr}", error=True)
        return ToolResult(output=f"Switched to branch: {branch}\n{stdout}")

    async def _git_log(self, repo: str = ".", limit: int = 10) -> ToolResult:
        """Get Git commit log."""
        returncode, stdout, stderr = await self._run_git_command(
            ["git", "log", f"-{limit}", "--oneline"], cwd=repo
        )
        if returncode != 0:
            return ToolResult(output=f"Log failed: {stderr}", error=True)
        return ToolResult(output=f"Recent commits:\n{stdout}")
