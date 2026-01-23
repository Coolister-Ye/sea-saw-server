"""
Outbound Order Model
"""

import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation

from ..base import BaseModel
from ..order import Order
from .enums import OutboundStatus


class OutboundOrder(BaseModel):
    """
    出仓单 / 出货单
    Outbound Order / Shipment Order

    隶属于Pipeline流程，由Pipeline创建和管理。
    Belongs to a Pipeline process, created and managed by Pipeline.

    描述一次实际出货行为（整柜、拼柜、部分出货均可）
    Describes an actual shipment (full container, LCL, partial shipment, etc.)
    """

    outbound_code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Outbound Code"),
        help_text=_("Unique outbound / shipment code."),
    )

    # Pipeline 关联 (新设计的主关联)
    pipeline = models.ForeignKey(
        "Pipeline",
        on_delete=models.CASCADE,
        related_name="outbound_orders",
        verbose_name=_("Pipeline"),
        help_text=_("The business process pipeline this outbound order belongs to."),
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

    # GenericRelation to unified Attachment model
    attachments = GenericRelation(
        "Attachment",
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="outbound_order",
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
