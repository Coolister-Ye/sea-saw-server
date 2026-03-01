"""
Status Sync Constants - Configuration for Pipeline → sub-entity status synchronization

Defines mappings between Pipeline status and sub-entity statuses for:
- Forward sync: Pipeline status change → Update sub-entity statuses
- Reverse sync: Sub-entity status change → Update Pipeline status

Note: Order.status is NOT included in PIPELINE_TO_SUBENTITY_STATUS.
Order status is managed independently:
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


# Pipeline status -> sub-entity status mapping
# Defines what status each sub-entity type should have for each pipeline status
PIPELINE_TO_SUBENTITY_STATUS = {
    PipelineStatusType.DRAFT: {
        "production": SubEntityStatus.DRAFT,
        "purchase": SubEntityStatus.DRAFT,
        "outbound": SubEntityStatus.DRAFT,
    },
    PipelineStatusType.ORDER_CONFIRMED: {
        # Order handled separately via StatusSyncService._confirm_order()
    },
    PipelineStatusType.IN_PRODUCTION: {
        "production": SubEntityStatus.ACTIVE,
    },
    PipelineStatusType.PRODUCTION_COMPLETED: {
        "production": SubEntityStatus.COMPLETED,
    },
    PipelineStatusType.IN_PURCHASE: {
        "purchase": SubEntityStatus.ACTIVE,
    },
    PipelineStatusType.PURCHASE_COMPLETED: {
        "purchase": SubEntityStatus.COMPLETED,
    },
    PipelineStatusType.IN_PURCHASE_AND_PRODUCTION: {
        "production": SubEntityStatus.ACTIVE,
        "purchase": SubEntityStatus.ACTIVE,
    },
    PipelineStatusType.PURCHASE_AND_PRODUCTION_COMPLETED: {
        "production": SubEntityStatus.COMPLETED,
        "purchase": SubEntityStatus.COMPLETED,
    },
    PipelineStatusType.IN_OUTBOUND: {
        "outbound": SubEntityStatus.ACTIVE,
    },
    PipelineStatusType.OUTBOUND_COMPLETED: {
        "outbound": SubEntityStatus.COMPLETED,
    },
    PipelineStatusType.COMPLETED: {
        "production": SubEntityStatus.COMPLETED,
        "purchase": SubEntityStatus.COMPLETED,
        "outbound": SubEntityStatus.COMPLETED,
        # Order stays 'confirmed' — pipeline completion does not change order status
    },
    PipelineStatusType.CANCELLED: {
        "production": SubEntityStatus.CANCELLED,
        "purchase": SubEntityStatus.CANCELLED,
        "outbound": SubEntityStatus.CANCELLED,
        # Order handled separately via StatusSyncService._cancel_order()
    },
    # issue_reported is handled specially - only the active_entity type gets marked
    PipelineStatusType.ISSUE_REPORTED: {},
}


# Sub-entity completion triggers for auto-advancing Pipeline
# When ALL sub-entities of a type reach 'completed' status,
# Pipeline can auto-transition from current_status to target_status
SUBENTITY_COMPLETION_TRIGGERS = {
    "production": {
        "current_status": PipelineStatusType.IN_PRODUCTION,
        "target_status": PipelineStatusType.PRODUCTION_COMPLETED,
    },
    "purchase": {
        "current_status": PipelineStatusType.IN_PURCHASE,
        "target_status": PipelineStatusType.PURCHASE_COMPLETED,
    },
    "outbound": {
        "current_status": PipelineStatusType.IN_OUTBOUND,
        "target_status": PipelineStatusType.OUTBOUND_COMPLETED,
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


