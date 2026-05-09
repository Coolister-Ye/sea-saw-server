from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import status
from django_filters import rest_framework as filters
from django.db.models import Subquery, OuterRef, Sum, DecimalField, Prefetch

from sea_saw_base.parsers import NestedMultiPartParser
from sea_saw_base.metadata import BaseMetadata
from sea_saw_export.mixins import ExportViewSetMixin
from sea_saw_procurement.models import PurchaseItem
from sea_saw_production.models import ProductionItem
from sea_saw_warehouse.models import OutboundItem
from sea_saw_pipeline.models import Pipeline

from ..models import Order, OrderItem
from ..serializers import OrderIntegrationSerializer
from ..permissions import OrderAdminPermission, OrderSalePermission
from ..filters import OrderFilter


def _sum_sub(model, field):
    """Correlated subquery: SUM(field) for rows matching order_item=OuterRef('pk')."""
    return Subquery(
        model.objects
        .filter(order_item=OuterRef("pk"))
        .values("order_item")
        .annotate(total=Sum(field))
        .values("total"),
        output_field=DecimalField(),
    )


class OrderIntegrationViewSet(ExportViewSetMixin, ModelViewSet):
    """
    ViewSet for Order with integrated pipeline/outbound data.
    Exposes eta (latest from outbound_orders), pipeline_status, and per-item
    aggregated stats from purchase_items, production_items, outbound_items.
    """

    serializer_class = OrderIntegrationSerializer
    parser_classes = (JSONParser, NestedMultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, OrderAdminPermission | OrderSalePermission]
    filter_backends = (OrderingFilter, SearchFilter, filters.DjangoFilterBackend)
    filterset_class = OrderFilter
    metadata_class = BaseMetadata
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
        annotated_items = OrderItem.objects.annotate(
            purchase_qty_total=_sum_sub(PurchaseItem, "purchase_qty"),
            purchase_price_total=_sum_sub(PurchaseItem, "total_price"),
            planned_qty_total=_sum_sub(ProductionItem, "planned_qty"),
            produced_qty_total=_sum_sub(ProductionItem, "produced_qty"),
            produced_net_weight_total=_sum_sub(ProductionItem, "produced_net_weight"),
            produced_gross_weight_total=_sum_sub(ProductionItem, "produced_gross_weight"),
            outbound_qty_total=_sum_sub(OutboundItem, "outbound_qty"),
            outbound_net_weight_total=_sum_sub(OutboundItem, "outbound_net_weight"),
            outbound_gross_weight_total=_sum_sub(OutboundItem, "outbound_gross_weight"),
        )

        return (
            Order.objects.filter(deleted__isnull=True)
            .select_related("pipeline")
            .prefetch_related(
                Prefetch("order_items", queryset=annotated_items),
                "pipeline__outbound_orders",
                "pipeline__purchase_orders",
                "pipeline__payments",
            )
        )

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=True, methods=["post"])
    def create_pipeline(self, request, pk=None):
        """
        Create a Pipeline for this Order.

        Returns:
            - 201: Pipeline created successfully, returns Order data
            - 400: Pipeline already exists for this Order
        """
        order = self.get_object()

        if hasattr(order, "pipeline") and order.pipeline:
            return Response(
                {
                    "error": "Pipeline already exists for this order",
                    "pipeline_id": order.pipeline.id,
                    "pipeline_code": order.pipeline.pipeline_code,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status == "cancelled":
            order.status = "draft"
            order.save(update_fields=["status", "updated_at"])

        pipeline_type = request.data.get("pipeline_type", "production_flow")

        Pipeline.objects.create(
            order=order,
            account=order.buyer,
            contact=order.contact,
            order_date=order.order_date,
            pipeline_type=pipeline_type,
            created_by=request.user,
            updated_by=request.user,
        )

        order.refresh_from_db()
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
