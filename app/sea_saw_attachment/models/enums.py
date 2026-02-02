"""
Attachment Enums
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class AttachmentType(models.TextChoices):
    """
    Attachment Type Choices

    附件类型枚举
    """

    ORDER_ATTACHMENT = "order_attachment", _("Order Attachment")
    PRODUCTION_ATTACHMENT = "production_attachment", _("Production Attachment")
    PURCHASE_ATTACHMENT = "purchase_attachment", _("Purchase Attachment")
    OUTBOUND_ATTACHMENT = "outbound_attachment", _("Outbound Attachment")
    PAYMENT_ATTACHMENT = "payment_attachment", _("Payment Attachment")
