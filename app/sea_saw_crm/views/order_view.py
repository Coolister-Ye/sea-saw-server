from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser
from ..parsers import NestedMultiPartParser
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from ..models.order import Order
from ..models.pipeline import Pipeline
from ..serializers.order import (
    OrderSerializerForOrderView,
    OrderSerializerForAdmin,
    OrderSerializerForSales,
)
from ..serializers.pipeline import (
    PipelineSerializerForAdmin,
    PipelineSerializerForSales,
)
from ..permissions import OrderAdminPermission, OrderSalePermission
from ..metadata import OrderMetadata
from ..mixins import ReturnRelatedMixin


class OrderViewSet(ModelViewSet):
    """
    ViewSet for Order (standalone access).

    Note: Pipeline is now the main entry point for business workflows.
    This ViewSet provides direct access to Order entities for:
    - Legacy API compatibility
    - Direct order management when not using pipeline workflow
    - Read-only access for reporting and queries

    For new workflows, use PipelineViewSet instead.
    """

    queryset = Order.objects.all()
    serializer_class = OrderSerializerForOrderView
    filter_backends = (OrderingFilter, SearchFilter, filters.DjangoFilterBackend)
    permission_classes = [
        IsAuthenticated,
        OrderAdminPermission | OrderSalePermission,
    ]
    metadata_class = OrderMetadata
    search_fields = ["order_code", "remark", "comment", "contact__name"]
    ordering_fields = [
        "order_code",
        "order_date",
        "delivery_date",
        "total_amount",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        # Filter out soft-deleted records
        return super().get_queryset().filter(deleted__isnull=True)

    def perform_update(self, serializer):
        """
        Update order with automatic pipeline synchronization.

        When order fields are updated, related pipeline fields are automatically synced:
        - contact → pipeline.contact
        - order_date → pipeline.order_date
        - total_amount → pipeline.total_amount

        The synchronization is handled by the serializer's update() method.
        """
        serializer.save()


class NestedOrderViewSet(ReturnRelatedMixin, OrderViewSet):
    """
    ViewSet for Order operations nested under a specific Pipeline.

    Handles CRUD operations for orders that belong to a specific pipeline.
    Related pipeline can be provided via:
      - Query parameter: ?related_pipeline=<pipeline_id>
      - Request body: {"related_pipeline": <pipeline_id>}

    URL: /api/sea-saw-crm/nested-orders/
    """

    parser_classes = (JSONParser, NestedMultiPartParser, FormParser)

    role_serializer_map = {
        "ADMIN": OrderSerializerForAdmin,
        "SALE": OrderSerializerForSales,
    }

    # ReturnRelatedMixin configuration
    related_field_name = "pipeline"
    role_related_serializer_map = {
        "ADMIN": PipelineSerializerForAdmin,
        "SALE": PipelineSerializerForSales,
    }

    def get_queryset(self):
        """
        Filter orders by related_pipeline if provided in query params.
        Soft-deleted records are already filtered by parent class.
        """
        qs = super().get_queryset()
        related_pipeline_id = self.request.query_params.get("related_pipeline")
        if related_pipeline_id:
            # Use 'pipeline' since it's a OneToOne reverse relation from Pipeline to Order
            qs = qs.filter(pipeline=related_pipeline_id)
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
        Get serializer instance.

        Note: related_pipeline is provided via query params for filtering and validation,
        but is not injected into serializer data since it's a reverse OneToOne relation
        that cannot be set directly on Order.
        """
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):  # noqa: ARG002
        """
        Nested order endpoint does not support CREATE operations.
        Orders must be created through the Pipeline API.
        This endpoint is only for UPDATE operations on existing orders.

        Raises:
            ValidationError: Always raised to prevent creation through nested endpoint
        """
        raise ValidationError(
            {
                "detail": "Cannot create orders through nested endpoint. "
                "Orders must be created through the Pipeline API (POST /api/sea-saw-crm/pipelines/). "
                "Use this endpoint only for updating existing orders."
            }
        )

    def perform_update(self, serializer):
        """
        Validate and update order with automatic pipeline synchronization:
        1. Prevent changing related_pipeline of an existing order
        2. Prevent creating new order_items (only allow updates to existing items)
        3. Automatically sync updated fields to related pipeline
        """
        instance = self.get_object()

        # Validate related_pipeline hasn't changed
        # Get the pipeline ID from query params (since it's not in serializer data)
        requested_pipeline_id = self.request.query_params.get("related_pipeline")
        current_pipeline_id = (
            getattr(instance.pipeline, "id", None)
            if hasattr(instance, "pipeline")
            else None
        )

        if requested_pipeline_id and current_pipeline_id != int(requested_pipeline_id):
            raise ValidationError(
                {
                    "related_pipeline": f"Cannot change related_pipeline from {current_pipeline_id} "
                    f"to {requested_pipeline_id}. Use standalone API to reassign."
                }
            )

        # Save through serializer, which handles pipeline synchronization
        serializer.save()

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
