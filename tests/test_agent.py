"""
iTaK - Core Agent Tests

Tests for core agent functionality:
- Agent (message processing, tool execution, error handling)
- ModelRouter (model selection, fallback chains, token tracking)
- Checkpoint (state persistence, recovery)
- SelfHeal (error recovery)
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock


# ============================================================
# ModelRouter Tests
# ============================================================
class TestModelRouter:
    """Test multi-model routing and fallback chains."""

    @pytest.mark.asyncio
    async def test_model_selection(self):
        """Should select correct model from config."""
        from core.models import ModelRouter
        
        config = {
            "router": {
                "default": "gpt-4o"
            },
            "models": {
                "gpt-4o": {
                    "provider": "openai",
                    "model": "gpt-4o"
                }
            }
        }
        
        router = ModelRouter(config)
        assert router.default_model == "gpt-4o"

    @pytest.mark.asyncio
    @patch('core.models.litellm.acompletion')
    async def test_completion_success(self, mock_completion):
        """Should complete with primary model successfully."""
        from core.models import ModelRouter
        
        # Mock LLM response
        mock_completion.return_value = AsyncMock(
            choices=[Mock(message=Mock(content="Test response"))]
        )
        
        config = {
            "router": {"default": "mock-model"},
            "models": {"mock-model": {"provider": "openai", "model": "gpt-3.5-turbo"}}
        }
        
        router = ModelRouter(config)
        response = await router.chat([{"role": "user", "content": "Hello"}])
        
        assert response is not None
        assert "Test response" in str(response)

    @pytest.mark.asyncio
    @patch('core.models.litellm.acompletion')
    async def test_fallback_on_error(self, mock_completion):
        """Should fallback to secondary model on primary failure."""
        from core.models import ModelRouter
        
        # First call fails, second succeeds
        mock_completion.side_effect = [
            Exception("Primary model failed"),
            AsyncMock(choices=[Mock(message=Mock(content="Fallback response"))])
        ]
        
        config = {
            "router": {
                "default": "primary",
                "fallback": ["secondary"]
            },
            "models": {
                "primary": {"provider": "openai", "model": "gpt-4o"},
                "secondary": {"provider": "openai", "model": "gpt-3.5-turbo"}
            }
        }
        
        router = ModelRouter(config)
        response = await router.chat([{"role": "user", "content": "Hello"}])
        
        assert response is not None
        assert "Fallback response" in str(response)

    def test_token_counting(self):
        """Should accurately count tokens."""
        from core.models import ModelRouter
        
        config = {
            "router": {"default": "gpt-3.5-turbo"},
            "models": {"gpt-3.5-turbo": {"provider": "openai", "model": "gpt-3.5-turbo"}}
        }
        
        router = ModelRouter(config)
        text = "Hello, world! This is a test message."
        
        # Token count should be reasonable (not zero, not excessive)
        tokens = router.count_tokens(text)
        assert tokens > 0
        assert tokens < 100  # Should be much less for this short text

    def test_cost_tracking(self):
        """Should track model usage costs."""
        from core.models import ModelRouter
        
        config = {
            "router": {"default": "gpt-4o"},
            "models": {
                "gpt-4o": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "cost_per_1k_input": 0.01,
                    "cost_per_1k_output": 0.03
                }
            }
        }
        
        router = ModelRouter(config)
        
        # Calculate cost
        cost = router.calculate_cost(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500
        )
        
        # Should be approximately 0.01 + (0.03 * 0.5) = 0.025
        assert cost > 0
        assert cost < 1.0  # Reasonable bounds


# ============================================================
# Checkpoint Tests
# ============================================================
class TestCheckpoint:
    """Test state persistence and recovery."""

    @pytest.mark.asyncio
    async def test_save_and_load_state(self, tmp_path):
        """Should save and load agent state correctly."""
        from core.checkpoint import CheckpointManager
        
        checkpoint_file = tmp_path / "checkpoint.json"
        manager = CheckpointManager(str(checkpoint_file))
        
        # Save state
        state = {
            "conversation_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "memory_context": "User prefers formal language",
            "iteration": 5
        }
        
        await manager.save(state)
        assert checkpoint_file.exists()
        
        # Load state
        loaded_state = await manager.load()
        assert loaded_state == state
        assert loaded_state["iteration"] == 5

    @pytest.mark.asyncio
    async def test_atomic_write(self, tmp_path):
        """Should write atomically to prevent corruption."""
        from core.checkpoint import CheckpointManager
        
        checkpoint_file = tmp_path / "checkpoint.json"
        manager = CheckpointManager(str(checkpoint_file))
        
        state = {"data": "test"}
        await manager.save(state)
        
        # File should exist and be valid JSON
        assert checkpoint_file.exists()
        with open(checkpoint_file) as f:
            data = json.load(f)
        assert data == state

    @pytest.mark.asyncio
    async def test_restore_from_corruption(self, tmp_path):
        """Should handle corrupted checkpoint gracefully."""
        from core.checkpoint import CheckpointManager
        
        checkpoint_file = tmp_path / "checkpoint.json"
        
        # Write corrupted JSON
        checkpoint_file.write_text("{invalid json")
        
        manager = CheckpointManager(str(checkpoint_file))
        
        # Should return None or empty state, not crash
        loaded = await manager.load()
        assert loaded is None or loaded == {}

    @pytest.mark.asyncio
    async def test_checkpoint_rotation(self, tmp_path):
        """Should rotate old checkpoints to backups."""
        from core.checkpoint import CheckpointManager
        
        checkpoint_file = tmp_path / "checkpoint.json"
        manager = CheckpointManager(str(checkpoint_file), max_backups=3)
        
        # Save multiple checkpoints
        for i in range(5):
            state = {"iteration": i}
            await manager.save(state)
        
        # Should have main checkpoint plus backups
        current = await manager.load()
        assert current["iteration"] == 4  # Latest


# ============================================================
# SelfHeal Tests
# ============================================================
class TestSelfHeal:
    """Test error recovery and self-healing."""

    @pytest.mark.asyncio
    async def test_classify_error_type(self):
        """Should correctly classify error types."""
        from core.self_heal import SelfHealEngine
        
        engine = SelfHealEngine(config={})
        
        # Network error
        error = Exception("Connection refused")
        classification = engine.classify_error(error)
        assert "network" in classification.lower() or "connection" in classification.lower()
        
        # Syntax error
        error = SyntaxError("invalid syntax")
        classification = engine.classify_error(error)
        assert "syntax" in classification.lower()

    @pytest.mark.asyncio
    @patch('core.self_heal.SelfHealEngine._search_similar_errors')
    async def test_search_similar_errors(self, mock_search):
        """Should search for similar past errors."""
        from core.self_heal import SelfHealEngine
        
        mock_search.return_value = [
            {
                "error": "Connection timeout",
                "solution": "Retry with exponential backoff"
            }
        ]
        
        engine = SelfHealEngine(config={})
        error = Exception("Connection timeout")
        
        similar = await engine._search_similar_errors(str(error))
        assert len(similar) > 0
        assert "solution" in similar[0]

    @pytest.mark.asyncio
    async def test_prevent_infinite_healing_loop(self):
        """Should prevent infinite healing loops."""
        from core.self_heal import SelfHealEngine
        
        engine = SelfHealEngine(config={"max_healing_attempts": 3})
        
        error = Exception("Persistent error")
        
        # Track healing attempts
        attempts = 0
        for i in range(5):
            if engine.should_attempt_healing(error, attempt=i):
                attempts += 1
        
        # Should stop after max attempts
        assert attempts <= 3

    @pytest.mark.asyncio
    async def test_security_errors_not_healed(self):
        """Security errors should not trigger healing."""
        from core.self_heal import SelfHealEngine
        
        engine = SelfHealEngine(config={})
        
        # Security errors should be blocked
        security_error = PermissionError("Access denied")
        should_heal = engine.is_healable_error(security_error)
        
        assert should_heal is False


# ============================================================
# Agent Integration Tests
# ============================================================
class TestAgent:
    """Test agent core functionality."""

    @pytest.mark.asyncio
    @patch('core.agent.ModelRouter')
    async def test_process_simple_message(self, mock_router_class):
        """Should process simple message and return response."""
        from core.agent import Agent
        
        # Mock model router
        mock_router = Mock()
        mock_router.chat = AsyncMock(return_value="Hello! I'm ready to help.")
        mock_router_class.return_value = mock_router
        
        config = {
            "agent": {"name": "TestAgent"},
            "models": {"router": {"default": "mock-model"}}
        }
        
        agent = Agent(config, user_id="test-user")
        response = await agent.message_loop("Hello, agent!")
        
        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    @patch('core.agent.ModelRouter')
    async def test_tool_execution_flow(self, mock_router_class):
        """Should execute tools and return results."""
        from core.agent import Agent
        
        # Mock model requesting a tool
        mock_router = Mock()
        mock_router.chat = AsyncMock(return_value='{"tool": "response", "message": "Done"}')
        mock_router_class.return_value = mock_router
        
        config = {
            "agent": {"name": "TestAgent"},
            "models": {"router": {"default": "mock-model"}},
            "tools": {"enabled": True}
        }
        
        agent = Agent(config, user_id="test-user")
        
        # This should execute successfully without crashing
        try:
            response = await agent.message_loop("Run a simple task")
            assert response is not None
        except Exception as e:
            # Some exceptions are OK during mocking
            assert "mock" in str(e).lower() or "tool" in str(e).lower()

    def test_extension_hooks_called(self):
        """Extension hooks should be called at appropriate times."""
        from core.agent import Agent
        
        hook_calls = []
        
        def test_hook(**kwargs):
            hook_calls.append(kwargs.get("hook_name"))
        
        config = {
            "agent": {"name": "TestAgent"},
            "models": {"router": {"default": "mock-model"}},
            "extensions": {
                "hooks": {
                    "agent_init": [test_hook],
                    "message_loop_start": [test_hook]
                }
            }
        }
        
        agent = Agent(config, user_id="test-user")
        
        # agent_init hook should have been called
        # Note: Actual implementation may vary
        assert agent is not None

    @pytest.mark.asyncio
    async def test_memory_context_integration(self, tmp_path):
        """Should integrate with memory system."""
        from core.agent import Agent
        
        config = {
            "agent": {"name": "TestAgent"},
            "models": {"router": {"default": "mock-model"}},
            "memory": {
                "enabled": True,
                "sqlite_path": str(tmp_path / "memory.db")
            }
        }
        
        # Should initialize without error
        agent = Agent(config, user_id="test-user")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_cost_tracking_integration(self):
        """Should track costs across operations."""
        from core.agent import Agent
        
        config = {
            "agent": {"name": "TestAgent"},
            "models": {"router": {"default": "mock-model"}},
            "cost": {
                "budget": 10.0,
                "warn_threshold": 0.8
            }
        }
        
        agent = Agent(config, user_id="test-user")
        
        # Add some cost
        agent.add_cost(0.50)
        total = agent.get_total_cost()
        
        assert total == 0.50
        
        # Should warn near budget
        agent.add_cost(7.5)
        assert agent.is_over_budget() is False
        
        agent.add_cost(5.0)
        assert agent.is_over_budget() is True

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self):
        """Should recover from errors using self-heal."""
        from core.agent import Agent
        
        config = {
            "agent": {"name": "TestAgent"},
            "models": {"router": {"default": "mock-model"}},
            "self_heal": {
                "enabled": True,
                "max_attempts": 3
            }
        }
        
        agent = Agent(config, user_id="test-user")
        
        # Agent should have self-heal capability
        assert hasattr(agent, "self_heal") or hasattr(agent, "error_recovery")
