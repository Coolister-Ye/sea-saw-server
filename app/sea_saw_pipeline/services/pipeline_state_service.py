"""
Pipeline State Service - State Machine for Pipeline Status Transitions

Manages valid state transitions and business rules for Pipeline status changes.
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from ..models.pipeline import PipelineStatusType
from ..constants import (
    PIPELINE_STATE_MACHINE_BY_TYPE,
    PIPELINE_ROLE_ALLOWED_TARGET_STATES,
    PIPELINE_STATUS_PRIORITY,
)

# Rollback threshold priorities
_PRIORITY_BEFORE_PRODUCTION = 1  # draft, order_confirmed
_PRIORITY_BEFORE_OUTBOUND = 3  # in_production, production_completed, etc.


class PipelineStateService:
    """
    Pipeline state machine service.
    Manages status transitions based on pipeline_type and role_type.
    """

    @classmethod
    def _get_status_priority(cls, status: str) -> int:
        """Get priority value for a status."""
        return PIPELINE_STATUS_PRIORITY.get(status, 0)

    @classmethod
    def _is_backward_transition(cls, current_status: str, target_status: str) -> bool:
        """Check if transition is a rollback (moving to lower priority status)."""
        return cls._get_status_priority(target_status) < cls._get_status_priority(
            current_status
        )

    @classmethod
    def _delete_related_orders(cls, pipeline, order_types: list[str]) -> dict:
        """
        Delete related orders by type.

        Args:
            pipeline: The pipeline instance
            order_types: List of order types to delete ('production', 'purchase', 'outbound')

        Returns:
            dict: Deletion counts for each order type
        """
        result = {}
        type_to_relation = {
            "production": "production_orders",
            "purchase": "purchase_orders",
            "outbound": "outbound_orders",
        }

        for order_type in order_types:
            relation_name = type_to_relation.get(order_type)
            if relation_name:
                relation = getattr(pipeline, relation_name)
                deleted = relation.filter(deleted__isnull=True).delete()
                result[f"deleted_{relation_name}"] = deleted[0] if deleted else 0

        return result

    @classmethod
    def _cleanup_documents_on_rollback(cls, pipeline, target_status: str) -> dict:
        """
        Delete downstream documents when rolling back status.

        Rollback rules:
        - To draft/order_confirmed: delete all sub-orders
        - To production/purchase stages: delete only outbound orders
        """
        target_priority = cls._get_status_priority(target_status)

        if target_priority <= _PRIORITY_BEFORE_PRODUCTION:
            return cls._delete_related_orders(
                pipeline, ["production", "purchase", "outbound"]
            )

        if target_priority <= _PRIORITY_BEFORE_OUTBOUND:
            return cls._delete_related_orders(pipeline, ["outbound"])

        return {}

    @classmethod
    def _require_related_orders(cls, pipeline, order_type: str, target_status: str):
        """
        Validate that pipeline has at least one related order of the given type.

        Args:
            pipeline: The pipeline instance
            order_type: Type of order ('production', 'purchase', 'outbound')
            target_status: Target status (for error message)

        Raises:
            ValidationError: If no related orders exist
        """
        type_to_relation = {
            "production": "production_orders",
            "purchase": "purchase_orders",
            "outbound": "outbound_orders",
        }
        relation_name = type_to_relation.get(order_type)
        if not relation_name:
            return

        relation = getattr(pipeline, relation_name)
        if not relation.filter(deleted__isnull=True).exists():
            raise ValidationError(
                {order_type: f"Must create {order_type} order before {target_status}"}
            )

    @classmethod
    def _validate_transition(cls, pipeline, target_status: str, _user=None):
        """
        Validate transition prerequisites.

        Args:
            pipeline: The pipeline instance
            target_status: Target status
            _user: Reserved for future permission-based validations

        Raises:
            ValidationError: If validation fails
        """
        if target_status == PipelineStatusType.ORDER_CONFIRMED:
            if not pipeline.order:
                raise ValidationError({"order": "Pipeline must have an order"})
            if not pipeline.account:
                raise ValidationError({"account": "Pipeline must have an account"})

        elif target_status == PipelineStatusType.PRODUCTION_COMPLETED:
            cls._require_related_orders(pipeline, "production", target_status)

        elif target_status == PipelineStatusType.PURCHASE_COMPLETED:
            cls._require_related_orders(pipeline, "purchase", target_status)

        elif target_status == PipelineStatusType.OUTBOUND_COMPLETED:
            cls._require_related_orders(pipeline, "outbound", target_status)

        elif target_status == PipelineStatusType.PURCHASE_AND_PRODUCTION_COMPLETED:
            cls._require_related_orders(pipeline, "purchase", target_status)
            cls._require_related_orders(pipeline, "production", target_status)

        elif target_status == PipelineStatusType.COMPLETED:
            cls._validate_all_outbound_completed(pipeline)

    @classmethod
    def _validate_all_outbound_completed(cls, pipeline):
        """Validate all outbound orders are completed."""
        from sea_saw_warehouse.models import OutboundStatus

        has_incomplete = (
            pipeline.outbound_orders.filter(deleted__isnull=True)
            .exclude(status=OutboundStatus.COMPLETED)
            .exists()
        )
        if has_incomplete:
            raise ValidationError(
                {"outbound": "All outbound orders must be completed first"}
            )

    @classmethod
    def _validate_role_permission(cls, pipeline, target_status: str, user):
        """
        Validate user has permission for the target status.

        Args:
            pipeline: The pipeline instance
            target_status: Target status
            user: User performing the transition

        Raises:
            ValidationError: If user lacks permission
        """
        role = getattr(getattr(user, "role", None), "role_type", None)
        if not role:
            raise ValidationError({"role": "User role required"})

        allowed = PIPELINE_ROLE_ALLOWED_TARGET_STATES.get(role, set())
        if "*" not in allowed and target_status not in allowed:
            raise ValidationError({"permission": "Permission denied for this transition"})

    # Status to timestamp field mapping
    _STATUS_TIMESTAMP_FIELDS = {
        PipelineStatusType.ORDER_CONFIRMED: "confirmed_at",
        PipelineStatusType.COMPLETED: "completed_at",
        PipelineStatusType.CANCELLED: "cancelled_at",
    }

    @classmethod
    def _update_timestamps(cls, pipeline, target_status: str):
        """Update relevant timestamp based on target status."""
        field = cls._STATUS_TIMESTAMP_FIELDS.get(target_status)
        if field:
            setattr(pipeline, field, timezone.now())

    @classmethod
    def _get_state_machine(cls, pipeline_type: str) -> dict:
        """
        Get state machine for pipeline type.

        Raises:
            ValidationError: If no state machine exists for the type
        """
        state_machine = PIPELINE_STATE_MACHINE_BY_TYPE.get(pipeline_type)
        if not state_machine:
            raise ValidationError(
                {"pipeline_type": f"No state machine for: {pipeline_type}"}
            )
        return state_machine

    @classmethod
    def _validate_state_transition(
        cls, state_machine: dict, current_status: str, target_status: str, pipeline_type: str
    ):
        """
        Validate the state transition is allowed by the state machine.

        Raises:
            ValidationError: If transition is not allowed
        """
        allowed_targets = state_machine.get(current_status, set())
        if target_status not in allowed_targets:
            raise ValidationError(
                {
                    "status": f"Invalid transition: {pipeline_type} | {current_status} -> {target_status}"
                }
            )

    @classmethod
    @transaction.atomic
    def transition(cls, *, pipeline, target_status: str, user=None):
        """
        Transition pipeline to target status with validation.

        Args:
            pipeline: The pipeline to transition
            target_status: Target status
            user: User performing the transition

        Returns:
            Pipeline: The updated pipeline instance

        Raises:
            ValidationError: If transition is invalid
        """
        current_status = pipeline.status
        pipeline_type = pipeline.pipeline_type

        # Validate state machine transition
        state_machine = cls._get_state_machine(pipeline_type)
        cls._validate_state_transition(
            state_machine, current_status, target_status, pipeline_type
        )

        # Validate prerequisites and permissions
        cls._validate_transition(pipeline, target_status)
        cls._validate_role_permission(pipeline, target_status, user)

        # Handle rollback cleanup
        cleanup_result = {}
        if cls._is_backward_transition(current_status, target_status):
            cleanup_result = cls._cleanup_documents_on_rollback(pipeline, target_status)

        # Update pipeline
        pipeline.status = target_status
        cls._update_timestamps(pipeline, target_status)
        if user:
            pipeline.updated_by = user

        pipeline.save(
            update_fields=[
                "status",
                "updated_at",
                "updated_by",
                "confirmed_at",
                "completed_at",
                "cancelled_at",
            ]
        )

        # Attach cleanup result for caller reference
        pipeline._cleanup_result = cleanup_result

        # Sync sub-entity statuses
        from .status_sync_service import StatusSyncService

        StatusSyncService.sync_pipeline_to_subentities(
            pipeline=pipeline,
            old_status=current_status,
            new_status=target_status,
            user=user,
        )

        return pipeline

    @classmethod
    def _get_user_role(cls, user) -> str | None:
        """Extract role_type from user object."""
        return getattr(getattr(user, "role", None), "role_type", None)

    @classmethod
    def get_allowed_actions(cls, pipeline, user) -> list[str]:
        """
        Get allowed target statuses for user on this pipeline.

        Args:
            pipeline: The pipeline instance
            user: Current user

        Returns:
            Sorted list of allowed target statuses
        """
        role = cls._get_user_role(user)
        if not role:
            return []

        state_machine = PIPELINE_STATE_MACHINE_BY_TYPE.get(pipeline.pipeline_type, {})
        state_targets = state_machine.get(pipeline.status, set())

        role_targets = PIPELINE_ROLE_ALLOWED_TARGET_STATES.get(role, set())

        # Admin has all permissions
        if "*" in role_targets:
            return sorted(state_targets)

        # Return intersection of state machine and role permissions
        return sorted(state_targets & role_targets)
