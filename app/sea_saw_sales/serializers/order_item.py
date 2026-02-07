from django.utils.translation import gettext_lazy as _

from sea_saw_base.serializers import BaseSerializer
from ..models import OrderItem


class OrderItemSerializer(BaseSerializer):
    """Base serializer for OrderItem."""

    class Meta:
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
        ]


class OrderItemSerializerForAdmin(OrderItemSerializer):
    """Admin can edit all fields."""

    class Meta(OrderItemSerializer.Meta):
        model = OrderItem
        fields = OrderItemSerializer.Meta.fields


class OrderItemSerializerForSales(OrderItemSerializer):
    """Sales can edit all fields"""

    class Meta(OrderItemSerializer.Meta):
        fields = OrderItemSerializer.Meta.fields


class OrderItemSerializerForProduction(OrderItemSerializer):
    """Production department: fully read-only view."""

    class Meta(OrderItemSerializer.Meta):
        fields = OrderItemSerializer.Meta.fields
        read_only_fields = OrderItemSerializer.Meta.fields


class OrderItemSerializerForWarehouse(OrderItemSerializer):
    """Warehouse: fully read-only."""

    class Meta(OrderItemSerializer.Meta):
        fields = OrderItemSerializer.Meta.fields
        read_only_fields = OrderItemSerializer.Meta.fields
