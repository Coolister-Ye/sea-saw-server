"""
Status Sync Constants - Configuration for Pipeline → sub-entity status synchronization

Cascade rules (Pipeline → sub-entities):
- CANCELLED: Cascade to all sub-entities (cancel all active/draft sub-orders)
- ISSUE_REPORTED: Mark currently active sub-entities as issue_reported (exception flow)
- All other transitions: Sub-entities manage their own status independently

Order.status is managed independently:
  - ORDER_CONFIRMED → order.status = 'confirmed'  (via StatusSyncService._confirm_order)
  - CANCELLED       → order.status = 'cancelled'  (via StatusSyncService._cancel_order)
  - All other Pipeline transitions leave Order.status unchanged.
"""

from ..models.pipeline import PipelineStatusType, ActiveEntityType


# Simplified sub-entity status values (to be used after enum simplification)
class SubEntityStatus:
    """Simplified status values for all sub-entities"""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ISSUE_REPORTED = "issue_reported"


# Pipeline status -> active_entity mapping
# Determines which entity type is currently active based on pipeline status
PIPELINE_TO_ACTIVE_ENTITY = {
    PipelineStatusType.DRAFT: ActiveEntityType.NONE,
    PipelineStatusType.ORDER_CONFIRMED: ActiveEntityType.ORDER,
    PipelineStatusType.IN_PRODUCTION: ActiveEntityType.PRODUCTION,
    PipelineStatusType.PRODUCTION_COMPLETED: ActiveEntityType.PRODUCTION,
    PipelineStatusType.IN_PURCHASE: ActiveEntityType.PURCHASE,
    PipelineStatusType.PURCHASE_COMPLETED: ActiveEntityType.PURCHASE,
    PipelineStatusType.IN_PURCHASE_AND_PRODUCTION: ActiveEntityType.PRODUCTION_AND_PURCHASE,
    PipelineStatusType.PURCHASE_AND_PRODUCTION_COMPLETED: ActiveEntityType.PRODUCTION_AND_PURCHASE,
    PipelineStatusType.IN_OUTBOUND: ActiveEntityType.OUTBOUND,
    PipelineStatusType.OUTBOUND_COMPLETED: ActiveEntityType.OUTBOUND,
    PipelineStatusType.COMPLETED: ActiveEntityType.NONE,
    PipelineStatusType.CANCELLED: ActiveEntityType.NONE,
    PipelineStatusType.ISSUE_REPORTED: None,  # Keep existing active_entity
}


# Pipeline status -> sub-entity status cascade mapping
# Only CANCELLED cascades to sub-entities; all other transitions leave sub-entities alone.
# (ISSUE_REPORTED is handled separately in StatusSyncService._propagate_issue_to_active_entity)
PIPELINE_TO_SUBENTITY_STATUS = {
    PipelineStatusType.CANCELLED: {
        "production": SubEntityStatus.CANCELLED,
        "purchase": SubEntityStatus.CANCELLED,
        "outbound": SubEntityStatus.CANCELLED,
        # Order handled separately via StatusSyncService._cancel_order()
    },
}


# Terminal statuses that should not be overwritten by sync operations
TERMINAL_STATUSES = {
    SubEntityStatus.CANCELLED,
    SubEntityStatus.ISSUE_REPORTED,
}


# Mapping from entity type string to ActiveEntityType enum
ENTITY_TYPE_TO_ACTIVE_ENTITY = {
    "order": ActiveEntityType.ORDER,
    "production": ActiveEntityType.PRODUCTION,
    "purchase": ActiveEntityType.PURCHASE,
    "outbound": ActiveEntityType.OUTBOUND,
}

# Mapping from ActiveEntityType to list of entity type strings
# Used when an active_entity can represent multiple entity types
ACTIVE_ENTITY_TO_ENTITY_TYPES = {
    ActiveEntityType.ORDER: ["order"],
    ActiveEntityType.PRODUCTION: ["production"],
    ActiveEntityType.PURCHASE: ["purchase"],
    ActiveEntityType.PRODUCTION_AND_PURCHASE: ["production", "purchase"],
    ActiveEntityType.OUTBOUND: ["outbound"],
    ActiveEntityType.NONE: [],
}
