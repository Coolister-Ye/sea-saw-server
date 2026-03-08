"""
Status Sync Service - Pipeline → sub-entity status synchronization

Cascade rules (explicit, user-triggered only):
- CANCELLED: Cascade cancel to all sub-entities and order
- ISSUE_REPORTED: Mark currently active sub-entities as issue_reported (exception flow)
- ORDER_CONFIRMED: Confirm the sales order
- All other Pipeline transitions leave sub-entity statuses unchanged

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

    Cascade-only: Pipeline status changes only propagate to sub-entities in
    exceptional cases (cancel, issue_reported). All other transitions leave
    sub-entity statuses untouched — sub-entities manage their own lifecycle.
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
        - CANCELLED: Cancels the sales order + all sub-entities
        - ISSUE_REPORTED: Marks currently active sub-entities as issue_reported
        - All other statuses: no sub-entity changes (sub-entities are independent)

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

        # Handle issue_reported specially
        if new_status == PipelineStatusType.ISSUE_REPORTED:
            cls._propagate_issue_to_active_entity(pipeline)
            return

        # Handle the two nodes where Pipeline affects Order.status
        if new_status == PipelineStatusType.ORDER_CONFIRMED:
            cls._confirm_order(pipeline, user)
        elif new_status == PipelineStatusType.CANCELLED:
            cls._cancel_order(pipeline, user)

        # Apply status updates to production/purchase/outbound sub-entities
        status_mapping = PIPELINE_TO_SUBENTITY_STATUS.get(new_status, {})
        for entity_type, target_status in status_mapping.items():
            cls._bulk_update_subentities(pipeline, entity_type, target_status)

    @classmethod
    def _propagate_issue_to_active_entity(cls, pipeline):
        """
        When Pipeline goes to issue_reported, mark the active entity type's
        sub-entities as issue_reported.

        Only affects sub-entities currently in 'active' status.
        Order.status is NOT updated — issue is visible via pipeline.status.

        Args:
            pipeline: Pipeline instance
            user: User performing the action
        """
        active_entity = pipeline.active_entity
        entity_types = ACTIVE_ENTITY_TO_ENTITY_TYPES.get(active_entity, [])

        for entity_type in entity_types:
            if entity_type == "order":
                # Order.status is independent — issue is visible via pipeline.status
                continue
            cls._bulk_update_subentities(
                pipeline,
                entity_type,
                SubEntityStatus.ISSUE_REPORTED,
                status_filter=SubEntityStatus.ACTIVE,
            )

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
    @transaction.atomic
    def resolve_issue(cls, pipeline, resume_status, user=None):
        """
        Resolve issue and resume pipeline workflow.

        1. Restore issue_reported sub-entities to 'active' status
        2. Transition pipeline back to the resume status

        Order.status is NOT touched during issue resolution.

        Args:
            pipeline: Pipeline with issue_reported status
            resume_status: Status to transition back to
            user: User resolving the issue

        Returns:
            Pipeline instance

        Raises:
            ValueError: If pipeline is not in issue_reported status
        """
        from .pipeline_state_service import PipelineStateService

        if pipeline.status != PipelineStatusType.ISSUE_REPORTED:
            raise ValueError("Pipeline is not in issue_reported status")

        active_entity = pipeline.active_entity
        entity_types = ACTIVE_ENTITY_TO_ENTITY_TYPES.get(active_entity, [])

        # Restore issue_reported sub-entities to active status
        for entity_type in entity_types:
            if entity_type == "order":
                # Order.status is independent — skip
                continue
            cls._bulk_update_subentities(
                pipeline,
                entity_type,
                SubEntityStatus.ACTIVE,
                status_filter=SubEntityStatus.ISSUE_REPORTED,
            )

        # Transition pipeline back to resume status
        PipelineStateService.transition(
            pipeline=pipeline,
            target_status=resume_status,
            user=user,
        )

        return pipeline
