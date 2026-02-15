"""
iTaK Agent Swarm Coordinator - Parallel sub-agent orchestration.

Coordinate multiple specialized sub-agents working simultaneously
on different aspects of a complex task, then merge their results.

Gameplan §22 - "Agent Swarms & Custom Agents"
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger("itak.swarm")


class SwarmStrategy(str, Enum):
    """How subtasks are executed."""
    PARALLEL = "parallel"        # All at once via asyncio.gather
    SEQUENTIAL = "sequential"    # One after another
    PIPELINE = "pipeline"        # Output of one → input of next


class MergeStrategy(str, Enum):
    """How subtask results are combined."""
    CONCAT = "concat"            # Join all results
    SUMMARIZE = "summarize"      # LLM summarizes combined results
    BEST = "best"                # Pick the best result (by length/quality heuristic)
    CUSTOM = "custom"            # Custom merge function


@dataclass
class AgentProfile:
    """A specialized sub-agent personality."""
    name: str                        # "researcher"
    display_name: str                # "Research Specialist"
    system_prompt: str               # Full prompt content
    preferred_model: str | None = None  # Override model
    tools_allowed: list[str] = field(default_factory=list)  # Empty = all
    max_iterations: int = 25         # Limit monologue loops


@dataclass
class SubtaskResult:
    """Result from a single subtask execution."""
    profile: str
    message: str
    result: str = ""
    status: str = "pending"          # pending, running, done, failed
    error: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    duration_ms: int = 0


@dataclass
class SwarmTask:
    """A coordinated swarm execution."""
    subtasks: list[SubtaskResult]
    strategy: SwarmStrategy = SwarmStrategy.PARALLEL
    merge_strategy: MergeStrategy = MergeStrategy.CONCAT
    merged_result: str = ""
    status: str = "pending"          # pending, running, done, failed
    started_at: float = 0.0
    completed_at: float = 0.0


class SwarmCoordinator:
    """
    Coordinate multiple specialized sub-agents.

    Usage:
        swarm = SwarmCoordinator(agent)
        result = await swarm.execute([
            {"profile": "researcher", "message": "Research top 10 competitors"},
            {"profile": "coder", "message": "Build a landing page"},
            {"profile": "writer", "message": "Write compelling copy"},
        ], strategy="parallel", merge="summarize")
    """

    def __init__(self, agent):
        self.agent = agent
        self.config = agent.config.get("swarm", {}) if hasattr(agent, 'config') else {}
        self.profiles: dict[str, AgentProfile] = {}
        self.history: list[SwarmTask] = []
        
        # Configuration settings
        self.default_strategy = SwarmStrategy(self.config.get("default_strategy", "parallel"))
        self.default_merge = MergeStrategy(self.config.get("default_merge", "concat"))
        self.max_parallel = self.config.get("max_parallel", 5)
        self.timeout_seconds = self.config.get("timeout_seconds", 300)
        
        self._load_profiles()

    def _load_profiles(self):
        """Load agent profiles from prompts/profiles/ directory."""
        profiles_dir = Path(self.config.get("profiles_dir", "prompts/profiles"))
        if not profiles_dir.exists():
            profiles_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created prompts/profiles/ directory")
            return

        for profile_file in profiles_dir.glob("*.md"):
            name = profile_file.stem
            try:
                content = profile_file.read_text(encoding="utf-8")

                # Parse optional metadata from frontmatter
                display_name = name.replace("_", " ").title()
                preferred_model = None
                max_iterations = 25
                tools_allowed = []

                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        frontmatter = content[3:end].strip()
                        for line in frontmatter.split("\n"):
                            if ":" in line:
                                key, val = line.split(":", 1)
                                key = key.strip().lower()
                                val = val.strip()
                                if key == "display_name":
                                    display_name = val
                                elif key == "preferred_model":
                                    preferred_model = val if val else None
                                elif key == "max_iterations":
                                    max_iterations = int(val)
                                elif key == "tools_allowed":
                                    tools_allowed = [
                                        t.strip() for t in val.split(",") if t.strip()
                                    ]
                        content = content[end + 3:].strip()

                self.profiles[name] = AgentProfile(
                    name=name,
                    display_name=display_name,
                    system_prompt=content,
                    preferred_model=preferred_model,
                    tools_allowed=tools_allowed,
                    max_iterations=max_iterations,
                )
                logger.debug(f"Loaded profile: {name} ({display_name})")

            except Exception as e:
                logger.warning(f"Failed to load profile {name}: {e}")

        if self.profiles:
            logger.info(
                f"Swarm Coordinator: {len(self.profiles)} profiles loaded "
                f"({', '.join(self.profiles.keys())})"
            )

    def get_profile(self, name: str) -> AgentProfile | None:
        """Get a profile by name."""
        return self.profiles.get(name)

    def list_profiles(self) -> list[dict]:
        """List all available profiles."""
        return [
            {
                "name": p.name,
                "display_name": p.display_name,
                "preferred_model": p.preferred_model,
                "max_iterations": p.max_iterations,
                "tools_allowed": p.tools_allowed,
            }
            for p in self.profiles.values()
        ]

    # ── Execution ──────────────────────────────────────────────

    async def execute(
        self,
        subtasks: list[dict],
        strategy: str = "parallel",
        merge: str = "concat",
    ) -> str:
        """
        Execute a swarm of subtasks.

        Args:
            subtasks: List of {"profile": str, "message": str}
            strategy: "parallel", "sequential", or "pipeline"
            merge: "concat", "summarize", "best", or "custom"

        Returns:
            Merged result string
        """
        strat = SwarmStrategy(strategy)
        merge_strat = MergeStrategy(merge)

        # Build SwarmTask
        swarm = SwarmTask(
            subtasks=[
                SubtaskResult(
                    profile=st.get("profile", "default"),
                    message=st.get("message", ""),
                )
                for st in subtasks
            ],
            strategy=strat,
            merge_strategy=merge_strat,
            started_at=time.time(),
        )
        swarm.status = "running"

        logger.info(
            f"Swarm started: {len(swarm.subtasks)} subtasks, "
            f"strategy={strategy}, merge={merge}"
        )

        try:
            if strat == SwarmStrategy.PARALLEL:
                await self._execute_parallel(swarm)
            elif strat == SwarmStrategy.SEQUENTIAL:
                await self._execute_sequential(swarm)
            elif strat == SwarmStrategy.PIPELINE:
                await self._execute_pipeline(swarm)

            # Merge results
            swarm.merged_result = await self._merge(swarm, merge_strat)
            swarm.status = "done"

        except Exception as e:
            swarm.status = "failed"
            swarm.merged_result = f"Swarm execution failed: {e}"
            logger.error(f"Swarm failed: {e}")

        swarm.completed_at = time.time()
        self.history.append(swarm)

        duration = int((swarm.completed_at - swarm.started_at) * 1000)
        done_count = sum(1 for s in swarm.subtasks if s.status == "done")
        logger.info(
            f"Swarm completed: {done_count}/{len(swarm.subtasks)} succeeded "
            f"in {duration}ms"
        )

        return swarm.merged_result

    async def _execute_parallel(self, swarm: SwarmTask):
        """Execute all subtasks concurrently."""
        tasks = [
            self._run_subtask(st) for st in swarm.subtasks
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_sequential(self, swarm: SwarmTask):
        """Execute subtasks one after another."""
        for st in swarm.subtasks:
            await self._run_subtask(st)

    async def _execute_pipeline(self, swarm: SwarmTask):
        """Execute subtasks as a pipeline - output feeds into next input."""
        prev_result = ""
        for st in swarm.subtasks:
            if prev_result:
                st.message = f"{st.message}\n\nContext from previous step:\n{prev_result}"
            await self._run_subtask(st)
            prev_result = st.result

    async def _run_subtask(self, subtask: SubtaskResult):
        """Run a single subtask using call_subordinate pattern."""
        subtask.status = "running"
        subtask.started_at = time.time()

        try:
            # Use the existing sub-agent system if available
            if hasattr(self.agent, 'sub_agents') and self.agent.sub_agents:
                result = await self.agent.sub_agents.delegate(
                    message=subtask.message,
                    profile=subtask.profile,
                )
                subtask.result = result if isinstance(result, str) else str(result)
            else:
                # Fallback: run through main agent monologue
                subtask.result = await self.agent.monologue(subtask.message)

            subtask.status = "done"

        except Exception as e:
            subtask.status = "failed"
            subtask.error = str(e)
            subtask.result = f"[Subtask failed: {e}]"
            logger.error(
                f"Subtask {subtask.profile} failed: {e}"
            )

        subtask.completed_at = time.time()
        subtask.duration_ms = int(
            (subtask.completed_at - subtask.started_at) * 1000
        )

    # ── Merge ──────────────────────────────────────────────────

    async def _merge(self, swarm: SwarmTask, strategy: MergeStrategy) -> str:
        """Merge subtask results."""
        results = [
            st for st in swarm.subtasks if st.status == "done" and st.result
        ]

        if not results:
            return "[No subtasks completed successfully]"

        if strategy == MergeStrategy.CONCAT:
            parts = []
            for st in results:
                parts.append(f"## {st.profile.title()} Agent\n\n{st.result}")
            return "\n\n---\n\n".join(parts)

        elif strategy == MergeStrategy.SUMMARIZE:
            # Use LLM to summarize combined results
            combined = "\n\n---\n\n".join(
                f"[{st.profile}]: {st.result}" for st in results
            )
            try:
                if hasattr(self.agent, 'model_router'):
                    summary_prompt = (
                        "Synthesize the following results from multiple agents "
                        "into a single coherent response:\n\n"
                        f"{combined}"
                    )
                    summary = await self.agent.model_router.chat(
                        [{"role": "user", "content": summary_prompt}],
                        purpose="utility"
                    )
                    return summary
            except Exception as e:
                logger.warning(f"Summarize merge failed, falling back to concat: {e}")
            # Fallback to concat
            return await self._merge(swarm, MergeStrategy.CONCAT)

        elif strategy == MergeStrategy.BEST:
            # Pick the longest/most detailed result
            best = max(results, key=lambda st: len(st.result))
            return best.result

        return await self._merge(swarm, MergeStrategy.CONCAT)

    # ── Status ─────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get swarm statistics."""
        return {
            "profiles_loaded": len(self.profiles),
            "profile_names": list(self.profiles.keys()),
            "total_swarms": len(self.history),
            "successful_swarms": sum(
                1 for s in self.history if s.status == "done"
            ),
        }
