"""
Pipeline Service - Complex Business Logic for Pipeline Orchestration

This service layer only contains methods with complex business logic.
Simple CRUD operations are handled directly by the Manager layer.

Handles:
- Complex state transitions with validation
- Cascade operations (e.g., canceling all sub-entities)
- Cross-entity synchronization
- Business rules enforcement
"""
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from ..models import Pipeline
from ..models.pipeline import PipelineStatusType


class PipelineService:
    """
    Service class for complex Pipeline business logic

    Note: Simple create operations (create_order, create_production_order, etc.)
    are handled directly by Pipeline.objects (Manager layer) to reduce unnecessary abstraction.
    """

    @staticmethod
    @transaction.atomic
    def complete_production(pipeline, production_order, user=None):
        """
        Mark production order as completed and update pipeline status

        Args:
            pipeline (Pipeline): The pipeline
            production_order (ProductionOrder): The production order to complete
            user: User completing the production
        """
        from sea_saw_production.models import ProductionStatus

        if production_order.pipeline_id != pipeline.id:
            raise ValidationError(
                {"production_order": "ProductionOrder does not belong to this pipeline"}
            )

        production_order.status = ProductionStatus.COMPLETED
        production_order.end_date = timezone.now().date()
        production_order.save(update_fields=["status", "end_date", "updated_at"])

        # Update pipeline status
        if pipeline.status == PipelineStatusType.IN_PRODUCTION:
            pipeline.status = PipelineStatusType.PRODUCTION_COMPLETED
            pipeline.save(update_fields=["status", "updated_at"])

    @staticmethod
    @transaction.atomic
    def complete_purchase(pipeline, purchase_order, user=None):
        """
        Mark purchase order as completed and update pipeline status

        Args:
            pipeline (Pipeline): The pipeline
            purchase_order (PurchaseOrder): The purchase order to complete
            user: User completing the purchase
        """
        from sea_saw_procurement.models import PurchaseStatus

        if purchase_order.pipeline_id != pipeline.id:
            raise ValidationError(
                {"purchase_order": "PurchaseOrder does not belong to this pipeline"}
            )

        purchase_order.status = PurchaseStatus.RECEIVED
        purchase_order.save(update_fields=["status", "updated_at"])

        # Update pipeline status
        if pipeline.status == PipelineStatusType.IN_PURCHASE:
            pipeline.status = PipelineStatusType.PURCHASE_COMPLETED
            pipeline.save(update_fields=["status", "updated_at"])

    @staticmethod
    @transaction.atomic
    def complete_outbound(pipeline, outbound_order, user=None):
        """
        Mark outbound order as completed and update pipeline status

        Args:
            pipeline (Pipeline): The pipeline
            outbound_order (OutboundOrder): The outbound order to complete
            user: User completing the outbound
        """
        from sea_saw_warehouse.models import OutboundStatus

        if outbound_order.pipeline_id != pipeline.id:
            raise ValidationError(
                {"outbound_order": "OutboundOrder does not belong to this pipeline"}
            )

        outbound_order.status = OutboundStatus.COMPLETED
        outbound_order.save(update_fields=["status", "updated_at"])

        # Update pipeline status
        if pipeline.status == PipelineStatusType.IN_OUTBOUND:
            pipeline.status = PipelineStatusType.OUTBOUND_COMPLETED
            pipeline.save(update_fields=["status", "updated_at"])

    @staticmethod
    @transaction.atomic
    def complete_pipeline(pipeline, user=None):
        """
        Mark the entire pipeline as completed

        Args:
            pipeline (Pipeline): The pipeline to complete
            user: User completing the pipeline
        """
        # Validate all sub-entities are completed
        if pipeline.status != PipelineStatusType.OUTBOUND_COMPLETED:
            raise ValidationError(
                {
                    "status": "Pipeline must be in OUTBOUND_COMPLETED status before final completion"
                }
            )

        pipeline.complete(user=user)

    @staticmethod
    @transaction.atomic
    def cancel_pipeline(pipeline, user=None, reason=None):
        """
        Cancel the pipeline and all related entities

        Args:
            pipeline (Pipeline): The pipeline to cancel
            user: User canceling the pipeline
            reason (str): Cancellation reason
        """
        # Cancel all sub-entities
        from sea_saw_production.models import ProductionStatus
        from sea_saw_procurement.models import PurchaseStatus
        from sea_saw_warehouse.models import OutboundStatus

        # Cancel production orders
        pipeline.production_orders.filter(deleted__isnull=True).update(
            status=ProductionStatus.CANCELLED, updated_at=timezone.now()
        )

        # Cancel purchase orders
        pipeline.purchase_orders.filter(deleted__isnull=True).update(
            status=PurchaseStatus.CANCELLED, updated_at=timezone.now()
        )

        # Cancel outbound orders
        pipeline.outbound_orders.filter(deleted__isnull=True).update(
            status=OutboundStatus.CANCELLED, updated_at=timezone.now()
        )

        # Cancel pipeline
        if reason:
            pipeline.remark = f"{pipeline.remark or ''}\nCancelled: {reason}".strip()
        pipeline.cancel(user=user)
