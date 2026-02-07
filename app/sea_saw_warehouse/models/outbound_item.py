"""
Outbound Item Model
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from sea_saw_base.models import AbstarctItemBase
from sea_saw_sales.models import OrderItem
from sea_saw_production.models import ProductionItem
from .outbound_order import OutboundOrder


class OutboundItem(AbstarctItemBase):
    """
    出仓明细：记录实际出货数量，可关联销售订单明细或生产明细
    """

    outbound_order = models.ForeignKey(
        OutboundOrder,
        on_delete=models.CASCADE,
        related_name="outbound_items",
        verbose_name=_("Outbound Order"),
    )

    # 销售订单明细
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="outbound_items",
        verbose_name=_("Order Item"),
        help_text=_("The sales order item associated with this outbound item."),
    )

    # 生产单明细
    production_item = models.ForeignKey(
        ProductionItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="outbound_items",
        verbose_name=_("Production Item"),
        help_text=_("The production item associated with this outbound item."),
    )

    outbound_qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Outbound Quantity"),
        help_text=_("Outbound quantity (cartons / pieces)."),
    )

    outbound_net_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Outbound Net Weight"),
    )

    outbound_gross_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Outbound Gross Weight"),
    )

    class Meta:
        verbose_name = _("Outbound Item")
        verbose_name_plural = _("Outbound Items")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["outbound_qty"]),
        ]

    def __str__(self):
        target = self.order_item or self.production_item or _("Unknown Item")
        return f"{target} - {self.outbound_qty}"
