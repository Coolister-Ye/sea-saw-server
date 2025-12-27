from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..base import BaseSerializer
from ...models.outbound import OutboundItem


# =====================================================
# Field factory
# =====================================================


def order_item_readonly_field(field_name, label):
    return serializers.CharField(
        source=f"order_item.{field_name}",
        read_only=True,
        label=label,
    )


# =====================================================
# Base Serializer
# =====================================================


class OutboundItemSerializer(BaseSerializer):
    """Base serializer for outbound items."""

    # -------- order_item fields (read-only) --------
    product_name = order_item_readonly_field("product_name", _("Product Name"))
    specification = order_item_readonly_field("specification", _("Specification"))
    outter_packaging = order_item_readonly_field(
        "outter_packaging", _("Outter Packaging")
    )
    inner_packaging = order_item_readonly_field("inner_packaging", _("Inner Packaging"))
    size = order_item_readonly_field("size", _("Size"))
    unit = order_item_readonly_field("unit", _("Unit"))
    glazing = order_item_readonly_field("glazing", _("Glazing"))
    gross_weight = order_item_readonly_field("gross_weight", _("Gross Weight"))
    net_weight = order_item_readonly_field("net_weight", _("Net Weight"))
    order_qty = order_item_readonly_field("order_qty", _("Order Quantity"))
    total_gross_weight = order_item_readonly_field(
        "total_gross_weight", _("Total Gross Weight")
    )
    total_net_weight = order_item_readonly_field(
        "total_net_weight", _("Total Net Weight")
    )

    class Meta:
        model = OutboundItem
        fields = [
            "id",
            # order_item fields
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
            # outbound fields
            "outbound_qty",
            "outbound_net_weight",
            "outbound_gross_weight",
        ]


# =====================================================
# Role-based serializers
# =====================================================


class OutboundItemSerializerForAdmin(OutboundItemSerializer):
    """Admin: full access"""

    pass


class OutboundItemSerializerForSales(OutboundItemSerializer):
    """Sales: all fields read-only"""

    class Meta(OutboundItemSerializer.Meta):
        read_only_fields = OutboundItemSerializer.Meta.fields


class OutboundItemSerializerForWarehouse(OutboundItemSerializer):
    """
    Warehouse:
    - order_item fields → read-only
    - outbound fields → editable
    """

    class Meta(OutboundItemSerializer.Meta):
        read_only_fields = [
            "product_name",
            "specification",
            "packaging",
            "inner_packaging",
            "size",
            "unit",
            "glazing",
            "gross_weight",
            "net_weight",
            "order_qty",
            "total_gross_weight",
            "total_net_weight",
        ]


class OutboundItemSerializerForProduction(OutboundItemSerializer):
    """Production: all fields read-only"""

    class Meta(OutboundItemSerializer.Meta):
        read_only_fields = OutboundItemSerializer.Meta.fields
