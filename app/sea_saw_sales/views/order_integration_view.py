from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters import rest_framework as filters
from django.db.models import Subquery, OuterRef, Sum, DecimalField, Prefetch

from ..models import Order, OrderItem
from ..serializers import OrderIntegrationSerializer
from ..permissions import OrderAdminPermission, OrderSalePermission
from ..filters import OrderFilter
from sea_saw_base.metadata import BaseMetadata
from sea_saw_procurement.models import PurchaseItem
from sea_saw_production.models import ProductionItem
from sea_saw_warehouse.models import OutboundItem


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


class OrderIntegrationViewSet(ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Order with integrated pipeline/outbound data.
    Exposes eta (latest from outbound_orders), pipeline_status, and per-item
    aggregated stats from purchase_items, production_items, outbound_items.
    """

    serializer_class = OrderIntegrationSerializer
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
            )
        )
