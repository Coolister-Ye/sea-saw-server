from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser
from sea_saw_base.parsers import NestedMultiPartParser

from sea_saw_pipeline.models.pipeline import Pipeline
from sea_saw_pipeline.serializers.pipeline import (
    PipelineSerializerForAdmin,
    PipelineSerializerForProduction,
    PipelineSerializerForSales,
    PipelineSerializerForWarehouse,
)
from sea_saw_base.permissions import IsAdmin, IsSale, IsProduction, IsWarehouse
from sea_saw_pipeline.permissions import (
    PipelineAdminPermission,
    PipelineSalePermission,
    PipelineProductionPermission,
    PipelineWarehousePermission,
    CanTransitionPipeline,
)

from ..constants import PipelineStatus, PipelineTypeAccess
from sea_saw_base.metadata import BaseMetadata
from sea_saw_base.mixins import MultipartNestedDataMixin


class PipelineViewSet(
    MultipartNestedDataMixin,
    ModelViewSet,
):
    """
    ViewSet for Pipeline - Business Process Orchestration

    Pipeline作为业务流程的主入口，串联整个订单处理流程:
    1. Order (销售订单)
    2. ProductionOrder / PurchaseOrder (生产订单/采购订单)
    3. OutboundOrder (出库订单)
    4. Payments (付款记录)

    Features:
    - Role-based serializer selection (ADMIN, SALE, PRODUCTION, WAREHOUSE)
    - Role-based queryset filtering
    - State transition management
    - Sub-entity creation (production/purchase/outbound orders)
    - File upload support via MultipartNestedDataMixin

    URL: /api/sea-saw-crm/pipelines/
    """

    queryset = Pipeline.objects.all()
    metadata_class = BaseMetadata
    filter_backends = (OrderingFilter, SearchFilter, filters.DjangoFilterBackend)
    parser_classes = (JSONParser, NestedMultiPartParser, FormParser)

    permission_classes = [
        IsAuthenticated,
        PipelineAdminPermission
        | PipelineSalePermission
        | PipelineProductionPermission
        | PipelineWarehousePermission,
    ]

    # Only these actions will parse nested multipart data
    multipart_nested_actions = {"create", "update", "partial_update"}

    # Role-based serializer mapping
    role_serializer_map = {
        "ADMIN": PipelineSerializerForAdmin,
        "SALE": PipelineSerializerForSales,
        "PRODUCTION": PipelineSerializerForProduction,
        "WAREHOUSE": PipelineSerializerForWarehouse,
    }

    # Search and filtering configuration
    search_fields = ["pipeline_code", "remark", "order__order_code", "contact__name"]
    filterset_fields = ["status", "pipeline_type", "order_date", "contact"]
    ordering_fields = [
        "pipeline_code",
        "status",
        "pipeline_type",
        "order_date",
        "confirmed_at",
        "completed_at",
        "total_amount",
        "paid_amount",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    # =====================
    # Core Overrides
    # =====================
    def get_serializer_class(self):
        """Select serializer based on user role"""
        role = getattr(self.request.user.role, "role_type", None)
        serializer = self.role_serializer_map.get(role)
        if not serializer:
            raise PermissionDenied("No serializer for this role")
        return serializer

    def create(self, request, *args, **kwargs):
        """
        Create a new Pipeline

        Supports auto_create_order parameter to automatically create an associated Order.

        Request body:
        {
            "auto_create_order": true,  # Optional: auto-create order
            "order_date": "2024-01-15",
            "contact_id": 1,
            ...
        }
        """
        data = (
            request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        )
        auto_create_order = data.pop("auto_create_order", False)

        # Convert string "true"/"false" to boolean
        if isinstance(auto_create_order, str):
            auto_create_order = auto_create_order.lower() == "true"

        if auto_create_order:
            # Use manager method to create pipeline with auto-created order
            pipeline = Pipeline.objects.create_with_auto_order(
                user=request.user,
                order_date=data.get("order_date"),
                contact_id=data.get("contact_id"),
                company_id=data.get("company_id"),  # Pass company_id
                currency=data.get("currency", "USD"),
                total_amount=data.get("total_amount", 0),
                remark=data.get("remark"),
                pipeline_type=data.get("pipeline_type"),
            )
            serializer = self.get_serializer(pipeline)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        """
        Filter queryset based on user role:
        - ADMIN: All pipelines (all states)
        - SALE: All pipelines (all states, but filtered by ownership)
        - PRODUCTION: ORDER_CONFIRMED and all subsequent states
        - WAREHOUSE: PRODUCTION_COMPLETED and all subsequent states
        """
        # Filter out soft-deleted records
        base_queryset = super().get_queryset().filter(deleted__isnull=True)

        user = self.request.user
        role = getattr(user.role, "role_type", None)

        if role == "SALE":
            # SALE: see all states, but only for pipelines owned by visible users
            visible_users = (
                user.get_all_visible_users()
                if callable(getattr(user, "get_all_visible_users", None))
                else [user]
            )
            return base_queryset.filter(owner__in=visible_users)

        if role == "PRODUCTION":
            # PRODUCTION: can see production-related pipeline types and relevant states
            return base_queryset.filter(
                pipeline_type__in=PipelineTypeAccess.PRODUCTION_VISIBLE,
                status__in=PipelineStatus.PRODUCTION_VISIBLE,
            )

        if role == "WAREHOUSE":
            # WAREHOUSE: can see all pipeline types (all need outbound) and relevant states
            return base_queryset.filter(
                pipeline_type__in=PipelineTypeAccess.WAREHOUSE_VISIBLE,
                status__in=PipelineStatus.WAREHOUSE_VISIBLE,
            )

        # ADMIN: see all pipelines (all states)
        return base_queryset

    # =====================
    # Custom Actions - State Transitions
    # =====================
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanTransitionPipeline],
    )
    def transition(self, request, pk=None):
        """
        Transition pipeline to target status

        Request body:
        {
            "target_status": "order_confirmed"
        }

        Returns:
        - 200: Pipeline data with new status
        - 400: Invalid transition
        """
        pipeline = self.get_object()
        target_status = request.data.get("target_status")

        if not target_status:
            return Response(
                {"detail": "target_status is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            success = pipeline.transition(target_status, user=request.user)
            if not success:
                return Response(
                    {"detail": f"Failed to transition to {target_status}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(pipeline)
        return Response(serializer.data)

    # =====================
    # Custom Actions - Sub-Entity Creation
    # =====================
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsSale | IsAdmin],
    )
    def create_order(self, request, pk=None):
        """
        Create an order for this pipeline

        This is useful when pipeline is created first without an order,
        or when duplicating an order workflow.

        Request body:
        {
            "order_code": "ORD-2024-001",
            "order_date": "2024-01-15",
            "contact": <contact_id>,
            "copy_items": true,
            "force": false,
            ...
        }

        Returns:
        - 201: Updated pipeline data with new order
        - 400: Invalid request or order already exists
        """
        pipeline = self.get_object()

        try:
            pipeline.create_order(user=request.user, **request.data)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(pipeline)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsProduction | IsAdmin],
    )
    def create_production(self, request, pk=None):
        """
        Create a production order for this pipeline

        Request body:
        {
            "planned_date": "2024-01-15",
            "production_items": [...],
            "auto_update_status": true  // Optional: auto-transition pipeline to IN_PRODUCTION
        }

        Returns:
        - 201: Updated pipeline data with new production order
        - 400: Invalid request or pipeline state
        """
        pipeline = self.get_object()

        try:
            pipeline.create_production_order(user=request.user, **request.data)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Refresh pipeline to get updated status if auto_update_status was used
        pipeline.refresh_from_db()
        serializer = self.get_serializer(pipeline)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsSale | IsAdmin],
    )
    def create_purchase(self, request, pk=None):
        """
        Create a purchase order for this pipeline

        Request body:
        {
            "supplier": <supplier_id>,
            "purchase_order_date": "2024-01-15",
            "purchase_items": [...],
            "auto_update_status": true  // Optional: auto-transition pipeline to IN_PURCHASE
        }

        Returns:
        - 201: Updated pipeline data with new purchase order
        - 400: Invalid request or pipeline state
        """
        pipeline = self.get_object()

        try:
            pipeline.create_purchase_order(user=request.user, **request.data)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Refresh pipeline to get updated status if auto_update_status was used
        pipeline.refresh_from_db()
        serializer = self.get_serializer(pipeline)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsWarehouse | IsAdmin],
    )
    def create_outbound(self, request, pk=None):
        """
        Create an outbound order for this pipeline

        Request body:
        {
            "outbound_date": "2024-01-15",
            "outbound_items": [...],
            "auto_update_status": true  // Optional: auto-transition pipeline to IN_OUTBOUND
        }

        Returns:
        - 201: Updated pipeline data with new outbound order
        - 400: Invalid request or pipeline state
        """
        pipeline = self.get_object()

        try:
            pipeline.create_outbound_order(user=request.user, **request.data)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Refresh pipeline to get updated status if auto_update_status was used
        pipeline.refresh_from_db()
        serializer = self.get_serializer(pipeline)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # =====================
    # Custom Actions - Data Aggregation
    # =====================
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsAdmin | IsSale],
    )
    def update_amounts(self, request, pk=None):
        """
        Manually trigger update of total_amount and paid_amount

        Returns:
        - 200: Updated pipeline data with refreshed amounts
        """
        pipeline = self.get_object()

        pipeline.update_total_amount()
        pipeline.update_paid_amount()
        pipeline.refresh_from_db()

        serializer = self.get_serializer(pipeline)
        return Response(serializer.data)
