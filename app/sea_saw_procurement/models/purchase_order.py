"""
Purchase Order Model

Purchase Order - 使用 Supplier 模型
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.db.models import Sum
from django.contrib.contenttypes.fields import GenericRelation

from sea_saw_base.models import AbstractOrderBase
from sea_saw_sales.models import Order
from .enums import PurchaseStatus


class PurchaseOrder(AbstractOrderBase):
    """
    Purchase Order - Records purchasing information for orders

    隶属于Pipeline流程，由Pipeline创建和管理。
    Belongs to a Pipeline process, created and managed by Pipeline.

    Flow: Pipeline → PurchaseOrder → OutboundOrder
    """

    purchase_code = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Purchase Code"),
        help_text=_("Unique identifier for this purchase order."),
    )

    # Pipeline 关联 (新设计的主关联)
    pipeline = models.ForeignKey(
        "sea_saw_pipeline.Pipeline",  # String reference to avoid circular import
        on_delete=models.CASCADE,
        related_name="purchase_orders",
        verbose_name=_("Pipeline"),
        help_text=_("The business process pipeline this purchase order belongs to."),
    )

    purchase_order_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Purchase Order Date"),
    )

    account = models.ForeignKey(
        "sea_saw_crm.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_orders",
        verbose_name=_("Account"),
        help_text=_("Supplier account for this purchase order"),
    )

    related_order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="purchase_orders_legacy_order",
        verbose_name=_("Related Order (Legacy)"),
        help_text=_("Sales order (legacy field, use pipeline.order instead)."),
    )

    status = models.CharField(
        max_length=32,
        choices=PurchaseStatus.choices,
        default=PurchaseStatus.DRAFT,
        verbose_name=_("Purchase Order Status"),
    )

    # GenericRelation to unified Attachment model
    attachments = GenericRelation(
        "sea_saw_attachment.Attachment",
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="purchase_order",
    )

    class Meta:
        verbose_name = _("Purchase Order")
        verbose_name_plural = _("Purchase Orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["purchase_code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["account"]),
        ]

    def __str__(self):
        return self.purchase_code or _("Unnamed Purchase Order")

    def generate_code(self):
        """Auto-generate purchase order code"""
        year = timezone.now().year
        count = PurchaseOrder.objects.filter(created_at__year=year).count() + 1
        return f"PO{year}-{count:06d}"

    def update_total_amount(self):
        """Update total amount from purchase items"""
        total = self.purchase_items.aggregate(total=Sum("total_price"))[
            "total"
        ] or Decimal("0")
        PurchaseOrder.objects.filter(pk=self.pk).update(total_amount=total)

    def save(self, *args, **kwargs):
        """Auto-generate purchase code if not set"""
        if not self.purchase_code:
            self.purchase_code = self.generate_code()
        super().save(*args, **kwargs)
        # Auto-update total_amount after save
        if hasattr(self, "purchase_items"):
            self.update_total_amount()
