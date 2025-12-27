from django.apps import AppConfig
from django.db.models.signals import post_migrate


class SeaSawAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sea_saw_auth"

    def ready(self):
        # Avoid duplicate signal registration in autoreload
        if hasattr(self, "already_registered"):
            return
        post_migrate.connect(add_default_roles, sender=self)
        self.already_registered = True


def add_default_roles(sender, **kwargs):
    """Add default roles to database on startup."""
    from .models import Role

    default_roles = [
        {
            "role_name": "ADMIN",
            "defaults": {
                "is_peer_visible": True,
                "role_type": "ADMIN",
                "description": "Users with this role have access to the data owned by all other users.",
                "parent": None,
            },
        },
        {
            "role_name": "UNKOWN",
            "defaults": {
                "is_peer_visible": False,
                "role_type": "UNKNOWN",
                "description": "Users belonging to this role cannot see data for admin users.",
                # parent will be set after creating admin role
            },
        },
    ]

    # Create or update admin role
    admin_role, _ = Role.objects.get_or_create(
        role_name=default_roles[0]["role_name"],
        defaults=default_roles[0]["defaults"],
    )

    # Ensure parent field is correct for "unkown user"
    normal_user_defaults = default_roles[1]["defaults"].copy()
    normal_user_defaults["parent"] = admin_role

    Role.objects.get_or_create(
        role_name=default_roles[1]["role_name"],
        defaults=normal_user_defaults,
    )
