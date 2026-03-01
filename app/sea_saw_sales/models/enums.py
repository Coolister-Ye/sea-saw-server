
"""
Order-related enumerations
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class OrderStatusType(models.TextChoices):
    """
    Order Status Enum - Independent sales document lifecycle.

    Represents commercial intent only. Fulfillment status is tracked
    via order.pipeline.status (read as order.fulfillment_status).

    Status flow: draft -> confirmed
    Terminal states: cancelled
    """

    DRAFT = "draft", _("Draft")
    CONFIRMED = "confirmed", _("Confirmed")
    CANCELLED = "cancelled", _("Cancelled")
