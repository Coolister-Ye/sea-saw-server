
"""
Pipeline-related enumerations
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class PipelineStatusType(models.TextChoices):
    """Pipeline Status Enum - tracks the overall business process status"""

    DRAFT = "draft", _("Draft")
    ORDER_CONFIRMED = "order_confirmed", _("Order Confirmed")
    IN_PURCHASE = "in_purchase", _("In Purchase")
    PURCHASE_COMPLETED = "purchase_completed", _("Purchase Completed")
    IN_PRODUCTION = "in_production", _("In Production")
    PRODUCTION_COMPLETED = "production_completed", _("Production Completed")
    IN_PURCHASE_AND_PRODUCTION = "in_purchase_and_production", _(
        "In Purchase and Production"
    )
    PURCHASE_AND_PRODUCTION_COMPLETED = "purchase_and_production_completed", _(
        "Purchase and Production Completed"
    )
    IN_OUTBOUND = "in_outbound", _("In Outbound")
    OUTBOUND_COMPLETED = "outbound_completed", _("Outbound Completed")
    COMPLETED = "completed", _("Completed")
    CANCELLED = "cancelled", _("Cancelled")
    ISSUE_REPORTED = "issue_reported", _("Issue Reported")


class PipelineType(models.TextChoices):
    """Pipeline Type Enum - defines the business process flow"""

    PRODUCTION_FLOW = "production_flow", _("Production Flow")
    # Order → ProductionOrder → OutboundOrder

    PURCHASE_FLOW = "purchase_flow", _("Purchase Flow")
    # Order → PurchaseOrder → OutboundOrder

    HYBRID_FLOW = "hybrid_flow", _("Hybrid Flow")
    # Order → (ProductionOrder + PurchaseOrder) → OutboundOrder


class ActiveEntityType(models.TextChoices):
    """
    Active Entity Type - tracks which sub-entity type is currently active in the pipeline.
    Used for issue reporting to identify which entity has the problem.
    """

    NONE = "none", _("None")
    ORDER = "order", _("Order")
    PRODUCTION = "production", _("Production")
    PURCHASE = "purchase", _("Purchase")
    PRODUCTION_AND_PURCHASE = "production_and_purchase", _("Production and Purchase")
    OUTBOUND = "outbound", _("Outbound")
