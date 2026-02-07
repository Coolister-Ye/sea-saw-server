"""
Order Model

Sales Order - 使用 Company 和 Contact 模型
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation

from sea_saw_base.models import AbstractOrderBase
from .enums import OrderStatusType
from ..manager.order_model_manager import OrderModelManager


class Order(AbstractOrderBase):
    """
    Sales Order
    Contains shipment info, linked contract, price summary and status.
    """

    objects = OrderModelManager()

    order_code = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Order Code"),
        help_text=_("Unique identifier for this order."),
    )

    order_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Order Date"),
    )

    account = models.ForeignKey(
        "sea_saw_crm.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Account"),
        help_text=_("Customer account for this order"),
    )

    contact = models.ForeignKey(
        "sea_saw_crm.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Contact"),
        help_text=_("Contact person for this order"),
    )

    status = models.CharField(
        max_length=32,
        choices=OrderStatusType.choices,
        default=OrderStatusType.DRAFT,
        verbose_name=_("Order Status"),
    )

    # GenericRelation to unified Attachment model
    attachments = GenericRelation(
        "sea_saw_attachment.Attachment",
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="order",
    )

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["account"]),
        ]

    def __str__(self):
        return self.order_code or _("Unnamed Order")

    def generate_code(self):
        """Auto-generate order code"""

        year = timezone.now().year
        count = Order.objects.filter(created_at__year=year).count() + 1
        return f"SO{year}-{count:06d}"

    def update_total_amount(self):
        """直接用 QuerySet update 避免递归 save()"""
        total = self.order_items.aggregate(total=Sum("total_price"))[
            "total"
        ] or Decimal("0")
        Order.objects.filter(pk=self.pk).update(total_amount=total)

    def save(self, *args, **kwargs):

        # auto populate order code
        if not self.order_code:
            self.order_code = self.generate_code()
        super().save(*args, **kwargs)

        # auto update total_amount
        if hasattr(self, "order_items"):
            self.update_total_amount()
