"""
Production Item Model
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ..base import AbstarctItemBase
from ..order import OrderItem
from .production_order import ProductionOrder


class ProductionItem(AbstarctItemBase):
    """
    生产单明细：每个明细对应销售订单的一条 item，
    记录计划生产数量与实际产量。
    """

    production_order = models.ForeignKey(
        ProductionOrder,
        on_delete=models.CASCADE,
        related_name="production_items",
        verbose_name=_("Production Order"),
    )

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="production_items",
        verbose_name=_("Related Order Item"),
        help_text=_("The sales order item linked to this production item."),
    )

    # Quantity
    planned_qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Planned Quantity"),
    )

    produced_qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Produced Quantity"),
        help_text=_("Total actual produced quantity."),
    )

    produced_net_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Outbound Net Weight"),
    )

    produced_gross_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Outbound Gross Weight"),
    )

    class Meta:
        verbose_name = _("Production Item")
        verbose_name_plural = _("Production Items")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["production_order"]),
        ]

    def __str__(self):
        return f"ProductionItem #{self.pk}"

    @property
    def progress_rate(self):
        """
        Return production completion rate (percentage).
        Auto-handle zero or null planned quantity.
        """
        if not self.planned_qty or float(self.planned_qty) == 0:
            return 0.0
        return round(float(self.produced_qty / self.planned_qty * 100), 2)
