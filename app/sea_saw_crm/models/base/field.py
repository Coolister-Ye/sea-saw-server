"""
Field Model - Metadata definition for dynamic fields
"""
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base_model import BaseModel


class FieldType(models.TextChoices):
    PICKLIST = "picklist", _("Picklist")
    TEXT = "text", _("Text")
    NUMERICAL = "numerical", _("Numerical")
    LOOKUP = "lookup", _("Lookup")
    DATE = "date", _("Date")
    CURRENCY = "currency", _("Currency")
    EMAIL = "email", _("Email")
    PHONE = "phone", _("Phone")
    URL = "url", _("URL")


class Field(BaseModel):
    """
    Metadata definition of a field belonging to a given ContentType model.
    """

    field_name = models.CharField(
        max_length=50,
        verbose_name=_("Field Name"),
        help_text=_("Unique name of the field within the same content type."),
    )

    field_type = models.CharField(
        max_length=50,
        choices=FieldType.choices,
        default=FieldType.TEXT,
        verbose_name=_("Field Type"),
        help_text=_("Type of this field, e.g., text, picklist, date."),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether the field is active."),
    )

    is_mandatory = models.BooleanField(
        default=False,
        verbose_name=_("Is Mandatory"),
        help_text=_("Whether this field is required."),
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("Content Type"),
        help_text=_("The model that this field belongs to."),
    )

    extra_info = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Extra Information"),
        help_text=_("Optional metadata, e.g., picklist choices."),
    )

    class Meta:
        ordering = ["id"]
        verbose_name = _("Field")
        verbose_name_plural = _("Fields")
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "field_name"],
                name="unique_field_per_content_type",
            )
        ]

    def __str__(self):
        return self.field_name

    def clean(self):
        """
        Custom validation logic.
        Ensures PICKLIST type fields contain picklist choices.
        """
        super().clean()

        if self.field_type == FieldType.PICKLIST and not self.extra_info:
            raise ValidationError(
                {
                    "extra_info": _(
                        "Picklist fields must define extra_info (e.g., picklist choices)."
                    )
                }
            )
