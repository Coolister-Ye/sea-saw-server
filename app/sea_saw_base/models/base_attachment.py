"""
Base Attachment Model - Abstract base for all attachment types
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base_model import BaseModel


class BaseAttachment(BaseModel):
    """
    Abstract base model for all attachment types.
    Provides common fields for file storage and metadata.
    """

    file = models.FileField(
        verbose_name=_("File"),
        help_text=_("Upload file. Files are organized by date with unique names."),
    )

    file_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("File Name"),
        help_text=_("Original filename for display purposes."),
    )

    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("File Size (bytes)"),
    )

    description = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Optional description of the file."),
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return self.file_name or f"Attachment #{self.pk}"

    def save(self, *args, **kwargs):
        """Auto-populate file_name and file_size"""
        if self.file and not self.file_name:
            import os
            self.file_name = os.path.basename(self.file.name)

        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass

        super().save(*args, **kwargs)
