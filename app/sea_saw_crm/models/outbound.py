import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .base import BaseModel
from .order import Order, OrderItem
from .production import ProductionItem


class OutboundStatus(models.TextChoices):
    """出仓状态 Enum"""

    DRAFT = "draft", _("Draft")
    PACKED = "packed", _("Packed")
    SHIPPED = "shipped", _("Shipped")
    CUSTOM_CLEARED = "custom_cleared", _("Custom Cleared")
    ARRIVED = "arrived", _("Arrived")
    COMPLETED = "completed", _("Completed")


class OutboundOrder(BaseModel):
    """
    出仓单 / 出货单
    描述一次实际出货行为（整柜、拼柜、部分出货均可）
    """

    outbound_code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Outbound Code"),
        help_text=_("Unique outbound / shipment code."),
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="outbound_orders",
        verbose_name=_("Related Order"),
        help_text=_("Sales order this outbound belongs to (optional)."),
    )

    outbound_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Outbound Date"),
    )

    status = models.CharField(
        max_length=30,
        choices=OutboundStatus.choices,
        default=OutboundStatus.DRAFT,
        verbose_name=_("Status"),
    )

    container_no = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Container No."),
    )

    seal_no = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Seal No."),
    )

    destination_port = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Destination Port"),
    )

    logistics_provider = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Logistics Provider"),
    )

    loader = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Loader"),
        help_text=_("Person who loads the goods into the container."),
    )

    remark = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Remark"),
    )

    class Meta:
        verbose_name = _("Outbound Order")
        verbose_name_plural = _("Outbound Orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["outbound_code"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.outbound_code} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        """自动生成编号"""
        if not self.outbound_code:
            self.outbound_code = (
                f"OB-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
            )
        super().save(*args, **kwargs)


class OutboundItem(BaseModel):
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
