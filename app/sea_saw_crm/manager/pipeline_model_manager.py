"""
Pipeline Model Manager - Handles Pipeline creation and sub-entity management

负责:
- 从Order创建Pipeline
- 从Pipeline创建Order (reverse operation)
- 从Pipeline创建ProductionOrder/PurchaseOrder/OutboundOrder
- 自动复制OrderItems到对应的Items
- 幂等控制和状态管理
"""

from .base_model_manager import BaseModelManager
from django.db import models, transaction
from django.core.exceptions import ValidationError


class PipelineModelManager(BaseModelManager):
    """
    Pipeline Manager - Orchestrates business process flows

    Features:
    - Create Pipeline from Order
    - Create Order from Pipeline (reverse operation)
    - Create ProductionOrder/PurchaseOrder/OutboundOrder from Pipeline
    - Auto-copy OrderItems to corresponding Items
    - Idempotency control (prevent duplicates)
    - State management integration
    """

    # ========================
    # Create Pipeline
    # ========================
    @transaction.atomic
    def create_with_auto_order(
        self,
        *,
        user=None,
        order_date=None,
        contact_id=None,
        currency="USD",
        total_amount=0,
        remark=None,
        **extra_fields,
    ):
        """
        Create a Pipeline with an automatically created Order

        This method first creates an Order, then creates a Pipeline linked to it.

        Args:
            user: User creating the pipeline
            order_date: Order date (defaults to today)
            contact_id: Contact ID for the order
            currency: Currency code (default: USD)
            total_amount: Total amount (default: 0)
            remark: Remark for the pipeline
            **extra_fields: Additional pipeline fields

        Returns:
            Pipeline instance with associated Order
        """
        from ..models.order import Order
        from django.utils import timezone

        # Create Order first
        order = Order.objects.create_with_user(
            user=user,
            order_date=order_date or timezone.now().date(),
            contact_id=contact_id,
            currency=currency,
            total_amount=total_amount,
            comment=remark or "Auto-created from pipeline",
        )

        # Create Pipeline with the new Order
        pipeline = self.create_with_user(
            user=user,
            order=order,
            contact_id=contact_id,
            order_date=order_date or timezone.now().date(),
            remark=remark,
            **extra_fields,
        )

        return pipeline

    @transaction.atomic
    def create_from_order(
        self,
        *,
        order,
        pipeline_type=None,
        user=None,
        **extra_fields,
    ):
        """
        Create a Pipeline from an existing Order

        Args:
            order: The Order instance
            pipeline_type: Type of pipeline flow (auto-determined if not specified)
            user: User creating the pipeline
            **extra_fields: Additional pipeline fields

        Returns:
            Pipeline instance
        """
        from ..models.pipeline import PipelineType

        # Create pipeline
        pipeline = self.create_with_user(
            user=user,
            order=order,
            pipeline_type=pipeline_type or PipelineType.PRODUCTION_FLOW,
            contact=order.contact or extra_fields.get("contact"),
            order_date=order.order_date or extra_fields.get("order_date"),
            remark=extra_fields.get("remark") or order.comment,
            **{
                k: v
                for k, v in extra_fields.items()
                if k not in ["remark", "contact", "order_date"]
            },
        )

        return pipeline

    # ========================
    # Create Order
    # ========================
    @transaction.atomic
    def create_order(
        self,
        *,
        pipeline,
        order_code=None,
        order_date=None,
        contact=None,
        user=None,
        copy_items=False,
        force=False,
        **extra_fields,
    ):
        """
        Create an Order from an existing Pipeline

        This is the reverse operation of create_from_order, useful when:
        - Creating a new order based on pipeline data
        - Duplicating an order workflow

        Args:
            pipeline: The Pipeline instance to create order from
            order_code: Custom order code (auto-generated if not provided)
            order_date: Order date (defaults to pipeline.order_date)
            contact: Contact for the order (defaults to pipeline.contact)
            user: User creating the order
            copy_items: Whether to copy items from pipeline's existing order
            force: Force creation even if pipeline already has an order
            **extra_fields: Additional order fields

        Returns:
            Order instance

        Raises:
            ValidationError: If pipeline already has an order and force=False
        """
        from ..models.order import Order

        # Idempotency check
        if not force and hasattr(pipeline, "order") and pipeline.order:
            raise ValidationError("Order already exists for this pipeline")

        # Create Order
        order = Order.objects.create_with_user(
            user=user,
            order_code=order_code,
            order_date=order_date or pipeline.order_date,
            contact=contact or pipeline.contact,
            comment=extra_fields.get("comment") or pipeline.remark,
            # Copy logistics and financial info if provided
            etd=extra_fields.get("etd"),
            loading_port=extra_fields.get("loading_port"),
            destination_port=extra_fields.get("destination_port"),
            shipment_term=extra_fields.get("shipment_term"),
            inco_terms=extra_fields.get("inco_terms"),
            currency=extra_fields.get("currency"),
            deposit=extra_fields.get("deposit"),
            balance=extra_fields.get("balance"),
            **{
                k: v
                for k, v in extra_fields.items()
                if k
                not in [
                    "comment",
                    "etd",
                    "loading_port",
                    "destination_port",
                    "shipment_term",
                    "inco_terms",
                    "currency",
                    "deposit",
                    "balance",
                ]
            },
        )

        # Copy items from pipeline's existing order if requested
        if copy_items and hasattr(pipeline, "order") and pipeline.order:
            self._copy_order_items(order, pipeline.order, user)

        return order

    def _copy_order_items(self, target_order, source_order, user=None):
        """Copy OrderItems from source order to target order"""
        from ..models.order import OrderItem

        items = [
            OrderItem(
                order=target_order,
                # Copy all product fields
                product_name=oi.product_name,
                specification=oi.specification,
                outter_packaging=oi.outter_packaging,
                inner_packaging=oi.inner_packaging,
                size=oi.size,
                unit=oi.unit,
                glazing=oi.glazing,
                gross_weight=oi.gross_weight,
                net_weight=oi.net_weight,
                # Copy order quantities and pricing
                order_qty=oi.order_qty,
                total_gross_weight=oi.total_gross_weight,
                total_net_weight=oi.total_net_weight,
                unit_price=oi.unit_price,
                total_price=oi.total_price,
                owner=user,
                created_by=user,
            )
            for oi in source_order.order_items.all()
        ]

        if items:
            OrderItem.objects.bulk_create(items)

    # ========================
    # Create ProductionOrder
    # ========================
    @transaction.atomic
    def create_production_order(
        self,
        *,
        pipeline,
        planned_date=None,
        start_date=None,
        remark=None,
        user=None,
        copy_items=True,
        force=False,
        auto_update_status=False,
        **extra_fields,
    ):
        """
        Create a ProductionOrder for the pipeline

        Args:
            pipeline: The parent Pipeline instance
            planned_date: Planned production date
            start_date: Start date
            remark: Additional remarks
            user: User creating the production order
            copy_items: Whether to copy OrderItems to ProductionItems
            force: Force creation even if production already exists
            auto_update_status: Whether to auto-transition pipeline status
            **extra_fields: Additional fields

        Returns:
            ProductionOrder instance
        """
        from ..models.production import ProductionOrder
        from ..models.pipeline import PipelineType

        # Validate pipeline type
        if pipeline.pipeline_type == PipelineType.PURCHASE_FLOW:
            raise ValidationError(
                "Cannot create ProductionOrder for PURCHASE_FLOW pipeline"
            )

        # Idempotency check
        if (
            not force
            and pipeline.production_orders.filter(deleted__isnull=True).exists()
        ):
            raise ValidationError("ProductionOrder already exists for this pipeline")

        # Create ProductionOrder
        production = ProductionOrder.objects.create_with_user(
            user=user,
            pipeline=pipeline,
            related_order=pipeline.order,  # For backward compatibility
            planned_date=planned_date,
            start_date=start_date,
            remark=remark or pipeline.remark or pipeline.order.comment,
            **extra_fields,
        )

        # Auto-copy OrderItems to ProductionItems
        if copy_items:
            self._create_production_items(production, pipeline.order, user)

        # Auto-update pipeline status based on pipeline_type
        if auto_update_status:
            self._auto_transition_pipeline_for_production(pipeline, user)

        return production

    def _auto_transition_pipeline_for_production(self, pipeline, user=None):
        """Auto-transition pipeline status when production order is created."""
        from ..models.pipeline import PipelineType, PipelineStatusType
        from ..services.pipeline_state_service import PipelineStateService

        # Determine target status based on pipeline type
        target_status = None
        if pipeline.pipeline_type == PipelineType.PRODUCTION_FLOW:
            if pipeline.status == PipelineStatusType.ORDER_CONFIRMED:
                target_status = PipelineStatusType.IN_PRODUCTION
        elif pipeline.pipeline_type == PipelineType.HYBRID_FLOW:
            if pipeline.status == PipelineStatusType.ORDER_CONFIRMED:
                target_status = PipelineStatusType.IN_PURCHASE_AND_PRODUCTION

        if target_status:
            PipelineStateService.transition(
                pipeline=pipeline,
                target_status=target_status,
                user=user,
            )

    def _create_production_items(self, production, order, user=None):
        """Copy OrderItems to ProductionItems"""
        from ..models.production import ProductionItem

        items = [
            ProductionItem(
                production_order=production,
                order_item=oi,
                # Copy base item fields
                product_name=oi.product_name,
                specification=oi.specification,
                outter_packaging=oi.outter_packaging,
                inner_packaging=oi.inner_packaging,
                size=oi.size,
                unit=oi.unit,
                glazing=oi.glazing,
                gross_weight=oi.gross_weight,
                net_weight=oi.net_weight,
                # Production specific
                planned_qty=oi.order_qty or 0,
                owner=user,
                created_by=user,
            )
            for oi in order.order_items.all()
        ]

        if items:
            ProductionItem.objects.bulk_create(items)

    # ========================
    # Create PurchaseOrder
    # ========================
    @transaction.atomic
    def create_purchase_order(
        self,
        *,
        pipeline,
        supplier=None,
        purchase_order_date=None,
        user=None,
        copy_items=True,
        force=False,
        auto_update_status=False,
        **extra_fields,
    ):
        """
        Create a PurchaseOrder for the pipeline

        Args:
            pipeline: The parent Pipeline instance
            supplier: Supplier for the purchase
            purchase_order_date: Purchase order date
            user: User creating the purchase order
            copy_items: Whether to copy OrderItems to PurchaseItems
            force: Force creation even if purchase already exists
            auto_update_status: Whether to auto-transition pipeline status
            **extra_fields: Additional fields

        Returns:
            PurchaseOrder instance
        """
        from ..models.purchase import PurchaseOrder
        from ..models.pipeline import PipelineType
        from django.utils import timezone

        # Validate pipeline type
        if pipeline.pipeline_type == PipelineType.PRODUCTION_FLOW:
            raise ValidationError(
                "Cannot create PurchaseOrder for PRODUCTION_FLOW pipeline. "
                "Use PURCHASE_FLOW or HYBRID_FLOW."
            )

        # Idempotency check
        if not force and pipeline.purchase_orders.filter(deleted__isnull=True).exists():
            raise ValidationError("PurchaseOrder already exists for this pipeline")

        order = pipeline.order

        # Create PurchaseOrder
        purchase = PurchaseOrder.objects.create_with_user(
            user=user,
            pipeline=pipeline,
            related_order=order,  # For backward compatibility
            supplier=supplier,
            purchase_order_date=purchase_order_date or timezone.now().date(),
            # Copy logistics info from order
            etd=order.etd,
            loading_port=order.loading_port,
            destination_port=order.destination_port,
            shipment_term=order.shipment_term,
            inco_terms=order.inco_terms,
            # Copy financial info from order
            currency=order.currency,
            deposit=order.deposit,
            balance=order.balance,
            comment=order.comment,
            **extra_fields,
        )

        # Auto-copy OrderItems to PurchaseItems
        if copy_items:
            self._create_purchase_items(purchase, order, user)

        # Auto-update pipeline status based on pipeline_type
        if auto_update_status:
            self._auto_transition_pipeline_for_purchase(pipeline, user)

        return purchase

    def _auto_transition_pipeline_for_purchase(self, pipeline, user=None):
        """Auto-transition pipeline status when purchase order is created."""
        from ..models.pipeline import PipelineType, PipelineStatusType
        from ..services.pipeline_state_service import PipelineStateService

        # Determine target status based on pipeline type
        target_status = None
        if pipeline.pipeline_type == PipelineType.PURCHASE_FLOW:
            if pipeline.status == PipelineStatusType.ORDER_CONFIRMED:
                target_status = PipelineStatusType.IN_PURCHASE
        elif pipeline.pipeline_type == PipelineType.HYBRID_FLOW:
            if pipeline.status == PipelineStatusType.ORDER_CONFIRMED:
                target_status = PipelineStatusType.IN_PURCHASE_AND_PRODUCTION

        if target_status:
            PipelineStateService.transition(
                pipeline=pipeline,
                target_status=target_status,
                user=user,
            )

    def _create_purchase_items(self, purchase, order, user=None):
        """Copy OrderItems to PurchaseItems"""
        from ..models.purchase import PurchaseItem

        items = [
            PurchaseItem(
                purchase_order=purchase,
                order_item=oi,
                # Copy base item fields
                product_name=oi.product_name,
                specification=oi.specification,
                outter_packaging=oi.outter_packaging,
                inner_packaging=oi.inner_packaging,
                size=oi.size,
                unit=oi.unit,
                glazing=oi.glazing,
                gross_weight=oi.gross_weight,
                net_weight=oi.net_weight,
                # Purchase specific
                purchase_qty=oi.order_qty or 0,
                total_gross_weight=oi.total_gross_weight,
                total_net_weight=oi.total_net_weight,
                unit_price=oi.unit_price,
                total_price=oi.total_price,
                owner=user,
                created_by=user,
            )
            for oi in order.order_items.all()
        ]

        if items:
            PurchaseItem.objects.bulk_create(items)

    # ========================
    # Create OutboundOrder
    # ========================
    @transaction.atomic
    def create_outbound_order(
        self,
        *,
        pipeline,
        outbound_date=None,
        container_no=None,
        seal_no=None,
        destination_port=None,
        logistics_provider=None,
        remark=None,
        user=None,
        copy_items=True,
        force=False,
        auto_update_status=False,
        **extra_fields,
    ):
        """
        Create an OutboundOrder for the pipeline

        Args:
            pipeline: The parent Pipeline instance
            outbound_date: Outbound/shipment date
            container_no: Container number
            seal_no: Seal number
            destination_port: Destination port
            logistics_provider: Logistics provider name
            remark: Additional remarks
            user: User creating the outbound order
            copy_items: Whether to copy OrderItems to OutboundItems
            force: Force creation even if outbound already exists
            auto_update_status: Whether to auto-transition pipeline status
            **extra_fields: Additional fields

        Returns:
            OutboundOrder instance
        """
        from ..models.outbound import OutboundOrder

        # Validate prerequisites (production or purchase must exist)
        production_orders = pipeline.production_orders.filter(deleted__isnull=True)
        purchase_orders = pipeline.purchase_orders.filter(deleted__isnull=True)

        if not force:
            from ..models.pipeline import PipelineType

            if pipeline.pipeline_type == PipelineType.PRODUCTION_FLOW:
                if not production_orders.exists():
                    raise ValidationError(
                        "Must create ProductionOrder before OutboundOrder in PRODUCTION_FLOW"
                    )
            elif pipeline.pipeline_type == PipelineType.PURCHASE_FLOW:
                if not purchase_orders.exists():
                    raise ValidationError(
                        "Must create PurchaseOrder before OutboundOrder in PURCHASE_FLOW"
                    )

        # Idempotency check
        if not force and pipeline.outbound_orders.filter(deleted__isnull=True).exists():
            raise ValidationError("OutboundOrder already exists for this pipeline")

        order = pipeline.order

        # Create OutboundOrder
        outbound = OutboundOrder.objects.create_with_user(
            user=user,
            pipeline=pipeline,
            outbound_date=outbound_date,
            container_no=container_no,
            seal_no=seal_no,
            destination_port=destination_port or order.destination_port,
            logistics_provider=logistics_provider,
            remark=remark or pipeline.remark or order.comment,
            **extra_fields,
        )

        # Auto-copy OrderItems to OutboundItems
        if copy_items:
            self._create_outbound_items(outbound, order, user)

        # Auto-update pipeline status based on pipeline_type
        if auto_update_status:
            self._auto_transition_pipeline_for_outbound(pipeline, user)

        return outbound

    def _auto_transition_pipeline_for_outbound(self, pipeline, user=None):
        """Auto-transition pipeline status when outbound order is created."""
        from ..models.pipeline import PipelineStatusType
        from ..services.pipeline_state_service import PipelineStateService

        # Outbound can be created from production_completed, purchase_completed,
        # or purchase_and_production_completed states
        target_status = None
        if pipeline.status in (
            PipelineStatusType.PRODUCTION_COMPLETED,
            PipelineStatusType.PURCHASE_COMPLETED,
            PipelineStatusType.PURCHASE_AND_PRODUCTION_COMPLETED,
        ):
            target_status = PipelineStatusType.IN_OUTBOUND

        if target_status:
            PipelineStateService.transition(
                pipeline=pipeline,
                target_status=target_status,
                user=user,
            )

    def _create_outbound_items(self, outbound, order, user=None):
        """Copy OrderItems to OutboundItems"""
        from ..models.outbound import OutboundItem

        items = [
            OutboundItem(
                outbound_order=outbound,
                order_item=oi,
                # Copy base item fields
                product_name=oi.product_name,
                specification=oi.specification,
                outter_packaging=oi.outter_packaging,
                inner_packaging=oi.inner_packaging,
                size=oi.size,
                unit=oi.unit,
                glazing=oi.glazing,
                gross_weight=oi.gross_weight,
                net_weight=oi.net_weight,
                # Outbound specific - initialize with 0
                outbound_qty=0,
                owner=user,
                created_by=user,
            )
            for oi in order.order_items.all()
        ]

        if items:
            OutboundItem.objects.bulk_create(items)
