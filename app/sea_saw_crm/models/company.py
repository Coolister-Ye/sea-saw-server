from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import BaseModel


class Company(BaseModel):
    """
    Represents a company entity with basic contact and address details.
    """

    company_name = models.CharField(
        max_length=255,
        verbose_name=_("Company Name"),
        help_text=_("The name of the company."),
    )

    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name=_("Email Address"),
        help_text=_("Contact email of the company."),
    )

    mobile = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Mobile Number"),
        help_text=_("The mobile phone number of the company."),
    )

    phone = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("The landline phone number of the company."),
    )

    address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Address"),
        help_text=_("The address of the company."),
    )

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ["company_name"]

    def __str__(self):
        return self.company_name or _("Unnamed Company")
