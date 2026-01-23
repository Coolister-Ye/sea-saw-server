"""
Order Item Model
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ..base import AbstarctItemBase
from .order import Order


class OrderItem(AbstarctItemBase):
    """
    Order line item:
    Product + packaging + weights + pricing.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name=_("Order"),
    )

    # Quantity
    order_qty = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Order Quantity"),
    )

    total_gross_weight = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Total Gross Weight"),
    )

    total_net_weight = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Total Net Weight"),
    )

    # Finance
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Unit Price"),
    )

    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Total Price"),
    )

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["product_name"]),
        ]

    def __str__(self):
        return self.product_name or _("Unnamed Item")

    def save(self, *args, **kwargs):
        """计算净重、总重、总价"""
        if self.glazing and self.gross_weight:
            self.net_weight = self.gross_weight * (1 - self.glazing)

        if self.net_weight and self.order_qty:
            self.total_net_weight = self.net_weight * self.order_qty

        if self.gross_weight and self.order_qty:
            self.total_gross_weight = self.gross_weight * self.order_qty

        if self.unit_price and self.total_gross_weight:
            self.total_price = self.unit_price * self.total_gross_weight

        super().save(*args, **kwargs)

        # auto update total_amount after item save
        if self.order_id:
            self.order.update_total_amount()
