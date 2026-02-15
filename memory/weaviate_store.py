"""
iTaK Weaviate Vector Store - Layer 4 of the 4-layer brain.
Semantic vector search for deep recall across all memories.
"""

import json
import logging
import time
from typing import Any, Optional

try:
    import weaviate
except Exception:
    weaviate = None

logger = logging.getLogger(__name__)


class WeaviateStore:
    """Weaviate-backed semantic vector search.

    Layer 4 of the 4-layer brain:
    - Layer 1: Markdown files (source of truth)
    - Layer 2: SQLite + embeddings (fast retrieval)
    - Layer 3: Neo4j (relationships)
    - Layer 4: Weaviate (semantic search) ← THIS

    Provides deep semantic recall - finds memories by meaning,
    not just keywords. Uses pre-computed embeddings from the
    model router's embedding model.
    """

    COLLECTION_NAME = "iTaKMemory"

    def __init__(self, config: dict):
        self.config = config
        self.url = config.get("url", "http://localhost:8080")
        self.client = None
        self._connected = False

    async def connect(self):
        """Connect to Weaviate."""
        try:
            if weaviate is None:
                raise ImportError("weaviate-client not installed")
            self.client = weaviate.Client(self.url)

            # Verify connection
            if not self.client.is_ready():
                raise ConnectionError("Weaviate not ready")

            self._connected = True
            logger.info(f"Connected to Weaviate at {self.url}")

            # Ensure schema exists
            await self._ensure_schema()

        except ImportError:
            logger.warning("weaviate-client not installed. Run: pip install weaviate-client")
            self._connected = False
        except Exception as e:
            logger.warning(f"Weaviate connection failed: {e}")
            self._connected = False

    async def _ensure_schema(self):
        """Create the memory collection schema if it doesn't exist."""
        if not self._connected:
            return

        try:
            if self.client.schema.exists(self.COLLECTION_NAME):
                return

            schema = {
                "class": self.COLLECTION_NAME,
                "vectorizer": "none",  # We provide our own vectors
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "category", "dataType": ["text"]},
                    {"name": "source", "dataType": ["text"]},
                    {"name": "metadata_json", "dataType": ["text"]},
                    {"name": "created_at", "dataType": ["number"]},
                    {"name": "room_id", "dataType": ["text"]},
                ],
            }
            self.client.schema.create_class(schema)
            logger.info(f"Created Weaviate collection: {self.COLLECTION_NAME}")
        except Exception as e:
            logger.warning(f"Schema creation failed: {e}")

    async def save(
        self,
        content: str,
        embedding: list[float] | None = None,
        vector: list[float] | None = None,
        category: str = "general",
        source: str = "agent",
        metadata: dict | None = None,
        room_id: str = "default",
    ) -> str:
        """Save a memory with its embedding vector. Returns UUID."""
        if not self._connected:
            return ""

        try:
            data_object = {
                "content": content,
                "category": category,
                "source": source,
                "metadata_json": json.dumps(metadata or {}),
                "created_at": time.time(),
                "room_id": room_id,
            }

            final_vector = embedding if embedding is not None else vector
            if final_vector is None:
                final_vector = []

            result = self.client.data_object.create(
                data_object=data_object,
                class_name=self.COLLECTION_NAME,
                vector=final_vector,
            )
            return result  # UUID string

        except Exception as e:
            logger.error(f"Weaviate save error: {e}")
            return ""

    async def search(
        self,
        query_embedding: list[float] | None = None,
        query: str | None = None,
        limit: int = 10,
        category: str | None = None,
        min_certainty: float = 0.7,
    ) -> list[dict]:
        """Semantic search using vector similarity."""
        if not self._connected:
            return []

        try:
            if query_embedding is None:
                query_embedding = []

            query = (
                self.client.query
                .get(self.COLLECTION_NAME, ["content", "category", "source", "metadata_json", "created_at", "room_id"])
                .with_near_vector({"vector": query_embedding, "certainty": min_certainty})
                .with_limit(limit)
                .with_additional(["certainty", "id"])
            )

            # Category filter
            if category:
                where_filter = {
                    "path": ["category"],
                    "operator": "Equal",
                    "valueText": category,
                }
                query = query.with_where(where_filter)

            result = query.do()

            memories = result.get("data", {}).get("Get", {}).get(self.COLLECTION_NAME, [])

            formatted = []
            for mem in memories:
                entry = {
                    "content": mem.get("content", ""),
                    "category": mem.get("category", "general"),
                    "source": mem.get("source", "weaviate"),
                    "metadata": json.loads(mem.get("metadata_json", "{}")),
                    "created_at": mem.get("created_at", 0),
                    "room_id": mem.get("room_id", "default"),
                    "score": mem.get("_additional", {}).get("certainty", 0),
                    "id": mem.get("_additional", {}).get("id", ""),
                    "layer": 4,
                }
                formatted.append(entry)

            return formatted

        except Exception as e:
            logger.error(f"Weaviate search error: {e}")
            return []

    async def delete(self, uuid: str) -> bool:
        """Delete a memory by UUID."""
        if not self._connected:
            return False

        try:
            self.client.data_object.delete(uuid, class_name=self.COLLECTION_NAME)
            return True
        except Exception as e:
            logger.error(f"Weaviate delete error: {e}")
            return False

    async def get_stats(self) -> dict:
        """Get collection statistics."""
        if not self._connected:
            return {"status": "disconnected"}

        try:
            result = (
                self.client.query
                .aggregate(self.COLLECTION_NAME)
                .with_meta_count()
                .do()
            )
            count = (
                result.get("data", {})
                .get("Aggregate", {})
                .get(self.COLLECTION_NAME, [{}])[0]
                .get("meta", {})
                .get("count", 0)
            )
            return {"status": "connected", "total_memories": count}
        except Exception:
            return {"status": "error"}

    async def close(self):
        """Close the Weaviate client."""
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected
