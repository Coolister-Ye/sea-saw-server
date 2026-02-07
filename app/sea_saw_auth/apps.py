
import logging
from django.apps import AppConfig
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)


class SeaSawAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sea_saw_auth"

    def ready(self):
        """Initialize app and register signal handlers."""
        # Avoid duplicate signal registration during autoreload
        if hasattr(self, "_signals_registered"):
            return

        post_migrate.connect(add_default_roles, sender=self)
        self._signals_registered = True


# Role configuration constants
class RoleConfig:
    """Default role configurations for the system."""

    ADMIN = {
        "role_name": "ADMIN",
        "role_type": "ADMIN",
        "is_peer_visible": True,
        "description": "Users with this role have access to the data owned by all other users.",
        "parent": None,
    }

    UNKNOWN = {
        "role_name": "UNKNOWN",
        "role_type": "UNKNOWN",
        "is_peer_visible": False,
        "description": "Users belonging to this role cannot see data for admin users.",
    }

    SALES = {
        "role_name": "SALES",
        "role_type": "SALE",
        "is_peer_visible": False,
        "description": "SALE users can only see their own data.",
    }

    SALES_MANAGER = {
        "role_name": "SALES MANAGER",
        "role_type": "SALE",
        "is_peer_visible": True,
        "description": "SALE MANAGER users can see all data.",
    }

    PRODUCTION = {
        "role_name": "PRODUCTION",
        "role_type": "PRODUCTION",
        "is_peer_visible": False,
        "description": "PRODUCTION users can only see their own data.",
    }

    PRODUCTION_MANAGER = {
        "role_name": "PRODUCTION MANAGER",
        "role_type": "PRODUCTION",
        "is_peer_visible": True,
        "description": "PRODUCTION MANAGER users can see all data.",
    }

    WAREHOUSE = {
        "role_name": "WAREHOUSE",
        "role_type": "WAREHOUSE",
        "is_peer_visible": False,
        "description": "WAREHOUSE users can only see their own data.",
    }

    WAREHOUSE_MANAGER = {
        "role_name": "WAREHOUSE MANAGER",
        "role_type": "WAREHOUSE",
        "is_peer_visible": True,
        "description": "WAREHOUSE MANAGER users can see all data.",
    }

    @classmethod
    def get_all_roles(cls):
        """
        Get all role configurations.
        Returns list of (config_dict, needs_parent) tuples.
        """
        return [
            (cls.ADMIN, False),
            (cls.UNKNOWN, True),
            (cls.SALES, True),
            (cls.SALES_MANAGER, True),
            (cls.PRODUCTION, True),
            (cls.PRODUCTION_MANAGER, True),
            (cls.WAREHOUSE, True),
            (cls.WAREHOUSE_MANAGER, True),
        ]


def add_default_roles(sender, **kwargs):  # noqa: ARG001
    """
    Add default roles to database after migration.

    This function is called automatically after running migrations to ensure
    all required default roles exist in the database.

    Args:
        sender: The AppConfig that sent the signal (unused but required by Django)
        **kwargs: Additional keyword arguments from the signal (unused)
    """
    from .models import Role

    logger.info("Initializing default roles...")

    # Step 1: Create ADMIN role (parent of all other roles)
    admin_config = RoleConfig.ADMIN.copy()
    admin_role, admin_created = Role.objects.get_or_create(
        role_name=admin_config["role_name"],
        defaults=admin_config,
    )

    if admin_created:
        logger.info(f"Created ADMIN role: {admin_role}")
    else:
        logger.debug(f"ADMIN role already exists: {admin_role}")

    # Step 2: Create all other roles with ADMIN as parent
    roles_to_create = RoleConfig.get_all_roles()
    created_count = 0

    for role_config, needs_parent in roles_to_create:
        # Skip ADMIN since we already created it
        if role_config["role_name"] == "ADMIN":
            continue

        # Prepare role data
        role_data = role_config.copy()
        if needs_parent:
            role_data["parent"] = admin_role

        # Create or get role
        role, created = Role.objects.get_or_create(
            role_name=role_data["role_name"],
            defaults=role_data,
        )

        if created:
            created_count += 1
            logger.info(f"Created role: {role.role_name} (type: {role.role_type})")
        else:
            logger.debug(f"Role already exists: {role.role_name}")

    # Summary
    total_roles = Role.objects.count()
    logger.info(
        f"Default roles initialization complete. "
        f"Created: {created_count + (1 if admin_created else 0)}, "
        f"Total: {total_roles}"
    )
