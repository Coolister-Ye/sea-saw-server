from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..base import BaseSerializer
from ...models.production import ProductionItem


def order_item_readonly_field(field_name, label):
    return serializers.CharField(
        source=f"order_item.{field_name}",
        read_only=True,
        label=label,
    )


class ProductionItemSerializer(BaseSerializer):
    """ProductionItem base serializer."""

    # -------- order_item display fields --------
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
        model = ProductionItem
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
            "planned_qty",
            "produced_qty",
        ]


class ProductionItemSerializerForAdmin(ProductionItemSerializer):
    """Admin 完全读写"""

    pass


# ===============================
# FIXED VERSION
# ===============================
class ProductionItemSerializerForSales(ProductionItemSerializer):
    """Sales: read-only"""

    class Meta(ProductionItemSerializer.Meta):
        read_only_fields = ProductionItemSerializer.Meta.fields


class ProductionItemSerializerForProduction(ProductionItemSerializer):
    """Production: editable quantities"""

    pass


class ProductionItemSerializerForWarehouse(ProductionItemSerializer):
    """Warehouse: read-only"""

    class Meta(ProductionItemSerializer.Meta):
        read_only_fields = ProductionItemSerializer.Meta.fields
