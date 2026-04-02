"""
Status Sync Service - Pipeline → sub-entity status synchronization

Cascade rules (explicit, user-triggered only):
- ORDER_CONFIRMED : Confirm the sales order (draft → confirmed)
- CANCELLED       : Cancel the sales order only (sub-entities unaffected)
- DRAFT           : Revert the sales order back to draft (confirmed → draft)
                    Triggered on rollback from issue_reported → draft
- ISSUE_REPORTED resume (→ in_production / in_outbound / etc.):
                    Restore sub-entities from issue_reported → active

All other Pipeline transitions leave sub-entity statuses unchanged.
Sub-entities manage their own status independently. Pipeline transitions are
validated against sub-entity completion state before being allowed.
"""

from django.db import transaction
from django.utils import timezone

from ..models.pipeline import PipelineStatusType
from ..constants import (
    SubEntityStatus,
    PIPELINE_TO_ACTIVE_ENTITY,
    PIPELINE_TO_SUBENTITY_STATUS,
    TERMINAL_STATUSES,
    ACTIVE_ENTITY_TO_ENTITY_TYPES,
)


class StatusSyncService:
    """
    Status synchronization service between Pipeline and sub-entities.

    Cascade-only: Pipeline status changes only propagate to sub-entities on
    cancel. All other transitions (including issue_reported) leave sub-entity
    statuses untouched — sub-entities manage their own lifecycle.
    """

    @classmethod
    def _get_subentity_queryset(cls, pipeline, entity_type):
        """
        Get the queryset for a specific sub-entity type.

        Args:
            pipeline: Pipeline instance
            entity_type: Type string ("production", "purchase", "outbound")

        Returns:
            QuerySet or None
        """
        queryset_map = {
            "production": pipeline.production_orders,
            "purchase": pipeline.purchase_orders,
            "outbound": pipeline.outbound_orders,
        }
        queryset = queryset_map.get(entity_type)
        if queryset is not None:
            return queryset.filter(deleted__isnull=True)
        return None

    @classmethod
    def _confirm_order(cls, pipeline, user=None):
        """
        Confirm the order when pipeline reaches ORDER_CONFIRMED.

        Only transitions draft → confirmed. Idempotent: if already confirmed,
        does nothing. Does not override cancelled orders.

        Args:
            pipeline: Pipeline instance
            user: User performing the action
        """
        if not pipeline.order:
            return
        order = pipeline.order
        if order.status != "draft":
            return
        order.status = "confirmed"
        order.updated_at = timezone.now()
        if user:
            order.updated_by = user
        order.save(update_fields=["status", "updated_at", "updated_by"])

    @classmethod
    def _cancel_order(cls, pipeline, user=None):
        """
        Cancel the order when pipeline is cancelled.

        Idempotent: if already cancelled, does nothing.

        Args:
            pipeline: Pipeline instance
            user: User performing the action
        """
        if not pipeline.order:
            return
        order = pipeline.order
        if order.status == "cancelled":
            return
        order.status = "cancelled"
        order.updated_at = timezone.now()
        if user:
            order.updated_by = user
        order.save(update_fields=["status", "updated_at", "updated_by"])

    @classmethod
    def _revert_order_to_draft(cls, pipeline, user=None):
        """
        Revert the order back to draft when pipeline returns to DRAFT.

        Reverts any non-terminal order status (confirmed) back to draft.
        Idempotent: already-draft or cancelled orders are left untouched.

        Args:
            pipeline: Pipeline instance
            user: User performing the action
        """
        if not pipeline.order:
            return
        order = pipeline.order
        # Skip if already draft or in a terminal state (cancelled)
        if order.status in ("draft", "cancelled"):
            return
        order.status = "draft"
        order.updated_at = timezone.now()
        if user:
            order.updated_by = user
        order.save(update_fields=["status", "updated_at", "updated_by"])

    @classmethod
    def _bulk_update_subentities(
        cls, pipeline, entity_type, target_status, status_filter=None
    ):
        """
        Bulk update sub-entities of a specific type.

        Uses QuerySet.update() to bypass Django signals (prevents loops).

        Args:
            pipeline: Pipeline instance
            entity_type: Type string ("production", "purchase", "outbound")
            target_status: Target status value
            status_filter: Optional status to filter by (for selective updates)
        """
        queryset = cls._get_subentity_queryset(pipeline, entity_type)
        if queryset is None:
            return

        if status_filter is not None:
            queryset = queryset.filter(status=status_filter)
        else:
            queryset = queryset.exclude(status__in=TERMINAL_STATUSES)

        queryset.update(status=target_status, updated_at=timezone.now())

    @classmethod
    @transaction.atomic
    def sync_pipeline_to_subentities(cls, pipeline, new_status, user=None):
        """
        Cascade pipeline status change to sub-entities (limited to exceptions only).

        Cascades:
        - ORDER_CONFIRMED: Confirms the sales order
        - CANCELLED: Cancels the sales order only (sub-entities unaffected)
        - All other statuses: no sub-entity changes

        Args:
            pipeline: Pipeline instance
            new_status: New pipeline status
            user: User performing the action
        """
        # Update active_entity field based on new status
        active_entity_value = PIPELINE_TO_ACTIVE_ENTITY.get(new_status)
        if active_entity_value is not None:  # None means keep existing
            pipeline.active_entity = active_entity_value
            pipeline.save(update_fields=["active_entity", "updated_at"])

        # Handle the nodes where Pipeline affects Order.status
        if new_status == PipelineStatusType.ORDER_CONFIRMED:
            cls._confirm_order(pipeline, user)
        elif new_status == PipelineStatusType.CANCELLED:
            cls._cancel_order(pipeline, user)
        elif new_status == PipelineStatusType.DRAFT:
            cls._revert_order_to_draft(pipeline, user)

        # Apply status updates to production/purchase/outbound sub-entities
        status_mapping = PIPELINE_TO_SUBENTITY_STATUS.get(new_status, {})
        for entity_type, target_status in status_mapping.items():
            cls._bulk_update_subentities(pipeline, entity_type, target_status)

    @classmethod
    def sync_subentity_to_pipeline(
        cls, subentity, entity_type, old_status, new_status, user=None
    ):
        """
        Reverse sync: Called when a sub-entity status changes.

        Currently a no-op — sub-entities manage their own lifecycle independently.
        Pipeline transitions are user-triggered and validated against sub-entity
        completion state. There is no automatic pipeline advancement from sub-entity changes.
        """
        pass

    @classmethod
    def restore_issue_entities(cls, pipeline, resume_status, user=None):
        """
        Restore sub-entities from issue_reported → active when pipeline resumes
        from issue_reported to a non-rollback status.

        Called by PipelineStateService.transition when:
            current_status == ISSUE_REPORTED and target is not DRAFT/CANCELLED.

        Only restores sub-entities whose type matches the resume stage's active
        entity (e.g. in_production → restores production orders only).
        Order.status is NOT touched here — it is managed by _revert_order_to_draft
        (for → DRAFT) or left unchanged (for forward resume).

        Args:
            pipeline: Pipeline instance (already at new status in memory)
            resume_status: The target status being resumed to
            user: User performing the action
        """
        active_entity_value = PIPELINE_TO_ACTIVE_ENTITY.get(resume_status)
        if active_entity_value is None:
            return

        entity_types = ACTIVE_ENTITY_TO_ENTITY_TYPES.get(active_entity_value, [])
        for entity_type in entity_types:
            if entity_type == "order":
                continue
            cls._bulk_update_subentities(
                pipeline,
                entity_type,
                SubEntityStatus.ACTIVE,
                status_filter=SubEntityStatus.ISSUE_REPORTED,
            )
