"""
Purchase Item Model
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ..base import AbstarctItemBase
from ..order import OrderItem
from .purchase_order import PurchaseOrder


class PurchaseItem(AbstarctItemBase):
    """
    Purchase Order Item - Details of products being purchased
    """

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="purchase_items",
        verbose_name=_("Purchase Order"),
    )

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_items",
        verbose_name=_("Related Order Item"),
        help_text=_("The order item this purchase is for."),
    )

    # Quantity
    purchase_qty = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Purchase Quantity"),
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
        help_text=_("Purchase price per unit."),
    )

    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Total Price"),
        help_text=_("Total price for this item."),
    )

    class Meta:
        verbose_name = _("Purchase Item")
        verbose_name_plural = _("Purchase Items")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["product_name"]),
        ]

    def __str__(self):
        return f"{self.product_name} - {self.purchase_qty}{self.unit}"

    def save(self, *args, **kwargs):
        """计算净重、总重、总价"""
        if self.glazing and self.gross_weight:
            self.net_weight = self.gross_weight * (1 - self.glazing)

        if self.net_weight and self.purchase_qty:
            self.total_net_weight = self.net_weight * self.purchase_qty

        if self.gross_weight and self.purchase_qty:
            self.total_gross_weight = self.gross_weight * self.purchase_qty

        if self.unit_price and self.total_gross_weight:
            self.total_price = self.unit_price * self.total_gross_weight

        super().save(*args, **kwargs)
        # Trigger purchase order total_amount update
        if self.purchase_order_id:
            self.purchase_order.update_total_amount()
