from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from sea_saw_base.serializers import BaseSerializer
from ..models import OrderItem

_decimal = dict(max_digits=14, decimal_places=3, read_only=True, allow_null=True, required=False)


class OrderItemIntegrationSerializer(BaseSerializer):
    """
    Read-only OrderItem serializer with aggregated stats from purchase/production/outbound items.
    Aggregations are pre-computed via Subquery annotations in OrderIntegrationViewSet.get_queryset().
    """

    purchase_qty_total = serializers.DecimalField(label=_("Purchase Qty (Total)"), **_decimal)
    purchase_price_total = serializers.DecimalField(label=_("Purchase Price (Total)"), **_decimal)

    planned_qty_total = serializers.DecimalField(label=_("Planned Qty (Total)"), **_decimal)
    produced_qty_total = serializers.DecimalField(label=_("Produced Qty (Total)"), **_decimal)
    produced_net_weight_total = serializers.DecimalField(label=_("Produced Net Weight (Total)"), **_decimal)
    produced_gross_weight_total = serializers.DecimalField(label=_("Produced Gross Weight (Total)"), **_decimal)

    outbound_qty_total = serializers.DecimalField(label=_("Outbound Qty (Total)"), **_decimal)
    outbound_net_weight_total = serializers.DecimalField(label=_("Outbound Net Weight (Total)"), **_decimal)
    outbound_gross_weight_total = serializers.DecimalField(label=_("Outbound Gross Weight (Total)"), **_decimal)

    class Meta(BaseSerializer.Meta):
        model = OrderItem
        fields = [
            "id",
            "product_name",
            "specification",
            "outter_packaging",
            "inner_packaging",
            "size",
            "unit",
            "glazing",
            "gross_weight",
            "net_weight",
            "order_qty",
            "total_gross_weight",
            "total_net_weight",
            "unit_price",
            "total_price",
            # Aggregated from purchase_items
            "purchase_qty_total",
            "purchase_price_total",
            # Aggregated from production_items
            "planned_qty_total",
            "produced_qty_total",
            "produced_net_weight_total",
            "produced_gross_weight_total",
            # Aggregated from outbound_items
            "outbound_qty_total",
            "outbound_net_weight_total",
            "outbound_gross_weight_total",
        ]
        read_only_fields = fields
