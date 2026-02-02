"""
AbstractOrderBase - Common fields shared by Order-like models
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base_model import BaseModel
from .enums import ShipmentTermType, CurrencyType, IncoTermsType


class AbstractOrderBase(BaseModel):
    """
    Common fields shared by Order-like models (Order, PurchaseOrder, etc.)

    Includes:
    - Logistics information (ETD, ports, shipment terms)
    - Finance information (currency, deposit, balance, total amount)
    - Additional comments
    """

    etd = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("ETD"),
        help_text=_("Estimated time of departure."),
    )

    # Logistic Info
    loading_port = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default="Any port of CHINA",
        verbose_name=_("Loading Port"),
    )

    destination_port = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Destination Port"),
    )

    shipment_term = models.CharField(
        max_length=20,
        choices=ShipmentTermType.choices,
        null=True,
        blank=True,
        verbose_name=_("Shipment Term"),
    )

    # Finance
    inco_terms = models.CharField(
        max_length=15,
        choices=IncoTermsType.choices,
        null=True,
        blank=True,
        verbose_name=_("Inco Terms"),
    )

    currency = models.CharField(
        max_length=10,
        choices=CurrencyType.choices,
        null=True,
        blank=True,
        verbose_name=_("Currency"),
    )

    deposit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Deposit"),
    )

    balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Balance"),
    )

    total_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Total Amount"),
    )

    comment = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Comment"),
    )

    class Meta:
        abstract = True
