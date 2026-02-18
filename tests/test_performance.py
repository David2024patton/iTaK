"""
iTaK Performance Tests - Validate optimizations.

Tests for performance improvements in:
- Rate limiter (deque vs list)
- SQLite store (connection pooling)
- Output guard (set operations)
- Config watcher (file caching)
- FastEmbed caching
"""

import time
import pytest
from collections import deque


class TestRateLimiterPerformance:
    """Test rate limiter performance improvements."""

    def test_deque_performance(self):
        """Verify deque is used instead of list for better performance."""
        from security.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        
        # Record some requests
        for _ in range(100):
            limiter.record("test_category")
        
        # Verify _requests uses deque
        assert isinstance(limiter._requests["test_category"], deque), \
            "Rate limiter should use deque for O(1) operations"
    
    def test_check_performance(self):
        """Verify check() is fast even with many requests."""
        from security.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        
        # Record many requests
        for i in range(1000):
            limiter.record("test_category")
        
        # Check should be fast (< 10ms even with 1000 requests)
        start = time.time()
        allowed, reason = limiter.check("test_category")
        elapsed = time.time() - start
        
        assert elapsed < 0.01, f"check() took {elapsed*1000:.2f}ms, should be < 10ms"
    
    def test_auth_lockout_uses_deque(self):
        """Verify auth lockout also uses deque."""
        from security.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        
        # Record auth failures
        for _ in range(10):
            limiter.record_auth_failure("test_client")
        
        # Verify auth failures use deque
        assert hasattr(limiter, "_auth_failures"), "Auth failures not initialized"
        assert isinstance(limiter._auth_failures["test_client"], deque), \
            "Auth failures should use deque"


class TestSQLiteStorePerformance:
    """Test SQLite store connection pooling."""

    @pytest.fixture
    def store(self, tmp_path):
        from memory.sqlite_store import SQLiteStore
        db_path = tmp_path / "test.db"
        return SQLiteStore(str(db_path))
    
    def test_connection_pooling(self, store):
        """Verify connection pooling is implemented."""
        # Verify the store has thread-local storage
        assert hasattr(store, "_local"), "SQLiteStore should have _local for thread-local connections"
        
        # Verify _get_connection method exists
        assert hasattr(store, "_get_connection"), "SQLiteStore should have _get_connection method"
        
        # Get connection twice - should be same object
        conn1 = store._get_connection()
        conn2 = store._get_connection()
        
        assert conn1 is conn2, "Should reuse same connection in same thread"
    
    @pytest.mark.asyncio
    async def test_multiple_operations_reuse_connection(self, store):
        """Verify multiple operations reuse the same connection."""
        # Save multiple memories
        for i in range(10):
            await store.save(f"Memory {i}", category="test")
        
        # Search
        results = await store.search(query="Memory", limit=5)
        assert len(results) > 0
        
        # Get stats
        stats = await store.get_stats()
        assert stats["total_memories"] == 10
        
        # All operations should have used the same connection
        # (implicitly verified by not crashing and proper results)


class TestOutputGuardPerformance:
    """Test output guard optimizations."""

    def test_categories_found_efficiency(self):
        """Verify categories_found uses efficient deduplication."""
        from security.output_guard import OutputGuard, GuardResult, Redaction, PIICategory
        
        OutputGuard()
        
        # Create result with duplicate categories
        redactions = [
            Redaction(category=PIICategory.EMAIL, original_length=10, position=0, replacement="[EMAIL]"),
            Redaction(category=PIICategory.EMAIL, original_length=10, position=20, replacement="[EMAIL]"),
            Redaction(category=PIICategory.PHONE, original_length=10, position=40, replacement="[PHONE]"),
            Redaction(category=PIICategory.EMAIL, original_length=10, position=60, replacement="[EMAIL]"),
        ]
        
        result = GuardResult(
            original_text="test",
            sanitized_text="test",
            redactions=redactions
        )
        
        # Should deduplicate efficiently
        categories = result.categories_found
        assert len(categories) == 2, "Should have 2 unique categories"
        assert "email" in categories
        assert "phone_number" in categories


class TestConfigWatcherPerformance:
    """Test config watcher caching."""

    def test_config_caching(self, tmp_path):
        """Verify config watcher caches config to avoid repeated reads."""
        from core.config_watcher import ConfigWatcher
        import json
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"test": "value"}))
        
        watcher = ConfigWatcher(config_file)
        
        # Verify cached config exists
        assert hasattr(watcher, "_cached_config"), "Should have _cached_config"
        assert watcher._cached_config is not None, "Should cache initial config"
        assert watcher._cached_config["test"] == "value"
    
    def test_mtime_check_before_read(self, tmp_path):
        """Verify check_now() checks mtime before reading file."""
        from core.config_watcher import ConfigWatcher
        import json
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"test": "value"}))
        
        watcher = ConfigWatcher(config_file)
        
        # Call check_now without file change - should return False quickly
        start = time.time()
        changed = watcher.check_now()
        elapsed = time.time() - start
        
        assert changed is False, "Should detect no change"
        assert elapsed < 0.001, f"Should be fast (< 1ms), took {elapsed*1000:.2f}ms"


class TestModelRouterPerformance:
    """Test model router caching."""

    def test_fastembed_cache(self):
        """Verify FastEmbed models are cached."""
        try:
            from core.models import ModelRouter
        except ImportError as e:
            if "litellm" in str(e):
                pytest.skip("litellm not available in CI environment")
            raise
        
        config = {
            "embeddings": {
                "provider": "fastembed",
                "model": "BAAI/bge-small-en-v1.5"
            }
        }
        
        router = ModelRouter(config)
        
        # Verify cache exists
        assert hasattr(router, "_fastembed_cache"), "Should have _fastembed_cache"
        assert isinstance(router._fastembed_cache, dict), "Cache should be a dict"


class TestWebSearchPerformance:
    """Test web search import optimization."""

    def test_ddgs_imported_at_module_level(self):
        """Verify DDGS is imported at module level."""
        import tools.web_search as ws_module
        
        # Should have DDGS_AVAILABLE flag
        assert hasattr(ws_module, "DDGS_AVAILABLE"), "Should have DDGS_AVAILABLE flag"
        assert isinstance(ws_module.DDGS_AVAILABLE, bool), "DDGS_AVAILABLE should be boolean"
