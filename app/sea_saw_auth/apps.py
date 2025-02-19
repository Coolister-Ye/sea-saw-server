from django.apps import AppConfig
from django.db.models.signals import post_migrate


class SeaSawAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sea_saw_auth"

    def ready(self):
        # Connect the signal to the add_default_roles function
        post_migrate.connect(add_default_roles, sender=self)


def add_default_roles(sender, **kwargs):
    from .models import Role

    # Get or create the 'admin' role
    admin_role, created = Role.objects.get_or_create(
        name="admin",
        is_peer_visible=True,
        description="Users with this role have access to the data owned by all other users.",
    )

    # Get or create the 'normal user' role, setting the parent as the 'admin' role
    Role.objects.get_or_create(
        name="normal user",
        parent=admin_role,  # Use the admin_role instance directly
        is_peer_visible=False,
        description="Users belonging to this role cannot see data for admin users.",
    )
