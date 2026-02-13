"""
iTaK Mission Control — Built-in Kanban task board.

§19 of the gameplan — every task the agent works on is tracked
with full lifecycle: inbox → in_progress → review → done.

Backed by SQLite for persistence. Graph queries via Neo4j deferred
until Phase 6.
"""

import json
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.agent import Agent


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class TaskStep:
    """A single step within a task."""
    name: str
    status: str = "pending"        # pending | in_progress | done | failed
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    notes: str = ""


@dataclass
class Deliverable:
    """An output artifact from a task."""
    type: str                      # url | file | screenshot
    title: str
    value: str                     # The actual URL / path / etc.


@dataclass
class Task:
    """A tracked unit of work."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    status: str = "inbox"          # inbox | in_progress | review | done | failed
    priority: str = "medium"       # low | medium | high | critical
    steps: list[TaskStep] = field(default_factory=list)
    current_step: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    deliverables: list[Deliverable] = field(default_factory=list)
    source: str = "cli"            # cli | discord | telegram | dashboard | heartbeat
    error_log: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        d = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "current_step": self.current_step,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "source": self.source,
            "steps": [asdict(s) for s in self.steps],
            "deliverables": [asdict(d) for d in self.deliverables],
            "error_log": self.error_log,
        }
        return d

    @staticmethod
    def from_dict(d: dict) -> "Task":
        """Deserialize from dict."""
        task = Task(
            id=d.get("id", str(uuid.uuid4())[:8]),
            title=d.get("title", ""),
            description=d.get("description", ""),
            status=d.get("status", "inbox"),
            priority=d.get("priority", "medium"),
            current_step=d.get("current_step", 0),
            created_at=d.get("created_at", time.time()),
            started_at=d.get("started_at"),
            completed_at=d.get("completed_at"),
            source=d.get("source", "cli"),
            error_log=d.get("error_log", []),
        )
        task.steps = [TaskStep(**s) for s in d.get("steps", [])]
        task.deliverables = [Deliverable(**dl) for dl in d.get("deliverables", [])]
        return task


# ---------------------------------------------------------------------------
# Priority helpers
# ---------------------------------------------------------------------------

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
PRIORITY_EMOJIS = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
STATUS_EMOJIS = {
    "inbox": "📥",
    "in_progress": "🔄",
    "review": "👀",
    "done": "✅",
    "failed": "❌",
}


# ---------------------------------------------------------------------------
# TaskBoard — SQLite-backed
# ---------------------------------------------------------------------------

DB_DIR = Path("data/db")
DB_PATH = DB_DIR / "tasks.db"


class TaskBoard:
    """Kanban-style task board backed by SQLite.

    Provides CRUD operations, status transitions, and
    formatted output for adapters (Discord, CLI, Dashboard).
    """

    def __init__(self, agent: Optional["Agent"] = None):
        self.agent = agent
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(DB_PATH))
        self._init_db()

    def _init_db(self):
        """Create the tasks table if it doesn't exist."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'inbox',
                priority TEXT NOT NULL DEFAULT 'medium',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        self._conn.commit()

    # ----- CRUD ---------------------------------------------------------------

    def create(self, title: str, description: str = "",
               priority: str = "medium", source: str = "cli") -> Task:
        """Create a new task."""
        task = Task(
            title=title,
            description=description,
            priority=priority,
            source=source,
        )
        self._conn.execute(
            "INSERT INTO tasks (id, data, status, priority, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (task.id, json.dumps(task.to_dict()), task.status,
             task.priority, task.created_at, time.time()),
        )
        self._conn.commit()
        return task

    def get(self, task_id: str) -> Optional[Task]:
        """Get a task by ID (supports prefix match)."""
        row = self._conn.execute(
            "SELECT data FROM tasks WHERE id LIKE ?",
            (f"{task_id}%",),
        ).fetchone()
        if row:
            return Task.from_dict(json.loads(row[0]))
        return None

    def list_all(self, status: Optional[str] = None,
                 limit: int = 50) -> list[Task]:
        """List tasks, optionally filtered by status."""
        if status:
            rows = self._conn.execute(
                "SELECT data FROM tasks WHERE status = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT data FROM tasks ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [Task.from_dict(json.loads(r[0])) for r in rows]

    def update(self, task: Task):
        """Persist task changes to the database."""
        self._conn.execute(
            "UPDATE tasks SET data = ?, status = ?, priority = ?, updated_at = ? "
            "WHERE id = ?",
            (json.dumps(task.to_dict()), task.status,
             task.priority, time.time(), task.id),
        )
        self._conn.commit()

    def delete(self, task_id: str) -> bool:
        """Delete a task."""
        cursor = self._conn.execute(
            "DELETE FROM tasks WHERE id LIKE ?", (f"{task_id}%",)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    # ----- State Transitions --------------------------------------------------

    def start(self, task_id: str) -> Optional[Task]:
        """Move task from inbox → in_progress."""
        task = self.get(task_id)
        if task and task.status == "inbox":
            task.status = "in_progress"
            task.started_at = time.time()
            self.update(task)
            return task
        return None

    def complete(self, task_id: str) -> Optional[Task]:
        """Move task to done."""
        task = self.get(task_id)
        if task:
            task.status = "done"
            task.completed_at = time.time()
            # Mark remaining steps as done
            for step in task.steps:
                if step.status != "done":
                    step.status = "done"
                    step.completed_at = time.time()
            self.update(task)
            return task
        return None

    def set_review(self, task_id: str) -> Optional[Task]:
        """Move task to review (awaiting user feedback)."""
        task = self.get(task_id)
        if task:
            task.status = "review"
            self.update(task)
            return task
        return None

    def fail(self, task_id: str, error: str = "") -> Optional[Task]:
        """Mark task as failed."""
        task = self.get(task_id)
        if task:
            task.status = "failed"
            if error:
                task.error_log.append(error)
            self.update(task)
            return task
        return None

    # ----- Step Management ----------------------------------------------------

    def add_step(self, task_id: str, step_name: str) -> Optional[Task]:
        """Add a step to a task."""
        task = self.get(task_id)
        if task:
            task.steps.append(TaskStep(name=step_name))
            self.update(task)
            return task
        return None

    def advance_step(self, task_id: str, notes: str = "") -> Optional[Task]:
        """Mark current step done and advance to next."""
        task = self.get(task_id)
        if not task or not task.steps:
            return None

        idx = task.current_step
        if idx < len(task.steps):
            task.steps[idx].status = "done"
            task.steps[idx].completed_at = time.time()
            task.steps[idx].notes = notes
            task.current_step = min(idx + 1, len(task.steps))

            # Start next step if available
            if task.current_step < len(task.steps):
                task.steps[task.current_step].status = "in_progress"
                task.steps[task.current_step].started_at = time.time()

            self.update(task)
        return task

    def add_deliverable(self, task_id: str, dtype: str,
                        title: str, value: str) -> Optional[Task]:
        """Add a deliverable to a task."""
        task = self.get(task_id)
        if task:
            task.deliverables.append(Deliverable(type=dtype, title=title, value=value))
            self.update(task)
            return task
        return None

    # ----- Formatting ---------------------------------------------------------

    def format_board(self, max_per_column: int = 5) -> str:
        """Format the task board for text-based display (CLI/Discord)."""
        tasks = self.list_all()
        columns: dict[str, list[Task]] = {
            "inbox": [], "in_progress": [], "review": [], "done": [],
        }
        for t in tasks:
            col = columns.get(t.status, columns.get("inbox", []))
            col.append(t)

        # Sort by priority within columns
        for col in columns.values():
            col.sort(key=lambda t: PRIORITY_ORDER.get(t.priority, 2))

        lines = ["📋 **iTaK Mission Control**\n"]

        for status, emoji in STATUS_EMOJIS.items():
            if status == "failed":
                continue
            col_tasks = columns.get(status, [])[:max_per_column]
            lines.append(f"\n{emoji} **{status.upper().replace('_', ' ')}** ({len(col_tasks)})")
            if not col_tasks:
                lines.append("  _(empty)_")
            for t in col_tasks:
                pri_emoji = PRIORITY_EMOJIS.get(t.priority, "⚪")
                progress = ""
                if t.steps:
                    done_steps = sum(1 for s in t.steps if s.status == "done")
                    progress = f" ({done_steps}/{len(t.steps)})"
                lines.append(f"  • {pri_emoji} `{t.id}` {t.title}{progress}")

        return "\n".join(lines)

    def format_task_detail(self, task_id: str) -> str:
        """Format a single task with full details."""
        task = self.get(task_id)
        if not task:
            return f"Task `{task_id}` not found."

        pri_emoji = PRIORITY_EMOJIS.get(task.priority, "⚪")
        status_emoji = STATUS_EMOJIS.get(task.status, "❓")

        lines = [
            f"{status_emoji} **{task.title}** `{task.id}`",
            f"Priority: {pri_emoji} {task.priority}",
            f"Source: {task.source}",
        ]

        if task.description:
            lines.append(f"Description: {task.description}")

        if task.steps:
            lines.append("\n**Steps:**")
            for i, step in enumerate(task.steps):
                icon = "✅" if step.status == "done" else "🔄" if step.status == "in_progress" else "⬜"
                notes = f" — {step.notes}" if step.notes else ""
                marker = " ← current" if i == task.current_step and step.status != "done" else ""
                lines.append(f"  {icon} {i+1}. {step.name}{notes}{marker}")

        if task.deliverables:
            lines.append("\n**Deliverables:**")
            for d in task.deliverables:
                lines.append(f"  📦 [{d.type}] {d.title}: {d.value}")

        if task.error_log:
            lines.append(f"\n**Errors:** {len(task.error_log)}")

        return "\n".join(lines)

    # ----- Stats --------------------------------------------------------------

    def get_stats(self) -> dict:
        """Get task board statistics for the dashboard."""
        tasks = self.list_all(limit=1000)
        stats = {
            "total": len(tasks),
            "by_status": {},
            "by_priority": {},
        }
        for t in tasks:
            stats["by_status"][t.status] = stats["by_status"].get(t.status, 0) + 1
            stats["by_priority"][t.priority] = stats["by_priority"].get(t.priority, 0) + 1
        return stats

    # ----- Cleanup ------------------------------------------------------------

    def close(self):
        """Close the database connection."""
        self._conn.close()
