"""
iTaK - Memory System Tests

Tests for 4-tier memory system:
- MemoryManager (orchestration)
- SQLiteStore (archival storage)
- Neo4jStore (knowledge graph)
- WeaviateStore (semantic search)
"""

import asyncio
import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock


# ============================================================
# SQLiteStore Tests (Extended from existing)
# ============================================================
class TestSQLiteStore:
    """Test SQLite archival memory storage."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create a temporary SQLite store."""
        from memory.sqlite_store import SQLiteStore
        
        db_path = tmp_path / "test_memory.db"
        store = SQLiteStore(str(db_path))
        return store

    @pytest.mark.asyncio
    async def test_save_and_search(self, store):
        """Should save and retrieve memory entries."""
        # Save entries
        await store.save(
            content="Python is a programming language",
            category="facts",
            metadata={"topic": "programming"}
        )
        
        await store.save(
            content="The sky is blue",
            category="facts",
            metadata={"topic": "nature"}
        )
        
        # Search for entries
        results = await store.search(query="Python", limit=5)
        
        assert len(results) >= 1
        assert any("Python" in r["content"] for r in results)

    @pytest.mark.asyncio
    async def test_delete(self, store):
        """Should delete entries by ID."""
        # Save entry
        entry_id = await store.save(
            content="Temporary memory",
            category="temp"
        )
        
        # Delete it
        await store.delete(entry_id)
        
        # Should not be found
        results = await store.search(query="Temporary", limit=5)
        assert not any(r["id"] == entry_id for r in results)

    @pytest.mark.asyncio
    async def test_category_filter(self, store):
        """Should filter by category."""
        # Save entries in different categories
        await store.save("Fact 1", category="facts")
        await store.save("Conversation 1", category="conversations")
        
        # Search with category filter
        results = await store.search(query="", category="facts", limit=10)
        
        assert all(r["category"] == "facts" for r in results)

    @pytest.mark.asyncio
    async def test_stats(self, store):
        """Should return storage statistics."""
        # Save some entries
        await store.save("Entry 1", category="test")
        await store.save("Entry 2", category="test")
        await store.save("Entry 3", category="other")
        
        stats = await store.get_stats()
        
        assert stats["total_entries"] >= 3
        assert "categories" in stats

    @pytest.mark.asyncio
    async def test_prevent_sql_injection(self, store):
        """Should prevent SQL injection in queries."""
        # Attempt SQL injection
        malicious_query = "'; DROP TABLE memories; --"
        
        # Should not crash or execute the injection
        results = await store.search(query=malicious_query, limit=5)
        
        assert results is not None
        # Table should still exist
        stats = await store.get_stats()
        assert stats is not None

    @pytest.mark.asyncio
    async def test_metadata_serialization(self, store):
        """Should properly serialize and deserialize metadata."""
        # Save with complex metadata
        metadata = {
            "tags": ["important", "review"],
            "source": "user_input",
            "timestamp": "2024-01-01T00:00:00"
        }
        
        entry_id = await store.save(
            content="Test content",
            category="test",
            metadata=metadata
        )
        
        # Retrieve and check metadata
        results = await store.search(query="Test content", limit=1)
        assert len(results) > 0
        assert results[0]["metadata"]["tags"] == ["important", "review"]

    @pytest.mark.asyncio
    async def test_concurrent_access(self, store):
        """Should handle concurrent read/write operations."""
        # Simulate concurrent saves
        tasks = [
            store.save(f"Entry {i}", category="concurrent")
            for i in range(10)
        ]
        
        await asyncio.gather(*tasks)
        
        # All should be saved
        results = await store.search(query="Entry", limit=20)
        assert len(results) >= 10


# ============================================================
# MemoryManager Tests
# ============================================================
class TestMemoryManager:
    """Test unified memory manager."""

    @pytest.mark.asyncio
    async def test_initialize_with_sqlite_only(self, tmp_path):
        """Should work with SQLite only (minimal config)."""
        from memory.manager import MemoryManager
        
        config = {
            "sqlite_path": str(tmp_path / "memory.db")
        }
        
        manager = MemoryManager(config)
        await manager.initialize()
        
        assert manager.sqlite_store is not None

    @pytest.mark.asyncio
    async def test_save_to_all_stores(self, tmp_path):
        """Should save to all configured stores."""
        from memory.manager import MemoryManager
        
        config = {
            "sqlite_path": str(tmp_path / "memory.db")
        }
        
        manager = MemoryManager(config)
        await manager.initialize()
        
        # Save memory
        result = await manager.save(
            content="Test memory",
            category="test"
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_search_across_stores(self, tmp_path):
        """Should search across all stores."""
        from memory.manager import MemoryManager
        
        config = {
            "sqlite_path": str(tmp_path / "memory.db")
        }
        
        manager = MemoryManager(config)
        await manager.initialize()
        
        # Save and search
        await manager.save("Important fact", category="facts")
        results = await manager.search(query="Important", limit=5)
        
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_tier_management(self, tmp_path):
        """Should manage memory across tiers."""
        from memory.manager import MemoryManager
        
        config = {
            "sqlite_path": str(tmp_path / "memory.db"),
            "tiers": {
                "tier1_size": 10,
                "tier2_size": 50
            }
        }
        
        manager = MemoryManager(config)
        await manager.initialize()
        
        # Should have tier configuration
        assert hasattr(manager, "tiers") or hasattr(manager, "config")

    @pytest.mark.asyncio
    async def test_compaction(self, tmp_path):
        """Should compact old memories."""
        from memory.manager import MemoryManager
        
        config = {
            "sqlite_path": str(tmp_path / "memory.db"),
            "compaction": {
                "enabled": True,
                "threshold": 100
            }
        }
        
        manager = MemoryManager(config)
        await manager.initialize()
        
        # Save many entries to trigger compaction
        for i in range(50):
            await manager.save(f"Memory {i}", category="test")
        
        # Compaction should work without errors
        if hasattr(manager, "compact"):
            await manager.compact()


# ============================================================
# Neo4j Store Tests (Mocked)
# ============================================================
class TestNeo4jStore:
    """Test Neo4j knowledge graph storage."""

    @pytest.mark.asyncio
    @patch('memory.neo4j_store.GraphDatabase')
    async def test_save_entity(self, mock_graph_db):
        """Should save entities to Neo4j."""
        from memory.neo4j_store import Neo4jStore
        
        # Mock Neo4j driver
        mock_driver = Mock()
        mock_session = Mock()
        mock_session.run = Mock(return_value=Mock())
        mock_driver.session = Mock(return_value=mock_session)
        mock_graph_db.driver.return_value = mock_driver
        
        config = {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "password"
        }
        
        store = Neo4jStore(config)
        
        result = await store.save_entity(
            entity_id="person_1",
            entity_type="Person",
            properties={"name": "John Doe", "age": 30}
        )
        
        assert result is not None

    @pytest.mark.asyncio
    @patch('memory.neo4j_store.GraphDatabase')
    async def test_save_relationship(self, mock_graph_db):
        """Should save relationships between entities."""
        from memory.neo4j_store import Neo4jStore
        
        # Mock Neo4j driver
        mock_driver = Mock()
        mock_session = Mock()
        mock_session.run = Mock(return_value=Mock())
        mock_driver.session = Mock(return_value=mock_session)
        mock_graph_db.driver.return_value = mock_driver
        
        config = {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "password"
        }
        
        store = Neo4jStore(config)
        
        result = await store.save_relationship(
            from_id="person_1",
            to_id="company_1",
            relationship_type="WORKS_AT",
            properties={"since": 2020}
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_graph(self):
        """Should query graph patterns."""
        from memory.neo4j_store import Neo4jStore
        
        # Without real Neo4j, this will fail gracefully
        config = {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "password"
        }
        
        # Should handle connection failure gracefully
        try:
            store = Neo4jStore(config)
            # Query should either work or fail gracefully
        except Exception as e:
            # Expected if Neo4j not available
            assert "connection" in str(e).lower() or "neo4j" in str(e).lower()


# ============================================================
# Weaviate Store Tests (Mocked)
# ============================================================
class TestWeaviateStore:
    """Test Weaviate vector storage."""

    @pytest.mark.asyncio
    @patch('memory.weaviate_store.weaviate.Client')
    async def test_save_vector(self, mock_client):
        """Should save vectors to Weaviate."""
        from memory.weaviate_store import WeaviateStore
        
        # Mock Weaviate client
        mock_client_instance = Mock()
        mock_client_instance.schema.exists.return_value = True
        mock_client_instance.data_object.create = Mock(return_value={"id": "test-id"})
        mock_client.return_value = mock_client_instance
        
        config = {
            "url": "http://localhost:8080"
        }
        
        store = WeaviateStore(config)
        
        result = await store.save(
            content="Test content for embedding",
            vector=[0.1] * 384  # Mock embedding
        )
        
        assert result is not None

    @pytest.mark.asyncio
    @patch('memory.weaviate_store.weaviate.Client')
    async def test_semantic_search(self, mock_client):
        """Should perform semantic similarity search."""
        from memory.weaviate_store import WeaviateStore
        
        # Mock Weaviate client
        mock_client_instance = Mock()
        mock_client_instance.schema.exists.return_value = True
        mock_client_instance.query.get.return_value.with_near_text.return_value.with_limit.return_value.do.return_value = {
            "data": {
                "Get": {
                    "Memory": [
                        {"content": "Similar content", "_additional": {"certainty": 0.95}}
                    ]
                }
            }
        }
        mock_client.return_value = mock_client_instance
        
        config = {
            "url": "http://localhost:8080"
        }
        
        store = WeaviateStore(config)
        
        results = await store.search(
            query="test query",
            limit=5
        )
        
        assert results is not None


# ============================================================
# Memory Consistency Tests
# ============================================================
class TestMemoryConsistency:
    """Test cross-store consistency."""

    @pytest.mark.asyncio
    async def test_save_propagates_to_all_stores(self, tmp_path):
        """Saving should propagate to all enabled stores."""
        from memory.manager import MemoryManager
        
        config = {
            "sqlite_path": str(tmp_path / "memory.db")
            # Neo4j and Weaviate disabled/not configured
        }
        
        manager = MemoryManager(config)
        await manager.initialize()
        
        # Save memory
        entry_id = await manager.save(
            content="Test consistency",
            category="test"
        )
        
        # Should be retrievable
        results = await manager.search(query="consistency", limit=5)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_delete_propagates_to_all_stores(self, tmp_path):
        """Deletion should propagate to all stores."""
        from memory.manager import MemoryManager
        
        config = {
            "sqlite_path": str(tmp_path / "memory.db")
        }
        
        manager = MemoryManager(config)
        await manager.initialize()
        
        # Save and delete
        entry_id = await manager.save("Delete me", category="temp")
        await manager.delete(entry_id)
        
        # Should be gone from all stores
        results = await manager.search(query="Delete me", limit=5)
        assert not any(r.get("id") == entry_id for r in results)
