from django.apps import AppConfig


class SeaSawPreferenceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sea_saw_preference"

    def ready(self):
        from django.db.models.signals import post_migrate
        from sea_saw_preference.seeds import seed_custom_views

        post_migrate.connect(seed_custom_views, sender=self)
