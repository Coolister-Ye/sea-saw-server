from django.apps import AppConfig


class SeaSawCrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sea_saw_crm"

    def ready(self):
        # Import signals to register them
        from . import signals  # noqa: F401
