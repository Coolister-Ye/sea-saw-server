from django.utils.translation import gettext_lazy as _

from sea_saw_base.serializers import BaseSerializer
from ..models import PurchaseItem


# =====================================================
# Base Serializer
# =====================================================


class PurchaseItemSerializer(BaseSerializer):
    """
    Base serializer for purchase items.

    Fields from AbstarctItemBase are marked as read-only by default.
    Calculated fields (total_gross_weight, total_net_weight, total_price) are read-only.
    Subclasses can override read_only_fields for different access patterns.
    """

    class Meta:
        model = PurchaseItem
        fields = [
            "id",
            # AbstarctItemBase fields (from PurchaseItem model)
            "product_name",
            "specification",
            "outter_packaging",
            "inner_packaging",
            "size",
            "unit",
            "glazing",
            "gross_weight",
            "net_weight",
            # PurchaseItem specific fields
            "purchase_qty",
            "total_gross_weight",
            "total_net_weight",
            "unit_price",
            "total_price",
            # BaseModel fields
            "owner",
            "created_at",
            "updated_at",
        ]


# =====================================================
# Role-based serializers
# =====================================================


class PurchaseItemSerializerForAdmin(PurchaseItemSerializer):
    """
    Admin: full access to purchase fields.
    - AbstarctItemBase fields → read-only
    - Calculated fields (total_gross_weight, total_net_weight, total_price) → read-only
    - purchase_qty, unit_price → editable
    """

    pass


class PurchaseItemSerializerForSales(PurchaseItemSerializer):
    """Sales: full access to purchase fields"""

    pass


class PurchaseItemSerializerForProduction(PurchaseItemSerializer):
    """
    Production: read-only access, no financial fields.
    Financial fields (unit_price, total_price) are excluded.
    """

    class Meta(PurchaseItemSerializer.Meta):
        fields = [
            "id",
            # AbstarctItemBase fields
            "product_name",
            "specification",
            "outter_packaging",
            "inner_packaging",
            "size",
            "unit",
            "glazing",
            "gross_weight",
            "net_weight",
            # PurchaseItem quantity/weight fields (no financial)
            "purchase_qty",
            "total_gross_weight",
            "total_net_weight",
            # BaseModel fields
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PurchaseItemSerializerForWarehouse(PurchaseItemSerializer):
    """
    Warehouse: read-only access, no financial fields.
    Financial fields (unit_price, total_price) are excluded.
    """

    class Meta(PurchaseItemSerializer.Meta):
        fields = [
            "id",
            # AbstarctItemBase fields
            "product_name",
            "specification",
            "outter_packaging",
            "inner_packaging",
            "size",
            "unit",
            "glazing",
            "gross_weight",
            "net_weight",
            # PurchaseItem quantity/weight fields (no financial)
            "purchase_qty",
            "total_gross_weight",
            "total_net_weight",
            # BaseModel fields
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
