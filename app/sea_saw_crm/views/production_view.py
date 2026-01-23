from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser
from ..parsers import NestedMultiPartParser
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from ..models.production import ProductionOrder
from ..models.pipeline import Pipeline
from ..serializers.production import (
    ProductionOrderSerializerForProductionView,
    ProductionOrderSerializerForAdmin,
    ProductionOrderSerializerForSales,
    ProductionOrderSerializerForProduction,
    ProductionOrderSerializerForWarehouse,
)
from ..serializers.pipeline import (
    PipelineSerializerForAdmin,
    PipelineSerializerForSales,
    PipelineSerializerForProduction,
    PipelineSerializerForWarehouse,
)
from ..permissions import IsAdmin, IsProduction
from ..metadata import BaseMetadata
from ..mixins import ReturnRelatedMixin


class ProductionOrderViewSet(ModelViewSet):
    """
    ViewSet for ProductionOrder.
    Only accessible by ADMIN and PRODUCTION roles.
    """

    queryset = ProductionOrder.objects.all()
    serializer_class = ProductionOrderSerializerForProductionView
    filter_backends = (OrderingFilter, SearchFilter, filters.DjangoFilterBackend)
    permission_classes = [
        IsAuthenticated,
        IsAdmin | IsProduction,
    ]
    metadata_class = BaseMetadata
    search_fields = ["production_code", "remark", "comment"]
    ordering_fields = [
        "production_code",
        "status",
        "planned_date",
        "start_date",
        "end_date",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        # Filter out soft-deleted records
        return super().get_queryset().filter(deleted__isnull=True)

    # -----------------------------
    # Custom actions
    # -----------------------------
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsProduction | IsAdmin],
    )
    def start_production(self, request, pk=None):
        """
        Start production (change status from DRAFT to ACTIVE).
        Only PRODUCTION and ADMIN can perform this action.
        """
        production_order = self.get_object()

        if production_order.status != "draft":
            return Response(
                {"detail": "Can only start production from draft status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        production_order.status = "active"
        if not production_order.start_date:
            from django.utils import timezone

            production_order.start_date = timezone.now().date()
        production_order.save()

        serializer = self.get_serializer(production_order)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsProduction | IsAdmin],
    )
    def finish_production(self, request, pk=None):
        """
        Finish production (change status from ACTIVE to COMPLETED).
        Only PRODUCTION and ADMIN can perform this action.
        """
        production_order = self.get_object()

        if production_order.status != "active":
            return Response(
                {"detail": "Can only finish production that is active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        production_order.status = "completed"
        if not production_order.end_date:
            from django.utils import timezone

            production_order.end_date = timezone.now().date()
        production_order.save()

        serializer = self.get_serializer(production_order)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsProduction | IsAdmin],
    )
    def report_issue(self, request, pk=None):
        """
        Report issue on production (change status to ISSUE_REPORTED).
        Only PRODUCTION and ADMIN can perform this action.
        """
        production_order = self.get_object()

        if production_order.status != "active":
            return Response(
                {"detail": "Can only report issue for active production"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        production_order.status = "issue_reported"
        production_order.save()

        serializer = self.get_serializer(production_order)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsProduction | IsAdmin],
    )
    def resolve_issue(self, request, pk=None):
        """
        Resolve issue and resume production (change status from ISSUE_REPORTED to ACTIVE).
        Only PRODUCTION and ADMIN can perform this action.
        """
        production_order = self.get_object()

        if production_order.status != "issue_reported":
            return Response(
                {"detail": "Can only resolve issue for production with reported issue"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        production_order.status = "active"
        production_order.save()

        serializer = self.get_serializer(production_order)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsProduction | IsAdmin],
    )
    def report_issue(self, request, pk=None):
        """
        Report an issue with production (change status to ISSUE_REPORTED).
        Only PRODUCTION and ADMIN can perform this action.
        """
        production_order = self.get_object()

        issue_comment = request.data.get("comment", "")
        if issue_comment:
            production_order.comment = (
                f"{production_order.comment or ''}\n[ISSUE] {issue_comment}".strip()
            )

        production_order.status = "issue_reported"
        production_order.save()

        serializer = self.get_serializer(production_order)
        return Response(serializer.data)


class NestedProductionOrderViewSet(ReturnRelatedMixin, ProductionOrderViewSet):
    """
    ViewSet for ProductionOrder operations nested under a specific Pipeline.

    Handles CRUD operations for production orders that belong to a specific pipeline.
    Related pipeline can be provided via:
      - Query parameter: ?related_pipeline=<pipeline_id>
      - Request body: {"pipeline": <pipeline_id>}

    Inherits workflow actions from ProductionOrderViewSet:
      start_production, finish_production, pause_production,
      resume_production, report_issue

    URL: /api/sea-saw-crm/nested-production-orders/
    """

    parser_classes = (JSONParser, NestedMultiPartParser, FormParser)

    role_serializer_map = {
        "ADMIN": ProductionOrderSerializerForAdmin,
        "SALE": ProductionOrderSerializerForSales,
        "PRODUCTION": ProductionOrderSerializerForProduction,
        "WAREHOUSE": ProductionOrderSerializerForWarehouse,
    }

    # ReturnRelatedMixin configuration
    related_field_name = "pipeline"
    role_related_serializer_map = {
        "ADMIN": PipelineSerializerForAdmin,
        "SALE": PipelineSerializerForSales,
        "PRODUCTION": PipelineSerializerForProduction,
        "WAREHOUSE": PipelineSerializerForWarehouse,
    }

    def get_queryset(self):
        """
        Filter production orders by related_pipeline if provided in query params.
        Soft-deleted records are already filtered by parent class.
        """
        qs = super().get_queryset()
        related_pipeline_id = self.request.query_params.get("related_pipeline")
        if related_pipeline_id:
            qs = qs.filter(pipeline_id=related_pipeline_id)
        return qs

    def get_serializer_class(self):
        """
        Select serializer based on user role.
        """
        role = getattr(getattr(self.request.user, "role", None), "role_type", None)
        serializer_class = self.role_serializer_map.get(role)
        if not serializer_class:
            raise PermissionDenied(f"No serializer configured for role {role}")
        return serializer_class

    def get_serializer(self, *args, **kwargs):
        """
        Auto-inject pipeline from query params into request data if not present.
        """
        related_pipeline_id = self.request.query_params.get("related_pipeline")

        # Inject pipeline into request data
        data = kwargs.get("data")
        if related_pipeline_id and data:
            if hasattr(data, "_mutable"):  # QueryDict
                data._mutable = True
                data["pipeline"] = related_pipeline_id
                data._mutable = False
            elif isinstance(data, dict):
                data["pipeline"] = related_pipeline_id
            kwargs["data"] = data

        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):  # noqa: ARG002
        """
        Nested production order endpoint does not support CREATE operations.
        Production orders must be created through the Pipeline API.
        This endpoint is only for UPDATE operations on existing production orders.

        Raises:
            ValidationError: Always raised to prevent creation through nested endpoint
        """
        raise ValidationError(
            {
                "detail": "Cannot create production orders through nested endpoint. "
                "Production orders must be created through the Pipeline API (POST /api/sea-saw-crm/pipelines/). "
                "Use this endpoint only for updating existing production orders."
            }
        )

    def perform_update(self, serializer):
        """
        Validate update operations:
        1. Prevent changing pipeline of an existing production order
        2. Prevent creating new production_items (only allow updates to existing items)
        """
        instance = self.get_object()

        # Validate pipeline hasn't changed
        requested_pipeline_id = self.request.query_params.get("related_pipeline")
        current_pipeline_id = instance.pipeline_id

        if requested_pipeline_id and current_pipeline_id != int(requested_pipeline_id):
            raise ValidationError(
                {
                    "related_pipeline": f"Cannot change pipeline from {current_pipeline_id} "
                    f"to {requested_pipeline_id}. Use standalone API to reassign."
                }
            )

        # Validate no new production_items are being created
        # Use initial_data since 'id' is read_only and won't be in validated_data
        production_items_data = serializer.initial_data.get("production_items")
        if production_items_data:
            existing_item_ids = set(
                instance.production_items.values_list("id", flat=True)
            )

            for item_data in production_items_data:
                item_id = item_data.get("id")
                # If item has no id or id not in existing items, it's a new item - reject
                if not item_id or int(item_id) not in existing_item_ids:
                    raise ValidationError(
                        {
                            "production_items": "Cannot create new production items through nested endpoint. "
                            "Production items must be created through the Pipeline API. "
                            "You can only update existing production items here."
                        }
                    )

        super().perform_update(serializer)

    def _validate_pipeline_access(self, pipeline_id):
        """
        Ensure user has access to the related pipeline.
        Raises ValidationError if pipeline does not exist.
        """
        try:
            pipeline = Pipeline.objects.get(pk=pipeline_id)
        except Pipeline.DoesNotExist:
            raise ValidationError(
                {"related_pipeline": f"Pipeline {pipeline_id} does not exist"}
            )

        return pipeline
