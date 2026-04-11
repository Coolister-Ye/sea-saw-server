from django.db import models
from django.utils.translation import gettext_lazy as _


class UserFilterPreset(models.Model):
    PRESET_TYPE_SYSTEM = "system"
    PRESET_TYPE_USER = "user"
    PRESET_TYPE_CHOICES = [
        (PRESET_TYPE_SYSTEM, _("System")),
        (PRESET_TYPE_USER, _("User")),
    ]

    # System presets have user=None; user presets are owned by a specific user
    user = models.ForeignKey(
        "sea_saw_auth.User",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        null=True,
        blank=True,
    )
    entity = models.CharField(max_length=100, verbose_name=_("Entity"))
    name = models.CharField(max_length=100, verbose_name=_("Preset name"))
    # Stable slug for system presets (e.g. "all", "pending") so the frontend
    # can reference them by a fixed key regardless of database id.
    key = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name=_("Key"),
    )
    params = models.JSONField(verbose_name=_("Filter params"))
    preset_type = models.CharField(
        max_length=10,
        choices=PRESET_TYPE_CHOICES,
        default=PRESET_TYPE_USER,
        verbose_name=_("Preset type"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created At"), help_text=_("Timestamp when this object was created.")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Updated At"), help_text=_("Timestamp when this object was last updated.")
    )

    class Meta:
        constraints = [
            # Each user can only have one preset with a given name per entity
            models.UniqueConstraint(
                fields=["user", "entity", "name"],
                condition=models.Q(preset_type="user"),
                name="unique_user_entity_preset_name",
            ),
            # System presets are unique by entity + key
            models.UniqueConstraint(
                fields=["entity", "key"],
                condition=models.Q(preset_type="system"),
                name="unique_system_entity_key",
            ),
        ]

    def __str__(self):
        owner = self.user.username if self.user else "system"
        return f"[{self.preset_type}] {self.entity} / {self.name} ({owner})"
