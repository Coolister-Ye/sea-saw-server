from django.db import models
from django.utils.translation import gettext_lazy as _


class UserColumnPreference(models.Model):
    user = models.ForeignKey("sea_saw_auth.User", on_delete=models.CASCADE, verbose_name=_("User"))
    table_name = models.CharField(max_length=100, verbose_name=_("Table name"))
    column_pref = models.JSONField(verbose_name=_("Column preference"))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created At"), help_text=_("Timestamp when this object was created.")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Updated At"), help_text=_("Timestamp when this object was last updated.")
    )
