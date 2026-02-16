from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from sea_saw_base.serializers import BaseSerializer
from sea_saw_warehouse.models import OutboundItem


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
    """
    Base serializer for outbound items.

    Fields from AbstarctItemBase are marked as read-only by default.
    Subclasses can override read_only_fields for different access patterns.
    """

    # -------- order_item field --------
    order_qty = order_item_readonly_field("order_qty", _("Order Quantity"))

    class Meta:
        model = OutboundItem
        fields = [
            "id",
            # AbstarctItemBase fields (from OutboundItem model)
            "product_name",
            "specification",
            "outter_packaging",
            "inner_packaging",
            "size",
            "unit",
            "glazing",
            "gross_weight",
            "net_weight",
            # order_item field
            "order_qty",
            # OutboundItem specific fields
            "outbound_qty",
            "outbound_gross_weight",
            "outbound_net_weight",
        ]


# =====================================================
# Role-based serializers
# =====================================================


class OutboundItemSerializerForAdmin(OutboundItemSerializer):
    """
    Admin: full access to outbound fields.
    AbstarctItemBase fields and order_qty remain read-only.
    """

    pass


class OutboundItemSerializerForSales(OutboundItemSerializer):
    """Sales: all fields read-only"""

    class Meta(OutboundItemSerializer.Meta):
        read_only_fields = OutboundItemSerializer.Meta.fields


class OutboundItemSerializerForWarehouse(OutboundItemSerializer):
    """
    Warehouse: can edit outbound fields.
    - AbstarctItemBase fields → read-only
    - order_qty → read-only
    - outbound_qty, outbound_gross_weight, outbound_net_weight → editable
    """

    pass


class OutboundItemSerializerForProduction(OutboundItemSerializer):
    """Production: all fields read-only"""

    class Meta(OutboundItemSerializer.Meta):
        read_only_fields = OutboundItemSerializer.Meta.fields
