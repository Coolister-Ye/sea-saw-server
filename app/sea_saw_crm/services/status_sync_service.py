"""
Status Sync Service - Bidirectional synchronization between Pipeline and sub-entities

Handles:
- Forward sync: Pipeline status change -> Update sub-entity statuses
- Reverse sync: Sub-entity status change -> Update Pipeline status
- Issue reporting propagation based on active_entity
"""

from django.db import transaction
from django.utils import timezone

from ..models.pipeline import PipelineStatusType, ActiveEntityType
from ..constants import (
    SubEntityStatus,
    PIPELINE_TO_ACTIVE_ENTITY,
    PIPELINE_TO_SUBENTITY_STATUS,
    SUBENTITY_COMPLETION_TRIGGERS,
    TERMINAL_STATUSES,
    ENTITY_TYPE_TO_ACTIVE_ENTITY,
    ACTIVE_ENTITY_TO_ENTITY_TYPES,
)


class StatusSyncService:
    """
    Bidirectional status synchronization service between Pipeline and sub-entities.

    Forward sync: When Pipeline status changes, update corresponding sub-entities.
    Reverse sync: When sub-entity status changes, potentially update Pipeline.
    """

    @classmethod
    def _get_subentity_queryset(cls, pipeline, entity_type):
        """
        Get the queryset for a specific sub-entity type.

        Args:
            pipeline: Pipeline instance
            entity_type: Type string ("production", "purchase", "outbound")

        Returns:
            QuerySet or None for "order" type
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
    def _update_order_status(
        cls, pipeline, target_status, user=None, status_filter=None
    ):
        """
        Update order status with optional status filter.

        Args:
            pipeline: Pipeline instance
            target_status: Target status value
            user: User performing the action
            status_filter: Optional status to filter by (for selective updates)
        """
        if not pipeline.order:
            return

        order = pipeline.order
        if status_filter is not None and order.status != status_filter:
            return
        if status_filter is None and order.status in TERMINAL_STATUSES:
            return

        order.status = target_status
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
    def sync_pipeline_to_subentities(cls, pipeline, old_status, new_status, user=None):
        """
        Forward sync: When Pipeline status changes, update sub-entity statuses.

        Args:
            pipeline: Pipeline instance
            old_status: Previous pipeline status
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
            cls._propagate_issue_to_active_entity(pipeline, user)
            return

        # Get status mapping for the new pipeline status
        status_mapping = PIPELINE_TO_SUBENTITY_STATUS.get(new_status, {})

        # Apply status updates to each entity type
        for entity_type, target_status in status_mapping.items():
            cls._update_subentity_status(pipeline, entity_type, target_status, user)

    @classmethod
    def _update_subentity_status(cls, pipeline, entity_type, target_status, user=None):
        """
        Update all sub-entities of a specific type to target status.

        Uses bulk update to avoid triggering Django signals (prevents loops).
        Skips entities in terminal states (cancelled, issue_reported).

        Args:
            pipeline: Pipeline instance
            entity_type: Type string ("order", "production", "purchase", "outbound")
            target_status: Target status value
            user: User performing the action
        """
        if entity_type == "order":
            cls._update_order_status(pipeline, target_status, user)
        else:
            cls._bulk_update_subentities(pipeline, entity_type, target_status)

    @classmethod
    def _propagate_issue_to_active_entity(cls, pipeline, user=None):
        """
        When Pipeline goes to issue_reported, mark the active entity type's
        sub-entities as issue_reported.

        Only affects sub-entities currently in 'active' status.

        Args:
            pipeline: Pipeline instance
            user: User performing the action
        """
        active_entity = pipeline.active_entity
        entity_types = ACTIVE_ENTITY_TO_ENTITY_TYPES.get(active_entity, [])

        for entity_type in entity_types:
            if entity_type == "order":
                cls._update_order_status(
                    pipeline,
                    SubEntityStatus.ISSUE_REPORTED,
                    user,
                    status_filter=SubEntityStatus.ACTIVE,
                )
            else:
                cls._bulk_update_subentities(
                    pipeline,
                    entity_type,
                    SubEntityStatus.ISSUE_REPORTED,
                    status_filter=SubEntityStatus.ACTIVE,
                )

    @classmethod
    @transaction.atomic
    def sync_subentity_to_pipeline(
        cls, subentity, entity_type, old_status, new_status, user=None
    ):
        """
        Reverse sync: When sub-entity status changes, potentially update Pipeline.

        Handles:
        - Auto-advance pipeline when all sub-entities complete
        - Propagate issue_reported to pipeline

        Args:
            subentity: The sub-entity instance (ProductionOrder, PurchaseOrder, etc.)
            entity_type: Type string ("production", "purchase", "outbound")
            old_status: Previous status
            new_status: New status
            user: User performing the action
        """
        pipeline = subentity.pipeline

        if new_status == SubEntityStatus.COMPLETED:
            cls._check_and_advance_pipeline(pipeline, entity_type, user)
        elif new_status == SubEntityStatus.ISSUE_REPORTED:
            cls._propagate_issue_to_pipeline(pipeline, entity_type, user)

    @classmethod
    def _check_and_advance_pipeline(cls, pipeline, entity_type, user=None):
        """
        Check if all sub-entities of a type are completed and auto-advance pipeline.

        Only advances if:
        - Pipeline is in the expected "in progress" status for this entity type
        - ALL sub-entities of this type are completed

        Args:
            pipeline: Pipeline instance
            entity_type: Type string ("production", "purchase", "outbound")
            user: User performing the action
        """
        trigger_config = SUBENTITY_COMPLETION_TRIGGERS.get(entity_type)
        if not trigger_config:
            return

        expected_current = trigger_config["current_status"]
        target_status = trigger_config["target_status"]

        # Only auto-advance if pipeline is in the expected current status
        if pipeline.status != expected_current:
            return

        # Check if ALL sub-entities of this type are completed
        if cls._all_subentities_completed(pipeline, entity_type):
            cls._try_pipeline_transition(pipeline, target_status, user)

    @classmethod
    def _all_subentities_completed(cls, pipeline, entity_type):
        """
        Check if all sub-entities of a type are completed.

        Returns True only if:
        - At least one sub-entity of this type exists
        - All non-deleted sub-entities have status 'completed'

        Args:
            pipeline: Pipeline instance
            entity_type: Type string

        Returns:
            bool: True if all sub-entities are completed
        """
        queryset = cls._get_subentity_queryset(pipeline, entity_type)
        if queryset is None:
            return False

        return (
            queryset.exists()
            and not queryset.exclude(status=SubEntityStatus.COMPLETED).exists()
        )

    @classmethod
    def _propagate_issue_to_pipeline(cls, pipeline, entity_type, user=None):
        """
        When sub-entity reports issue, update pipeline status and active_entity.

        Args:
            pipeline: Pipeline instance
            entity_type: Type string identifying which entity has the issue
            user: User performing the action
        """
        # Update active_entity to reflect which entity has the issue
        active_entity_value = ENTITY_TYPE_TO_ACTIVE_ENTITY.get(
            entity_type, ActiveEntityType.NONE
        )

        pipeline.active_entity = active_entity_value
        pipeline.save(update_fields=["active_entity", "updated_at"])

        # Transition pipeline to issue_reported if valid
        cls._try_pipeline_transition(pipeline, PipelineStatusType.ISSUE_REPORTED, user)

    @classmethod
    def _try_pipeline_transition(cls, pipeline, target_status, user=None):
        """
        Attempt to transition pipeline to target status.

        Silently fails if transition is not valid - manual transition will be needed.

        Args:
            pipeline: Pipeline instance
            target_status: Target pipeline status
            user: User performing the action
        """
        from .pipeline_state_service import PipelineStateService

        try:
            PipelineStateService.transition(
                pipeline=pipeline,
                target_status=target_status,
                user=user,
            )
        except Exception:
            # Transition may fail due to validation - that's ok
            pass

    @classmethod
    @transaction.atomic
    def resolve_issue(cls, pipeline, resume_status, user=None):
        """
        Resolve issue and resume pipeline workflow.

        1. Restore issue_reported sub-entities to 'active' status
        2. Transition pipeline back to the resume status

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
                cls._update_order_status(
                    pipeline,
                    SubEntityStatus.ACTIVE,
                    user,
                    status_filter=SubEntityStatus.ISSUE_REPORTED,
                )
            else:
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
