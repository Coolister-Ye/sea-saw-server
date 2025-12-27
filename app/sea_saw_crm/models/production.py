import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .base import BaseModel
from .order import Order, OrderItem


class ProductionStatus(models.TextChoices):
    """Production Status Enum"""

    DRAFT = "draft", _("Draft")  # 草稿
    PLANNED = "planned", _("Planned")  # 已计划
    IN_PROGRESS = "in_progress", _("In Progress")  # 进行中
    PAUSED = "paused", _("Paused")  # 暂停
    FINISHED = "finished", _("Finished")  # 已完成
    CANCELLED = "cancelled", _("Cancelled")  # 取消
    ISSUE_REPORTED = "issue_reported", _("Issue Reported")  # 问题单


class ProductionOrder(BaseModel):
    """
    生产单：可由多个订单触发，也可独立生产。
    """

    production_code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Production Code"),
        help_text=_("Unique code for the production order."),
    )

    related_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="production_orders",
        verbose_name=_("Related Order"),
        help_text=_("Sales order that triggered this production (optional)."),
    )

    planned_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Planned Date"),
    )

    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Start Date"),
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("End Date"),
    )

    status = models.CharField(
        max_length=20,
        choices=ProductionStatus.choices,
        default=ProductionStatus.DRAFT,
        verbose_name=_("Status"),
        help_text=_("Production status."),
    )

    remark = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Remark"),
        help_text=_("Additional notes for this production order."),
    )

    comment = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Comment"),
        help_text=_("Additional notes for this production order."),
    )

    production_files = models.FileField(
        upload_to="production_files/",
        null=True,
        blank=True,
        verbose_name=_("Production Files"),
    )

    class Meta:
        verbose_name = _("Production Order")
        verbose_name_plural = _("Production Orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["production_code"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.production_code

    def save(self, *args, **kwargs):
        """自动生成编号"""
        if not self.production_code:
            self.production_code = f"PROD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class ProductionItem(BaseModel):
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
