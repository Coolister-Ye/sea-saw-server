"""
Base Product Item Model
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

from .base_model import BaseModel
from .enums import UnitType


class AbstarctItemBase(BaseModel):
    """
    Abstract base for item models (OrderItem, ProductionItem, etc.)

    Contains common fields for:
    - Product information (name, specification, packaging, size)
    - Weight information (gross weight, net weight, glazing)
    - Unit type

    Note: Spelling "Abstarct" is intentional to match existing code.
    """

    # Product Info
    product_name = models.CharField(
        max_length=200,
        verbose_name=_("Product Name"),
    )

    specification = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name=_("Specification"),
    )

    outter_packaging = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Outter Packaging"),
    )

    inner_packaging = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Inner Packaging"),
    )

    size = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Size"),
    )

    unit = models.CharField(
        max_length=20,
        choices=UnitType.choices,
        default=UnitType.KGS,
        verbose_name=_("Unit"),
    )

    glazing = models.DecimalField(
        max_digits=5,
        decimal_places=5,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("1")),
        ],
        verbose_name=_("Glazing (%)"),
    )

    gross_weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Gross Weight"),
    )

    net_weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Net Weight"),
    )

    class Meta:
        abstract = True
