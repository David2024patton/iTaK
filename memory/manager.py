"""
iTaK Memory Manager - Unified interface across all 4 memory layers.
Searches markdown files, SQLite, Neo4j, and Weaviate.
"""

import logging
import time
from pathlib import Path
from typing import Any, Optional

from memory.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)


class MemoryManager:
    """Unified memory interface across all 4 layers.

    Layer 1: Markdown files (SOUL.md, USER.md, MEMORY.md, AGENTS.md)
    Layer 2: SQLite + embeddings (fast vector search)
    Layer 3: Neo4j (relationships / knowledge graph)
    Layer 4: Weaviate (semantic vector search)

    Search order: SQLite (fast) → Markdown (always loaded) → Neo4j → Weaviate
    """

    def __init__(self, config: dict, model_router=None, full_config: dict = None):
        self.config = config
        self.model_router = model_router
        self.full_config = full_config or {}

        # Layer 1: Markdown files
        self.memory_dir = Path("memory")

        # Layer 2: SQLite (with path traversal guard)
        sqlite_path = config.get("sqlite_path", "data/db/memory.db")
        try:
            from security.path_guard import validate_path
            safe, reason = validate_path(
                sqlite_path,
                allowed_roots=["data", "."],
                allow_absolute=False,
            )
            if not safe:
                logger.warning(f"Memory path blocked: {reason}, using default")
                sqlite_path = "data/db/memory.db"
        except ImportError:
            pass
        self.sqlite = SQLiteStore(db_path=sqlite_path)

        # Layer 3: Neo4j
        self.neo4j = None
        # Try nested config first (memory.neo4j), then top-level (neo4j)
        neo4j_config = config.get("neo4j", {})
        if not neo4j_config.get("uri"):
            neo4j_config = self.full_config.get("neo4j", {})
        
        # Only initialize if enabled and URI is set
        if neo4j_config.get("enabled", False) and neo4j_config.get("uri"):
            try:
                from memory.neo4j_store import Neo4jStore
                self.neo4j = Neo4jStore(neo4j_config)
            except Exception as e:
                logger.warning(f"Neo4j store init failed: {e}")

        # Layer 4: Weaviate
        self.weaviate = None
        # Try nested config first (memory.weaviate), then top-level (weaviate)
        weaviate_config = config.get("weaviate", {})
        if not weaviate_config.get("url"):
            weaviate_config = self.full_config.get("weaviate", {})
            
        # Only initialize if enabled and URL is set
        if weaviate_config.get("enabled", False) and weaviate_config.get("url"):
            try:
                from memory.weaviate_store import WeaviateStore
                self.weaviate = WeaviateStore(weaviate_config)
            except Exception as e:
                logger.warning(f"Weaviate store init failed: {e}")

        # Settings
        self.similarity_threshold = config.get("similarity_threshold", 0.7)
        self.max_results = config.get("max_results", 10)
        self.auto_memorize = config.get("auto_memorize", True)

    async def connect_stores(self):
        """Connect to Neo4j and Weaviate (call once at startup)."""
        if self.neo4j:
            await self.neo4j.connect()
        if self.weaviate:
            await self.weaviate.connect()

    async def save(
        self,
        content: str,
        category: str = "general",
        metadata: dict | None = None,
        source: str = "agent",
        entities: list[str] | None = None,
    ) -> int:
        """Save a memory across all relevant layers."""
        # Generate embedding if model router available
        embedding = None
        if self.model_router:
            try:
                embeddings = await self.model_router.embed([content])
                embedding = embeddings[0] if embeddings else None
            except Exception:
                pass

        # Save to SQLite (Layer 2) - always
        memory_id = await self.sqlite.save(
            content=content,
            metadata=metadata,
            category=category,
            source=source,
            embedding=embedding,
        )

        # Append to MEMORY.md (Layer 1) for important memories
        if category in ("decision", "lesson", "fact", "solution"):
            await self._append_to_markdown(content, category)

        # Save to Neo4j (Layer 3) - if connected and entities provided
        if self.neo4j and self.neo4j.is_connected:
            try:
                await self.neo4j.save_memory(
                    content=content,
                    category=category,
                    entities=entities,
                    metadata=metadata,
                )
            except Exception as e:
                logger.warning(f"Neo4j save failed: {e}")

        # Save to Weaviate (Layer 4) - if connected and embedding available
        if self.weaviate and self.weaviate.is_connected and embedding:
            try:
                await self.weaviate.save(
                    content=content,
                    embedding=embedding,
                    category=category,
                    source=source,
                    metadata=metadata,
                )
            except Exception as e:
                logger.warning(f"Weaviate save failed: {e}")

        return memory_id

    async def search(
        self,
        query: str,
        category: str | None = None,
        limit: int | None = None,
        threshold: float | None = None,
    ) -> list[dict]:
        """Search across all memory layers, merge and rank results."""
        limit = limit or self.max_results
        threshold = threshold or self.similarity_threshold
        all_results = []

        # Generate query embedding
        query_embedding = None
        if self.model_router:
            try:
                embeddings = await self.model_router.embed([query])
                query_embedding = embeddings[0] if embeddings else None
            except Exception:
                pass

        # Search Layer 2: SQLite (fastest)
        sqlite_results = await self.sqlite.search(
            query=query,
            query_embedding=query_embedding,
            category=category,
            limit=limit,
            threshold=threshold,
        )
        all_results.extend(sqlite_results)

        # Search Layer 1: Markdown files (always check)
        md_results = await self._search_markdown(query)
        all_results.extend(md_results)

        # Search Layer 3: Neo4j (relationships)
        if self.neo4j and self.neo4j.is_connected:
            try:
                neo4j_results = await self.neo4j.search(
                    query=query, category=category, limit=limit
                )
                for r in neo4j_results:
                    r["layer"] = 3
                all_results.extend(neo4j_results)
            except Exception as e:
                logger.warning(f"Neo4j search failed: {e}")

        # Search Layer 4: Weaviate (semantic)
        if self.weaviate and self.weaviate.is_connected and query_embedding:
            try:
                weaviate_results = await self.weaviate.search(
                    query_embedding=query_embedding,
                    category=category,
                    limit=limit,
                    min_certainty=threshold,
                )
                all_results.extend(weaviate_results)
            except Exception as e:
                logger.warning(f"Weaviate search failed: {e}")

        # Deduplicate and rank
        seen = set()
        unique_results = []
        for r in sorted(all_results, key=lambda x: x.get("score", 0), reverse=True):
            content_hash = hash(r.get("content", "")[:100])
            if content_hash not in seen:
                seen.add(content_hash)
                unique_results.append(r)

        return unique_results[:limit]

    async def delete(self, query: str) -> int:
        """Delete memories matching a query from all layers."""
        count = await self.sqlite.delete_by_query(query)
        return count

    async def get_entity_context(self, entity_name: str) -> str:
        """Get knowledge graph context for an entity (Layer 3)."""
        if self.neo4j and self.neo4j.is_connected:
            return await self.neo4j.get_entity_context(entity_name)
        return f"Neo4j not connected. Cannot look up '{entity_name}'."

    async def save_relationship(
        self,
        from_name: str,
        from_type: str,
        to_name: str,
        to_type: str,
        rel_type: str,
        properties: dict | None = None,
    ):
        """Save a relationship to the knowledge graph (Layer 3)."""
        if self.neo4j and self.neo4j.is_connected:
            await self.neo4j.save_relationship(
                from_name, from_type, to_name, to_type, rel_type, properties
            )

    async def _search_markdown(self, query: str) -> list[dict]:
        """Search Layer 1 markdown files for relevant content."""
        results = []
        query_lower = query.lower()

        for md_file in self.memory_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    lines = content.split("\n")
                    relevant_lines = []
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            start = max(0, i - 5)
                            end = min(len(lines), i + 6)
                            relevant_lines.extend(lines[start:end])
                            break

                    if relevant_lines:
                        results.append({
                            "content": "\n".join(relevant_lines),
                            "metadata": {"source_file": md_file.name, "layer": 1},
                            "category": "markdown",
                            "score": 0.6,
                        })
            except Exception:
                continue

        return results

    async def _append_to_markdown(self, content: str, category: str):
        """Append a memory to MEMORY.md."""
        memory_file = self.memory_dir / "MEMORY.md"
        if memory_file.exists():
            try:
                section_map = {
                    "decision": "## Architecture Decisions",
                    "lesson": "## Lessons Learned",
                    "fact": "## Important Facts",
                    "solution": "## Lessons Learned",
                }
                section = section_map.get(category, "## Important Facts")

                existing = memory_file.read_text(encoding="utf-8")
                timestamp = time.strftime("%Y-%m-%d %H:%M")
                entry = f"\n- [{timestamp}] {content}"

                if section in existing:
                    existing = existing.replace(section, f"{section}{entry}", 1)
                else:
                    existing += f"\n\n{section}{entry}"

                memory_file.write_text(existing, encoding="utf-8")
            except Exception:
                pass

    async def get_context(self) -> str:
        """Load all Layer 1 markdown files into a context string."""
        context_parts = []
        for filename in ["SOUL.md", "USER.md", "MEMORY.md", "AGENTS.md"]:
            filepath = self.memory_dir / filename
            if filepath.exists():
                content = filepath.read_text(encoding="utf-8")
                context_parts.append(f"### {filename}\n{content}")
        return "\n\n---\n\n".join(context_parts)

    async def get_stats(self) -> dict:
        """Get memory statistics across all layers."""
        sqlite_stats = await self.sqlite.get_stats()
        stats = {
            "layer_1_files": len(list(self.memory_dir.glob("*.md"))),
            "layer_2_sqlite": sqlite_stats,
        }

        if self.neo4j:
            stats["layer_3_neo4j"] = "connected" if self.neo4j.is_connected else "disconnected"
        else:
            stats["layer_3_neo4j"] = "not configured"

        if self.weaviate:
            stats["layer_4_weaviate"] = await self.weaviate.get_stats() if self.weaviate.is_connected else {"status": "disconnected"}
        else:
            stats["layer_4_weaviate"] = "not configured"

        return stats

    async def close(self):
        """Close all store connections."""
        if self.neo4j:
            await self.neo4j.close()
        if self.weaviate:
            await self.weaviate.close()
