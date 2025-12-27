from ..base import BaseSerializer
from .production_item import (
    ProductionItemSerializer,
    ProductionItemSerializerForAdmin,
    ProductionItemSerializerForSales,
    ProductionItemSerializerForProduction,
    ProductionItemSerializerForWarehouse,
)

from ...models.production import ProductionOrder

from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin


class ProductionOrderSerializer(UniqueFieldsMixin, BaseSerializer):
    """Order serializer."""

    production_items = ProductionItemSerializer(
        many=True, required=False, allow_null=True, label=_("Production Items")
    )

    class Meta(BaseSerializer.Meta):
        model = ProductionOrder
        fields = [
            "id",
            "production_code",
            "planned_date",
            "start_date",
            "end_date",
            "status",
            "remark",
            "production_files",
            "production_items",
        ]


class ProductionOrderSerializerForAdmin(ProductionOrderSerializer):
    """
    Order serializer for admin users.
    """

    production_items = ProductionItemSerializerForAdmin(
        many=True, required=False, allow_null=True, label=_("Production Items")
    )

    class Meta(ProductionOrderSerializer.Meta):
        fields = ProductionOrderSerializer.Meta.fields


class ProductionOrderSerializerForSales(ProductionOrderSerializer):
    """
    Order serializer for sales users.
    """

    production_items = ProductionItemSerializerForSales(
        many=True, required=False, allow_null=True, label=_("Production Items")
    )

    class Meta(ProductionOrderSerializer.Meta):
        """设置全部字段为read-only"""

        fields = ProductionOrderSerializer.Meta.fields
        read_only_fields = ProductionOrderSerializer.Meta.fields


class ProductionOrderSerializerForProduction(ProductionOrderSerializer):
    """
    Order serializer for production users.
    """

    production_items = ProductionItemSerializerForProduction(
        many=True, required=False, allow_null=True, label=_("Production Items")
    )

    class Meta(ProductionOrderSerializer.Meta):
        fields = ProductionOrderSerializer.Meta.fields


class ProductionOrderSerializerForWarehouse(ProductionOrderSerializer):
    """
    Order serializer for warehouse users.
    """

    production_items = ProductionItemSerializerForWarehouse(
        many=True, required=False, allow_null=True, label=_("Production Items")
    )

    class Meta(ProductionOrderSerializer.Meta):
        """设置全部字段为read-only"""

        fields = ProductionOrderSerializer.Meta.fields
        read_only_fields = ProductionOrderSerializer.Meta.fields
