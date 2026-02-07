from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SeaSawSalesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sea_saw_sales"
    verbose_name = _("Sea-Saw Sales")
