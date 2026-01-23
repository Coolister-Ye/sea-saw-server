"""
Production Order Model
"""
import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation

from ..base import BaseModel
from ..order import Order
from .enums import ProductionStatus


class ProductionOrder(BaseModel):
    """
    生产单：隶属于Pipeline流程，由Pipeline创建和管理。
    Production Order: belongs to a Pipeline process, created and managed by Pipeline.
    """

    production_code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Production Code"),
        help_text=_("Unique code for the production order."),
    )

    # Pipeline 关联 (新设计的主关联)
    pipeline = models.ForeignKey(
        "Pipeline",
        on_delete=models.CASCADE,
        related_name="production_orders",
        verbose_name=_("Pipeline"),
        help_text=_("The business process pipeline this production order belongs to."),
    )

    # 保留 related_order 用于向后兼容和快速查询
    related_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="production_orders_legacy",
        verbose_name=_("Related Order (Legacy)"),
        help_text=_("Sales order (legacy field, use pipeline.order instead)."),
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

    # GenericRelation to unified Attachment model
    attachments = GenericRelation(
        "Attachment",
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="production_order",
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
