from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from sea_saw_base.serializers import BaseSerializer
from ..models import ProductionItem

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


class ProductionItemSerializer(BaseSerializer):
    """
    Base serializer for production items.

    Fields from AbstarctItemBase are marked as read-only by default.
    Subclasses can override read_only_fields for different access patterns.
    """

    # -------- order_item field --------
    order_qty = order_item_readonly_field("order_qty", _("Order Quantity"))

    class Meta:
        model = ProductionItem
        fields = [
            "id",
            # AbstarctItemBase fields (from ProductionItem model)
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
            # ProductionItem specific fields
            "planned_qty",
            "produced_qty",
            "produced_gross_weight",
            "produced_net_weight",
        ]
        read_only_fields = [
            "product_name",
            "specification",
            "outter_packaging",
            "inner_packaging",
            "size",
            "unit",
            "glazing",
            "gross_weight",
            "net_weight",
        ]


# =====================================================
# Role-based serializers
# =====================================================


class ProductionItemSerializerForAdmin(ProductionItemSerializer):
    """
    Admin: full access to production fields.
    - AbstarctItemBase fields → read-only
    - order_qty → read-only
    - planned_qty, produced_qty, produced_gross_weight, produced_net_weight → editable
    """

    pass


class ProductionItemSerializerForSales(ProductionItemSerializer):
    """Sales: all fields read-only"""

    class Meta(ProductionItemSerializer.Meta):
        read_only_fields = ProductionItemSerializer.Meta.fields


class ProductionItemSerializerForProduction(ProductionItemSerializer):
    """
    Production: can edit production fields.
    - AbstarctItemBase fields → read-only
    - order_qty → read-only
    - planned_qty, produced_qty, produced_gross_weight, produced_net_weight → editable
    """

    pass


class ProductionItemSerializerForWarehouse(ProductionItemSerializer):
    """Warehouse: all fields read-only"""

    class Meta(ProductionItemSerializer.Meta):
        read_only_fields = ProductionItemSerializer.Meta.fields
