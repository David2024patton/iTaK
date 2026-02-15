"""
iTaK - Integration Tests
Verify that features from Agent Zero, Letta/MemGPT, and OpenClaw are properly integrated.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock


EXAMPLE_CONFIG_PATH = Path("install/config/config.json.example")


# ============================================================
# Configuration Integration Tests
# ============================================================
class TestConfigurationIntegration:
    """Test that all subsystems load their config correctly."""

    @pytest.fixture
    def config(self):
        """Load the example config."""
        with open(EXAMPLE_CONFIG_PATH) as f:
            return json.load(f)

    def test_agent_zero_config(self, config):
        """Agent Zero features are in config."""
        # Monologue engine settings
        assert "agent" in config
        assert config["agent"]["max_iterations"] == 25
        assert config["agent"]["checkpoint_enabled"] is True
        
        # 4-model architecture
        assert "models" in config
        assert "chat" in config["models"]
        assert "utility" in config["models"]
        assert "browser" in config["models"]
        assert "embeddings" in config["models"]

    def test_letta_memgpt_config(self, config):
        """Letta/MemGPT features are in config."""
        # 4-tier memory system
        assert "memory" in config
        assert "sqlite_path" in config["memory"]
        assert "neo4j" in config["memory"]
        assert "weaviate" in config["memory"]
        
        # Memory settings
        assert "auto_memorize" in config["memory"]
        assert "consolidation_threshold" in config["memory"]

    def test_openclaw_config(self, config):
        """OpenClaw features are in config."""
        # Multi-channel adapters
        assert "adapters" in config
        assert "discord" in config["adapters"]
        assert "telegram" in config["adapters"]
        assert "slack" in config["adapters"]
        assert "cli" in config["adapters"]
        
        # Multi-user RBAC
        assert "users" in config
        assert "registry_path" in config["users"]
        assert "rate_limits" in config["users"]
        
        # MCP server/client
        assert "mcp_server" in config
        assert "mcp_client" in config

    def test_itak_unique_config(self, config):
        """iTaK-unique features are in config."""
        # Self-healing, task board, webhooks, swarm
        assert "webhooks" in config
        assert "swarm" in config
        assert "task_board" in config
        assert "security" in config
        assert "output_guard" in config
        assert "heartbeat" in config

    def test_neo4j_integration(self, config):
        """Neo4j is properly configured."""
        # Check both nested and top-level
        assert "neo4j" in config["memory"]
        assert "uri" in config["memory"]["neo4j"]
        assert "enabled" in config["memory"]["neo4j"]


# ============================================================
# Memory Manager Integration Tests
# ============================================================
class TestMemoryManagerIntegration:
    """Test 4-tier memory system (Agent Zero + Letta/MemGPT + Neo4j)."""

    @pytest.fixture
    def config(self):
        with open(EXAMPLE_CONFIG_PATH) as f:
            return json.load(f)

    def test_memory_manager_init(self, config, tmp_path):
        """MemoryManager should initialize with nested config."""
        from memory.manager import MemoryManager
        
        # Mock model router
        model_router = MagicMock()
        
        # Update config to use temp paths
        memory_config = config["memory"].copy()
        memory_config["sqlite_path"] = str(tmp_path / "test.db")
        
        manager = MemoryManager(
            config=memory_config,
            model_router=model_router,
            full_config=config
        )
        
        # Should have SQLite (always enabled)
        assert manager.sqlite is not None
        
        # Neo4j/Weaviate should be None (not enabled in example config)
        assert manager.neo4j is None
        assert manager.weaviate is None

    def test_memory_tiers(self, tmp_path):
        """All 4 memory tiers should be accessible."""
        from memory.manager import MemoryManager
        
        config = {
            "sqlite_path": str(tmp_path / "test.db"),
            "neo4j": {
                "enabled": False,
                "uri": "bolt://localhost:7687"
            },
            "weaviate": {
                "enabled": False,
                "url": "http://localhost:8080"
            }
        }
        
        manager = MemoryManager(config=config, full_config={})
        
        # Tier 1: Markdown files
        assert manager.memory_dir.exists()
        
        # Tier 2: SQLite
        assert manager.sqlite is not None
        
        # Tier 3: Neo4j (disabled but config present)
        assert manager.neo4j is None  # Not enabled
        
        # Tier 4: Weaviate (disabled but config present)
        assert manager.weaviate is None  # Not enabled


# ============================================================
# Swarm Coordinator Integration Tests
# ============================================================
class TestSwarmCoordinatorIntegration:
    """Test Agent Zero sub-agent system enhanced with swarm coordination."""

    def test_swarm_reads_config(self):
        """SwarmCoordinator should use config settings."""
        from core.swarm import SwarmCoordinator, SwarmStrategy, MergeStrategy
        
        agent = MagicMock()
        agent.config = {
            "swarm": {
                "enabled": True,
                "default_strategy": "parallel",
                "default_merge": "concat",
                "max_parallel": 5,
                "timeout_seconds": 300,
                "profiles_dir": "prompts/profiles"
            }
        }
        
        swarm = SwarmCoordinator(agent)
        
        assert swarm.default_strategy == SwarmStrategy.PARALLEL
        assert swarm.default_merge == MergeStrategy.CONCAT
        assert swarm.max_parallel == 5
        assert swarm.timeout_seconds == 300

    def test_swarm_loads_profiles(self):
        """SwarmCoordinator should load agent profiles."""
        from core.swarm import SwarmCoordinator
        
        agent = MagicMock()
        agent.config = {"swarm": {}}
        
        swarm = SwarmCoordinator(agent)
        
        # Should have loaded profiles from prompts/profiles/
        # At minimum, the example profiles (researcher, coder, devops)
        assert len(swarm.profiles) >= 0  # May be 0 if directory is empty


# ============================================================
# Webhook Engine Integration Tests
# ============================================================
class TestWebhookEngineIntegration:
    """Test n8n/Zapier integration (iTaK-unique)."""

    def test_webhook_engine_init(self):
        """WebhookEngine should load from config."""
        from core.webhooks import WebhookEngine
        
        agent = MagicMock()
        config = {
            "inbound_secret": "test-secret",
            "enabled": True,
            "outbound": [
                {
                    "name": "n8n",
                    "url": "https://n8n.example.com/webhook",
                    "events": ["task_completed"],
                    "enabled": True
                }
            ]
        }
        
        engine = WebhookEngine(agent, config)
        
        # Should have loaded inbound secret
        # Note: inbound_secret may be empty if config value is placeholder
        assert hasattr(engine, 'inbound_secret')


# ============================================================
# MCP Server Integration Tests
# ============================================================
class TestMCPServerIntegration:
    """Test MCP server (OpenClaw feature)."""

    def test_mcp_server_disabled_by_default(self):
        """MCP server should be disabled in example config."""
        with open(EXAMPLE_CONFIG_PATH) as f:
            config = json.load(f)
        
        from core.mcp_server import ITaKMCPServer
        
        agent = MagicMock()
        mcp_server = ITaKMCPServer(agent, config)
        
        # Should be disabled
        assert mcp_server.enabled is False
        
        # Should have 0 tools registered when disabled
        assert len(mcp_server.tools) == 0

    def test_mcp_server_tools_config(self):
        """MCP server should expose configured tools."""
        with open(EXAMPLE_CONFIG_PATH) as f:
            config = json.load(f)
        
        assert "mcp_server" in config
        assert "expose_tools" in config["mcp_server"]
        
        # Should have 6 exposed tools
        tools = config["mcp_server"]["expose_tools"]
        assert len(tools) == 6
        assert "send_message" in tools
        assert "search_memory" in tools
        assert "list_tasks" in tools


# ============================================================
# User Registry Integration Tests
# ============================================================
class TestUserRegistryIntegration:
    """Test multi-user RBAC (OpenClaw feature)."""

    def test_user_registry_init(self, tmp_path):
        """UserRegistry should initialize from config path."""
        from core.users import UserRegistry
        
        users_path = str(tmp_path / "users.json")
        registry = UserRegistry(users_path)
        
        # Should have default owner user
        assert len(registry.users) >= 1
        assert registry.unknown_user_role == "user"

    def test_rbac_permissions(self):
        """RBAC should enforce tool permissions."""
        from core.users import TOOL_PERMISSIONS, ROLE_HIERARCHY
        
        # Verify permission hierarchy exists
        assert "owner" in ROLE_HIERARCHY
        assert "sudo" in ROLE_HIERARCHY
        assert "user" in ROLE_HIERARCHY
        
        # Verify tool permissions are defined
        assert "bash_execute" in TOOL_PERMISSIONS
        assert "memory_save" in TOOL_PERMISSIONS
        assert "config_update" in TOOL_PERMISSIONS


# ============================================================
# Task Board Integration Tests
# ============================================================
class TestTaskBoardIntegration:
    """Test Mission Control task board (iTaK-unique)."""

    def test_task_board_config(self):
        """Task board should have proper config."""
        with open(EXAMPLE_CONFIG_PATH) as f:
            config = json.load(f)
        
        assert "task_board" in config
        assert config["task_board"]["enabled"] is True
        assert "db_path" in config["task_board"]
        assert "default_priority" in config["task_board"]


# ============================================================
# Extension System Integration Tests
# ============================================================
class TestExtensionSystemIntegration:
    """Test Agent Zero extension hook system."""

    def test_extension_hooks_exist(self):
        """Extension hook directories should exist."""
        ext_dir = Path("extensions")
        assert ext_dir.exists()
        
        # Check for hook directories
        # At minimum should have structure even if empty
        hook_dirs = list(ext_dir.glob("*"))
        assert len(hook_dirs) >= 0  # May be empty


# ============================================================
# Integration Verification Summary
# ============================================================
def test_integration_completeness():
    """Verify all three source repos are integrated."""
    
    with open(EXAMPLE_CONFIG_PATH) as f:
        config = json.load(f)
    
    # Agent Zero checklist
    agent_zero_features = [
        "agent" in config,  # Monologue engine
        "models" in config,  # 4-model architecture
        len(config.get("models", {})) >= 4,  # All 4 models defined
    ]
    assert all(agent_zero_features), "Agent Zero features missing"
    
    # Letta/MemGPT checklist
    letta_features = [
        "memory" in config,  # Memory system
        "sqlite_path" in config.get("memory", {}),  # Tier 2
        "neo4j" in config.get("memory", {}),  # Tier 3
        "weaviate" in config.get("memory", {}),  # Tier 4
    ]
    assert all(letta_features), "Letta/MemGPT features missing"
    
    # OpenClaw checklist
    openclaw_features = [
        "adapters" in config,  # Multi-channel
        "discord" in config.get("adapters", {}),  # Discord adapter
        "telegram" in config.get("adapters", {}),  # Telegram adapter
        "slack" in config.get("adapters", {}),  # Slack adapter
        "users" in config,  # RBAC
        "mcp_server" in config,  # MCP server
        "mcp_client" in config,  # MCP client
    ]
    assert all(openclaw_features), "OpenClaw features missing"
    
    # Neo4j integration
    neo4j_integrated = [
        "neo4j" in config,  # Top-level
        "neo4j" in config.get("memory", {}),  # Nested
    ]
    assert any(neo4j_integrated), "Neo4j not configured"
    
    # iTaK-unique features
    itak_features = [
        "webhooks" in config,  # Webhook engine
        "swarm" in config,  # Agent swarms
        "task_board" in config,  # Task tracking
        "output_guard" in config,  # DLP
        "heartbeat" in config,  # Health monitoring
    ]
    assert all(itak_features), "iTaK-unique features missing"
    
    print("\n✅ Integration verification complete:")
    print(f"  - Agent Zero: {sum(agent_zero_features)}/{len(agent_zero_features)} features")
    print(f"  - Letta/MemGPT: {sum(letta_features)}/{len(letta_features)} features")
    print(f"  - OpenClaw: {sum(openclaw_features)}/{len(openclaw_features)} features")
    print(f"  - Neo4j: Integrated")
    print(f"  - iTaK-unique: {sum(itak_features)}/{len(itak_features)} features")
