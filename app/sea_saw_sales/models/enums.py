
"""
Order-related enumerations
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class OrderStatusType(models.TextChoices):
    """
    Order Status Enum - Simplified for Pipeline sync

    Status flow: draft -> active -> completed
    Terminal states: cancelled, issue_reported
    """

    DRAFT = "draft", _("Draft")
    ACTIVE = "active", _("Active")
    COMPLETED = "completed", _("Completed")
    CANCELLED = "cancelled", _("Cancelled")
    ISSUE_REPORTED = "issue_reported", _("Issue Reported")
