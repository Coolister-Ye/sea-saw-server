"""
Status Sync Constants - Configuration for Pipeline → sub-entity status synchronization

Order.status cascade rules (StatusSyncService):
  - ORDER_CONFIRMED  → order.status = 'confirmed'  (_confirm_order)
  - CANCELLED        → order.status = 'cancelled'  (_cancel_order)
  - DRAFT            → order.status = 'draft'       (_revert_order_to_draft)
                       Triggered when rolling back issue_reported → draft.

Sub-entity (production/purchase/outbound) cascade rules:
  - issue_reported → resume state (e.g. in_production):
      sub-entities with issue_reported status are restored to active
      (restore_issue_entities, called from PipelineStateService.transition)
  - issue_reported → DRAFT: sub-entities are deleted (cleanup_documents_on_rollback)
  - All other transitions: sub-entities manage their own status independently
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
PIPELINE_TO_SUBENTITY_STATUS = {}
# Order.status on CANCELLED is handled separately via StatusSyncService._cancel_order()
# Sub-entities (production/purchase/outbound) are NOT cancelled when pipeline is cancelled


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
