from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomView(models.Model):
    class VisibilityChoice(models.TextChoices):
        PRIVATE = "private", _("Private")
        SHARED = "shared", _("Shared")
        PUBLIC = "public", _("Public")

    owner = models.ForeignKey(
        "sea_saw_auth.User",
        on_delete=models.CASCADE,
        related_name="custom_views",
        verbose_name=_("Owner"),
        null=True,
        blank=True,
    )
    entity = models.CharField(max_length=100, verbose_name=_("Entity"))
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    # Stable slug for system views (e.g. "all", "pending") — empty for user views
    key = models.CharField(max_length=100, blank=True, default="", verbose_name=_("Key"))
    is_system = models.BooleanField(default=False, verbose_name=_("Is system"))
    params = models.JSONField(default=dict, verbose_name=_("Filter params"))
    column_order = models.JSONField(
        default=list,
        verbose_name=_("Column order"),
        help_text=_("Ordered list of visible column field names. Empty list means use page default."),
    )
    visibility = models.CharField(
        max_length=10,
        choices=VisibilityChoice.choices,
        default=VisibilityChoice.PRIVATE,
        verbose_name=_("Visibility"),
    )
    shared_users = models.ManyToManyField(
        "sea_saw_auth.User",
        blank=True,
        related_name="shared_custom_views",
        verbose_name=_("Shared with users"),
    )
    shared_roles = models.ManyToManyField(
        "sea_saw_auth.Role",
        blank=True,
        related_name="shared_custom_views",
        verbose_name=_("Shared with roles"),
    )
    is_default = models.BooleanField(default=False, verbose_name=_("Is default"))
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("Timestamp when this object was created."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Timestamp when this object was last updated."),
    )

    class Meta:
        constraints = [
            # At most one default view per owner+entity (user views only)
            models.UniqueConstraint(
                fields=["owner", "entity"],
                condition=models.Q(is_default=True, is_system=False),
                name="unique_default_view_per_owner_entity",
            ),
            # User views: unique name per owner+entity
            models.UniqueConstraint(
                fields=["owner", "entity", "name"],
                condition=models.Q(is_system=False),
                name="unique_custom_view_name_per_owner_entity",
            ),
            # System views: unique by entity+key
            models.UniqueConstraint(
                fields=["entity", "key"],
                condition=models.Q(is_system=True),
                name="unique_system_view_entity_key",
            ),
        ]

    def __str__(self):
        return f"[{self.visibility}] {self.entity}/{self.name} ({self.owner})"
