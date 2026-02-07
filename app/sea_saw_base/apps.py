from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SeaSawBaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sea_saw_base"
    verbose_name = _("Sea-Saw Base")

    def ready(self):
        # Import signals to register them
        from . import signals  # noqa: F401
