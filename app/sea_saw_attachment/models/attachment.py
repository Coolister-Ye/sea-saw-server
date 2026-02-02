"""
Unified Attachment Model - Uses GenericForeignKey for polymorphic relationships

统一附件模型 - 使用GenericForeignKey实现多态关联

支持的关联实体:
- Order (订单)
- ProductionOrder (生产订单)
- PurchaseOrder (采购订单)
- OutboundOrder (出库订单)
- Payment (付款单)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from sea_saw_base.models import BaseModel
from .enums import AttachmentType
from ..validators import validate_file_upload
from ..utils import attachment_file_path


class Attachment(BaseModel):
    """
    统一附件模型 - Unified Attachment Model

    使用GenericForeignKey支持多种实体类型的附件上传
    Uses GenericForeignKey to support attachments for multiple entity types

    使用场景 / Usage Examples:

    1. Order Attachment:
       content_type = ContentType.objects.get_for_model(Order)
       object_id = order.id
       attachment_type = ORDER_ATTACHMENT

    2. ProductionOrder Attachment:
       content_type = ContentType.objects.get_for_model(ProductionOrder)
       object_id = production_order.id
       attachment_type = PRODUCTION_ATTACHMENT

    3. Payment Attachment:
       content_type = ContentType.objects.get_for_model(Payment)
       object_id = payment.id
       attachment_type = PAYMENT_ATTACHMENT

    关系链 / Relationship Chain:
    Attachment → Order/ProductionOrder/PurchaseOrder/OutboundOrder/Payment (通过GenericFK)
    """

    attachment_type = models.CharField(
        max_length=50,
        choices=AttachmentType.choices,
        verbose_name=_("Attachment Type"),
        help_text=_(
            "Type of attachment (order, production, purchase, outbound, payment)"
        ),
    )

    # GenericForeignKey to support multiple entity types
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("Related Entity Type"),
        help_text=_(
            "Type of entity: Order, ProductionOrder, PurchaseOrder, OutboundOrder, or Payment"
        ),
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_("Related Entity ID"),
        help_text=_("ID of the related entity"),
    )
    related_object = GenericForeignKey("content_type", "object_id")

    # File fields
    file = models.FileField(
        upload_to=attachment_file_path,
        validators=[validate_file_upload],
        verbose_name=_("File"),
        help_text=_(
            "Upload file. Files are organized by entity type and date. "
            "Max size: 50MB. Allowed types: PDF, Office documents, images, archives."
        ),
    )

    file_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("File Name"),
        help_text=_("Original filename for display purposes."),
    )

    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("File Size (bytes)"),
    )

    description = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Optional description of the file."),
    )

    class Meta:
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["attachment_type"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return (
            f"{self.file_name or 'Attachment'} - {self.get_attachment_type_display()}"
        )

    def save(self, *args, **kwargs):
        """Auto-populate file_name, file_size, and attachment_type"""
        # Auto-populate file_name
        if self.file and not self.file_name:
            import os

            self.file_name = os.path.basename(self.file.name)

        # Auto-populate file_size
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass

        # Auto-set attachment_type if not set
        if not self.attachment_type and self.content_type:
            model_name = self.content_type.model
            if model_name == "order":
                self.attachment_type = AttachmentType.ORDER_ATTACHMENT
            elif model_name == "productionorder":
                self.attachment_type = AttachmentType.PRODUCTION_ATTACHMENT
            elif model_name == "purchaseorder":
                self.attachment_type = AttachmentType.PURCHASE_ATTACHMENT
            elif model_name == "outboundorder":
                self.attachment_type = AttachmentType.OUTBOUND_ATTACHMENT
            elif model_name == "payment":
                self.attachment_type = AttachmentType.PAYMENT_ATTACHMENT
            else:
                # Default to order attachment if unknown
                self.attachment_type = AttachmentType.ORDER_ATTACHMENT

        super().save(*args, **kwargs)
