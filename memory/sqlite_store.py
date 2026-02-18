"""
iTaK SQLite Memory Store - Layer 2 of the 4-layer brain.
Fast local storage with vector embeddings for semantic search.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any
import threading

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
        
        # Thread-local storage for connections (one connection per thread)
        self._local = threading.local()
        
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection. Creates one if doesn't exist."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = self._get_connection()
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

        conn.execute("""
            CREATE TABLE IF NOT EXISTS skill_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                skill_type TEXT DEFAULT 'general',
                domain TEXT DEFAULT 'general',
                metadata TEXT DEFAULT '{}',
                source_memory_id INTEGER,
                confidence REAL DEFAULT 0.75,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                embedding BLOB,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                last_used REAL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_skill_bank_type
            ON skill_bank(skill_type)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_skill_bank_domain
            ON skill_bank(domain)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_skill_bank_confidence
            ON skill_bank(confidence)
        """)
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS skill_bank_fts
                USING fts5(title, content, domain, metadata)
            """)
        except sqlite3.OperationalError:
            pass
        conn.commit()

    async def initialize(self):
        """Backward-compatible initializer for async setup flows."""
        return self

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

        conn = self._get_connection()
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

        conn = self._get_connection()

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
        conn = self._get_connection()
        conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        try:
            conn.execute("DELETE FROM memories_fts WHERE rowid = ?", (memory_id,))
        except sqlite3.OperationalError:
            pass
        conn.commit()
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
        conn = self._get_connection()
        total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        total_skills = conn.execute("SELECT COUNT(*) FROM skill_bank").fetchone()[0]
        categories = conn.execute(
            "SELECT category, COUNT(*) FROM memories GROUP BY category"
        ).fetchall()
        skill_domains = conn.execute(
            "SELECT domain, COUNT(*) FROM skill_bank GROUP BY domain"
        ).fetchall()
        return {
            "total_memories": total,
            "total_entries": total,
            "total_skills": total_skills,
            "categories": {cat: cnt for cat, cnt in categories},
            "skill_domains": {domain: cnt for domain, cnt in skill_domains},
        }

    async def save_skill(
        self,
        title: str,
        content: str,
        skill_type: str = "general",
        domain: str = "general",
        metadata: dict | None = None,
        source_memory_id: int | None = None,
        confidence: float = 0.75,
        embedding: list[float] | None = None,
    ) -> int:
        """Save a distilled skill to the SkillBank."""
        now = time.time()
        emb_blob = self._embedding_to_blob(embedding) if embedding else None

        conn = self._get_connection()
        cursor = conn.execute(
            """INSERT INTO skill_bank
               (title, content, skill_type, domain, metadata, source_memory_id,
                confidence, embedding, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title,
                content,
                skill_type,
                domain,
                json.dumps(metadata or {}),
                source_memory_id,
                float(max(0.0, min(1.0, confidence))),
                emb_blob,
                now,
                now,
            ),
        )
        skill_id = cursor.lastrowid

        try:
            conn.execute(
                "INSERT INTO skill_bank_fts(rowid, title, content, domain, metadata) VALUES (?, ?, ?, ?, ?)",
                (skill_id, title, content, domain, json.dumps(metadata or {})),
            )
        except sqlite3.OperationalError:
            pass

        conn.commit()
        return skill_id

    async def search_skills(
        self,
        query: str = "",
        query_embedding: list[float] | None = None,
        skill_type: str | None = None,
        domain: str | None = None,
        limit: int = 10,
        threshold: float = 0.65,
    ) -> list[dict]:
        """Search SkillBank by text and/or vector similarity."""
        results = []
        conn = self._get_connection()

        if query_embedding:
            rows = conn.execute("SELECT * FROM skill_bank WHERE embedding IS NOT NULL").fetchall()
            scored = []
            for row in rows:
                stored_emb = self._blob_to_embedding(row["embedding"])
                if stored_emb:
                    sim = self._cosine_similarity(query_embedding, stored_emb)
                    if sim >= threshold:
                        entry = dict(row)
                        entry["score"] = sim
                        entry["embedding"] = None
                        scored.append(entry)
            scored.sort(key=lambda x: x.get("score", 0), reverse=True)
            results = scored[:limit]
        elif query:
            try:
                rows = conn.execute(
                    """SELECT s.*, skill_bank_fts.rank as score
                       FROM skill_bank_fts
                       JOIN skill_bank s ON skill_bank_fts.rowid = s.id
                       WHERE skill_bank_fts MATCH ?
                       ORDER BY rank
                       LIMIT ?""",
                    (query, limit),
                ).fetchall()
                results = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                rows = conn.execute(
                    "SELECT *, 0.5 as score FROM skill_bank WHERE content LIKE ? OR title LIKE ? LIMIT ?",
                    (f"%{query}%", f"%{query}%", limit),
                ).fetchall()
                results = [dict(r) for r in rows]

        if skill_type:
            results = [r for r in results if r.get("skill_type") == skill_type]
        if domain:
            results = [r for r in results if r.get("domain") == domain]

        if not results and (skill_type or domain):
            clauses = []
            values: list[Any] = []
            if skill_type:
                clauses.append("skill_type = ?")
                values.append(skill_type)
            if domain:
                clauses.append("domain = ?")
                values.append(domain)
            where = " AND ".join(clauses) if clauses else "1=1"
            rows = conn.execute(
                f"SELECT *, confidence as score FROM skill_bank WHERE {where} ORDER BY confidence DESC, created_at DESC LIMIT ?",
                (*values, limit),
            ).fetchall()
            results = [dict(r) for r in rows]

        now = time.time()
        for r in results:
            conn.execute(
                "UPDATE skill_bank SET usage_count = usage_count + 1, last_used = ? WHERE id = ?",
                (now, r["id"]),
            )
        conn.commit()

        for r in results:
            r.pop("embedding", None)
            if isinstance(r.get("metadata"), str):
                try:
                    r["metadata"] = json.loads(r["metadata"])
                except json.JSONDecodeError:
                    pass

        return results[:limit]

    async def record_skill_outcome(self, skill_id: int, success: bool = True):
        """Update skill success/failure counters based on observed outcome."""
        conn = self._get_connection()
        field = "success_count" if success else "failure_count"
        conn.execute(
            f"UPDATE skill_bank SET {field} = {field} + 1, updated_at = ? WHERE id = ?",
            (time.time(), skill_id),
        )
        conn.commit()

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
