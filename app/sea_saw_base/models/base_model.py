"""
Base Model - Abstract base for all models with audit fields and soft-delete
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE

from ..manager import BaseModelManager


class BaseModel(SafeDeleteModel):
    """
    Abstract base model providing audit fields and soft-delete support.

    All Sea-Saw models should inherit from this base model to get:
    - Audit fields (owner, created_by, updated_by, created_at, updated_at)
    - Soft delete capability
    - Custom manager with user tracking
    """

    _safedelete_policy = SOFT_DELETE_CASCADE
    objects = BaseModelManager()

    owner = models.ForeignKey(
        "sea_saw_auth.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s",
        verbose_name=_("Owner"),
        help_text=_("The user who owns this object."),
    )

    created_by = models.ForeignKey(
        "sea_saw_auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_%(class)s",
        verbose_name=_("Created By"),
        help_text=_("The user who created this object."),
    )

    updated_by = models.ForeignKey(
        "sea_saw_auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_%(class)s",
        verbose_name=_("Updated By"),
        help_text=_("The user who last updated this object."),
    )

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
        abstract = True
        verbose_name = _("Base Model")
        verbose_name_plural = _("Base Models")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"
