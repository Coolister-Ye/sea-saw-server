from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .base import BaseModel
from .company import Company


class Contact(BaseModel):
    """
    Represents a contact person with personal and communication details.
    Supports additional custom attributes via JSON.
    """

    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Name"),
        help_text=_("Full name of the contact."),
    )

    title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Job Title"),
        help_text=_("The position or title of the contact."),
    )

    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name=_("Email"),
        help_text=_("Email address of the contact."),
    )

    mobile = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Mobile Number"),
        help_text=_("Mobile phone number of the contact."),
    )

    phone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("Landline phone number of the contact."),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts",
        verbose_name=_("Company"),
        help_text=_("The company associated with this contact."),
    )

    class Meta:
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")
        ordering = ["name", "email"]
        unique_together = ("email", "deleted")  # Soft delete support

    def __str__(self):
        return self.name or _("Unnamed Contact")

    def clean(self):
        """
        Custom validation:
        At least one of email or phone must be provided.
        """
        super().clean()

        if not self.email and not self.phone:
            raise ValidationError(
                _("At least one contact method is required: email or phone.")
            )
