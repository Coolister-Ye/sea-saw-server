from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser
from ..parsers import NestedMultiPartParser
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from ..models.purchase import PurchaseOrder
from ..serializers.purchase import PurchaseOrderSerializerForAdmin
from ..serializers.pipeline import (
    PipelineSerializerForAdmin,
    PipelineSerializerForSales,
    PipelineSerializerForProduction,
    PipelineSerializerForWarehouse,
)
from ..permissions import IsAdmin, IsSale
from ..metadata import BaseMetadata
from ..mixins import ReturnRelatedMixin


class NestedPurchaseOrderViewSet(ReturnRelatedMixin, ModelViewSet):
    """
    ViewSet for PurchaseOrder operations within the context of a Pipeline.

    This viewset handles CRUD operations on purchase orders that belong to
    a specific pipeline. It automatically sets pipeline based on:
    - Query parameter: ?pipeline=<pipeline_id>
    - Request body: {"pipeline": <pipeline_id>}

    URL: /api/sea-saw-crm/nested-purchase-orders/
    """

    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializerForAdmin
    parser_classes = (JSONParser, NestedMultiPartParser, FormParser)
    filter_backends = (OrderingFilter, SearchFilter, filters.DjangoFilterBackend)
    permission_classes = [
        IsAuthenticated,
        IsAdmin | IsSale,
    ]
    metadata_class = BaseMetadata

    # ReturnRelatedMixin 配置 - 返回完整的 Pipeline 数据(包含所有嵌套子实体)
    related_field_name = "pipeline"
    role_related_serializer_map = {
        "ADMIN": PipelineSerializerForAdmin,
        "SALE": PipelineSerializerForSales,
        "PRODUCTION": PipelineSerializerForProduction,
        "WAREHOUSE": PipelineSerializerForWarehouse,
    }
    search_fields = ["purchase_code", "supplier__name", "comment"]
    ordering_fields = [
        "purchase_code",
        "purchase_order_date",
        "status",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter by pipeline if provided"""
        # Filter out soft-deleted records
        base_queryset = super().get_queryset().filter(deleted__isnull=True)

        # Support filtering by pipeline via query param
        pipeline_id = self.request.query_params.get('pipeline')
        if pipeline_id:
            base_queryset = base_queryset.filter(pipeline_id=pipeline_id)

        return base_queryset

    def get_serializer(self, *args, **kwargs):
        """
        Auto-inject pipeline into data if provided via query params.
        This ensures consistent behavior for create/update operations.
        """
        # Get pipeline from query params
        pipeline_id = self.request.query_params.get('pipeline')

        if pipeline_id and 'data' in kwargs:
            # Inject pipeline into request data
            # Handle both dict and QueryDict
            data = kwargs['data']
            if hasattr(data, '_mutable'):
                # QueryDict - make mutable
                data._mutable = True
                data['pipeline'] = pipeline_id
                data._mutable = False
            elif isinstance(data, dict):
                # Regular dict
                data['pipeline'] = pipeline_id
            kwargs['data'] = data

        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        """
        Nested purchase order endpoint does not support CREATE operations.
        Purchase orders and items must be created through the Pipeline API.
        This endpoint is only for UPDATE operations on existing purchase orders.

        Args:
            serializer: The serializer instance (not used as creation is blocked)

        Raises:
            ValidationError: Always raised to prevent creation through nested endpoint
        """
        raise ValidationError(
            {
                "detail": "Cannot create purchase orders through nested endpoint. "
                "Purchase orders must be created through the Pipeline API (POST /api/sea-saw-crm/pipelines/). "
                "Use this endpoint only for updating existing purchase orders."
            }
        )

    def perform_update(self, serializer):
        """
        Validate update operations:
        1. Prevent changing pipeline of an existing purchase order
        2. Prevent creating new purchase_items (only allow updates to existing items)
        """
        instance = self.get_object()
        new_pipeline = serializer.validated_data.get('pipeline')

        # Validate pipeline hasn't changed
        if new_pipeline and instance.pipeline_id != new_pipeline.id:
            raise ValidationError(
                {
                    'pipeline': f'Cannot change pipeline from {instance.pipeline_id} '
                                f'to {new_pipeline.id}. Use standalone API to reassign.'
                }
            )

        # Validate no new purchase_items are being created
        # Use initial_data since 'id' is read_only and won't be in validated_data
        purchase_items_data = serializer.initial_data.get('purchase_items')
        if purchase_items_data:
            existing_item_ids = set(instance.purchase_items.values_list('id', flat=True))

            for item_data in purchase_items_data:
                item_id = item_data.get('id')
                # If item has no id or id not in existing items, it's a new item - reject
                if not item_id or int(item_id) not in existing_item_ids:
                    raise ValidationError(
                        {
                            'purchase_items': 'Cannot create new purchase items through nested endpoint. '
                            'Purchase items must be created through the Pipeline API. '
                            'You can only update existing purchase items here.'
                        }
                    )

        serializer.save()
