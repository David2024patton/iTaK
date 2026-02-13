"""
iTaK Multi-User RBAC - 3-tier permission system.

Manages users, roles, and per-tool permission enforcement.
Users are identified by their platform IDs (Discord, Telegram, etc.)

Gameplan §25 - "Multi-User & Permissions"
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("itak.users")


# ── Permission Hierarchy ──────────────────────────────────────

ROLE_HIERARCHY = {
    "owner": 3,
    "sudo": 2,
    "user": 1,
}

# Minimum role required for each tool category
TOOL_PERMISSIONS = {
    # File operations - sudo+
    "write_file": "sudo",
    "edit_file": "sudo",
    "delete_file": "sudo",
    "create_file": "sudo",

    # Code execution - sudo+
    "bash_execute": "sudo",
    "code_execution": "sudo",
    "code_execution_tool": "sudo",

    # Memory writes - sudo+
    "memory_save": "sudo",
    "memory_forget": "sudo",
    "memory_delete": "sudo",

    # Config - owner only
    "config_update": "owner",
    "user_manage": "owner",
    "restart_agent": "owner",

    # Everything else - all users
    "web_search": "user",
    "memory_search": "user",
    "memory_load": "user",
    "browser_navigate": "user",
    "ask_user": "user",
    "response": "user",
    "call_subordinate": "user",
    "delegate_task": "user",
}


@dataclass
class User:
    """A registered user."""
    id: str
    name: str
    role: str                        # "owner", "sudo", "user"
    platforms: dict = field(default_factory=dict)  # {"discord": "123", "telegram": "456"}
    rate_limit: dict | None = None   # {"messages_per_hour": 100}
    active: bool = True

    @property
    def role_level(self) -> int:
        return ROLE_HIERARCHY.get(self.role, 1)


class UserRegistry:
    """
    Manage users and enforce permissions.

    Usage:
        registry = UserRegistry("data/users.json")
        user = registry.resolve("discord", "776628215066132502")
        if registry.check_permission(user, "bash_execute"):
            # allowed
    """

    def __init__(self, path: str = "data/users.json"):
        self.path = Path(path)
        self.users: dict[str, User] = {}
        self.unknown_user_role = "user"
        self.allow_unknown_users = False

        self._load()

    def _load(self):
        """Load user registry from JSON file."""
        if not self.path.exists():
            self._create_default()
            return

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))

            self.unknown_user_role = data.get("unknown_user_role", "user")
            self.allow_unknown_users = data.get("allow_unknown_users", False)

            for user_data in data.get("users", []):
                user = User(
                    id=user_data["id"],
                    name=user_data.get("name", user_data["id"]),
                    role=user_data.get("role", "user"),
                    platforms=user_data.get("platforms", {}),
                    rate_limit=user_data.get("rate_limit"),
                    active=user_data.get("active", True),
                )
                self.users[user.id] = user

            logger.info(
                f"User Registry: {len(self.users)} users loaded "
                f"({sum(1 for u in self.users.values() if u.role == 'owner')} owners, "
                f"{sum(1 for u in self.users.values() if u.role == 'sudo')} sudo, "
                f"{sum(1 for u in self.users.values() if u.role == 'user')} users)"
            )

        except Exception as e:
            logger.error(f"Failed to load user registry: {e}")
            self._create_default()

    def _create_default(self):
        """Create default user registry with David as owner."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

        default = {
            "users": [
                {
                    "id": "david",
                    "name": "David",
                    "role": "owner",
                    "platforms": {
                        "discord": "776628215066132502"
                    },
                    "rate_limit": None,
                    "active": True
                }
            ],
            "unknown_user_role": "user",
            "allow_unknown_users": False
        }

        self.path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        logger.info(f"Created default user registry at {self.path}")

        # Load the default
        self.users = {
            "david": User(
                id="david", name="David", role="owner",
                platforms={"discord": "776628215066132502"},
            )
        }
        self.unknown_user_role = "user"
        self.allow_unknown_users = False

    def _save(self):
        """Save user registry to disk."""
        data = {
            "users": [
                {
                    "id": u.id,
                    "name": u.name,
                    "role": u.role,
                    "platforms": u.platforms,
                    "rate_limit": u.rate_limit,
                    "active": u.active,
                }
                for u in self.users.values()
            ],
            "unknown_user_role": self.unknown_user_role,
            "allow_unknown_users": self.allow_unknown_users,
        }
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ── Resolution ─────────────────────────────────────────────

    def resolve(self, platform: str, platform_id: str) -> User | None:
        """
        Resolve a platform identity to a registered user.

        Args:
            platform: "discord", "telegram", "slack", "dashboard"
            platform_id: The platform-specific user ID

        Returns:
            User if found, or an "unknown" user if allowed, or None
        """
        for user in self.users.values():
            if not user.active:
                continue
            if user.platforms.get(platform) == platform_id:
                return user

        # Unknown user
        if self.allow_unknown_users:
            return User(
                id=f"unknown_{platform}_{platform_id}",
                name=f"Unknown ({platform})",
                role=self.unknown_user_role,
                platforms={platform: platform_id},
            )

        return None

    def resolve_by_id(self, user_id: str) -> User | None:
        """Resolve a user by internal ID."""
        return self.users.get(user_id)

    # ── Permission Checks ──────────────────────────────────────

    def check_permission(self, user: User | None, tool_name: str) -> bool:
        """
        Check if a user has permission to use a tool.

        Args:
            user: The resolved user (None = blocked)
            tool_name: Name of the tool to check

        Returns:
            True if allowed, False if denied
        """
        if user is None:
            return False

        required_role = TOOL_PERMISSIONS.get(tool_name, "user")
        required_level = ROLE_HIERARCHY.get(required_role, 1)

        return user.role_level >= required_level

    def get_denial_message(self, user: User | None, tool_name: str) -> str:
        """Get a friendly denial message for a permission failure."""
        if user is None:
            return "You are not authorized to interact with this agent."

        required = TOOL_PERMISSIONS.get(tool_name, "user")
        return (
            f"Sorry, you don't have permission to use `{tool_name}`. "
            f"This requires **{required}** role, but you have **{user.role}** role. "
            f"Ask the owner to upgrade your access!"
        )

    # ── CRUD ───────────────────────────────────────────────────

    def add_user(self, user_id: str, name: str, role: str = "user",
                 platforms: dict | None = None,
                 rate_limit: dict | None = None) -> User:
        """Add a new user."""
        if role not in ROLE_HIERARCHY:
            raise ValueError(f"Invalid role: {role}. Must be: {list(ROLE_HIERARCHY.keys())}")

        user = User(
            id=user_id,
            name=name,
            role=role,
            platforms=platforms or {},
            rate_limit=rate_limit,
        )
        self.users[user_id] = user
        self._save()
        logger.info(f"Added user: {name} ({role})")
        return user

    def remove_user(self, user_id: str) -> bool:
        """Remove a user."""
        if user_id in self.users:
            user = self.users.pop(user_id)
            self._save()
            logger.info(f"Removed user: {user.name}")
            return True
        return False

    def update_role(self, user_id: str, new_role: str) -> bool:
        """Update a user's role."""
        if user_id not in self.users:
            return False
        if new_role not in ROLE_HIERARCHY:
            raise ValueError(f"Invalid role: {new_role}")

        self.users[user_id].role = new_role
        self._save()
        logger.info(f"Updated {user_id} role to {new_role}")
        return True

    def list_users(self) -> list[dict]:
        """List all users as dicts."""
        return [
            {
                "id": u.id,
                "name": u.name,
                "role": u.role,
                "platforms": u.platforms,
                "rate_limit": u.rate_limit,
                "active": u.active,
            }
            for u in self.users.values()
        ]

    def get_stats(self) -> dict:
        """Get user registry stats."""
        return {
            "total_users": len(self.users),
            "owners": sum(1 for u in self.users.values() if u.role == "owner"),
            "sudos": sum(1 for u in self.users.values() if u.role == "sudo"),
            "users": sum(1 for u in self.users.values() if u.role == "user"),
            "allow_unknown": self.allow_unknown_users,
        }
