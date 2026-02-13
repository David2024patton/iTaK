"""
iTaK SQLite Memory Store — Layer 2 of the 4-layer brain.
Fast local storage with vector embeddings for semantic search.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np


class SQLiteStore:
    """SQLite-backed memory with vector similarity search.

    Layer 2 of the 4-layer brain:
    - Layer 1: Markdown files (source of truth)
    - Layer 2: SQLite + embeddings (fast retrieval) ← THIS
    - Layer 3: Neo4j (relationships)
    - Layer 4: Weaviate (semantic search)
    """

    def __init__(self, db_path: str = "data/db/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                category TEXT DEFAULT 'general',
                source TEXT DEFAULT 'agent',
                embedding BLOB,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                access_count INTEGER DEFAULT 0,
                last_accessed REAL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_category
            ON memories(category)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_created
            ON memories(created_at)
        """)
        # FTS5 for keyword search
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
                USING fts5(content, metadata, category)
            """)
        except sqlite3.OperationalError:
            pass  # FTS5 not available
        conn.commit()
        conn.close()

    async def save(
        self,
        content: str,
        metadata: dict | None = None,
        category: str = "general",
        source: str = "agent",
        embedding: list[float] | None = None,
    ) -> int:
        """Save a memory entry. Returns the memory ID."""
        now = time.time()
        emb_blob = self._embedding_to_blob(embedding) if embedding else None

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute(
            """INSERT INTO memories
               (content, metadata, category, source, embedding, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                content,
                json.dumps(metadata or {}),
                category,
                source,
                emb_blob,
                now,
                now,
            ),
        )
        memory_id = cursor.lastrowid

        # Update FTS
        try:
            conn.execute(
                "INSERT INTO memories_fts(rowid, content, metadata, category) VALUES (?, ?, ?, ?)",
                (memory_id, content, json.dumps(metadata or {}), category),
            )
        except sqlite3.OperationalError:
            pass

        conn.commit()
        conn.close()
        return memory_id

    async def search(
        self,
        query: str = "",
        query_embedding: list[float] | None = None,
        category: str | None = None,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> list[dict]:
        """Search memories by text and/or vector similarity."""
        results = []

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row

        # Vector similarity search
        if query_embedding:
            rows = conn.execute("SELECT * FROM memories WHERE embedding IS NOT NULL").fetchall()
            scored = []
            for row in rows:
                stored_emb = self._blob_to_embedding(row["embedding"])
                if stored_emb:
                    sim = self._cosine_similarity(query_embedding, stored_emb)
                    if sim >= threshold:
                        entry = dict(row)
                        entry["score"] = sim
                        entry["embedding"] = None  # Don't return blob
                        scored.append(entry)
            scored.sort(key=lambda x: x["score"], reverse=True)
            results = scored[:limit]

        # FTS keyword search (if no embedding or as supplement)
        elif query:
            try:
                rows = conn.execute(
                    """SELECT m.*, memories_fts.rank as score
                       FROM memories_fts
                       JOIN memories m ON memories_fts.rowid = m.id
                       WHERE memories_fts MATCH ?
                       ORDER BY rank
                       LIMIT ?""",
                    (query, limit),
                ).fetchall()
                results = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                # Fallback: LIKE search
                rows = conn.execute(
                    "SELECT *, 0.5 as score FROM memories WHERE content LIKE ? LIMIT ?",
                    (f"%{query}%", limit),
                ).fetchall()
                results = [dict(r) for r in rows]

        # Category filter
        if category and not results:
            rows = conn.execute(
                "SELECT *, 1.0 as score FROM memories WHERE category = ? ORDER BY created_at DESC LIMIT ?",
                (category, limit),
            ).fetchall()
            results = [dict(r) for r in rows]

        # Update access counts
        for r in results:
            conn.execute(
                "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                (time.time(), r["id"]),
            )
        conn.commit()
        conn.close()

        # Clean up blobs from results
        for r in results:
            r.pop("embedding", None)
            if isinstance(r.get("metadata"), str):
                try:
                    r["metadata"] = json.loads(r["metadata"])
                except json.JSONDecodeError:
                    pass

        return results

    async def delete(self, memory_id: int) -> bool:
        """Delete a memory by ID."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        try:
            conn.execute("DELETE FROM memories_fts WHERE rowid = ?", (memory_id,))
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        return True

    async def delete_by_query(self, query: str) -> int:
        """Delete memories matching a query. Returns count deleted."""
        results = await self.search(query=query, limit=50, threshold=0.5)
        count = 0
        for r in results:
            await self.delete(r["id"])
            count += 1
        return count

    async def get_stats(self) -> dict:
        """Get memory store statistics."""
        conn = sqlite3.connect(str(self.db_path))
        total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        categories = conn.execute(
            "SELECT category, COUNT(*) FROM memories GROUP BY category"
        ).fetchall()
        conn.close()
        return {
            "total_memories": total,
            "categories": {cat: cnt for cat, cnt in categories},
        }

    @staticmethod
    def _embedding_to_blob(embedding: list[float]) -> bytes:
        """Convert embedding list to bytes for SQLite storage."""
        return np.array(embedding, dtype=np.float32).tobytes()

    @staticmethod
    def _blob_to_embedding(blob: bytes) -> list[float] | None:
        """Convert bytes back to embedding list."""
        if not blob:
            return None
        return np.frombuffer(blob, dtype=np.float32).tolist()

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        dot = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))
