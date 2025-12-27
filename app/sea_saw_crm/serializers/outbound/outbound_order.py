from ..base import BaseSerializer
from .outbound_item import (
    OutboundItemSerializer,
    OutboundItemSerializerForAdmin,
    OutboundItemSerializerForSales,
    OutboundItemSerializerForProduction,
    OutboundItemSerializerForWarehouse,
)

from ...models.outbound import OutboundOrder
from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin


class OutboundOrderSerializer(UniqueFieldsMixin, BaseSerializer):
    """Outbound Order serializer (default: admin view)."""

    outbound_items = OutboundItemSerializer(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )

    class Meta(BaseSerializer.Meta):
        model = OutboundOrder
        fields = [
            "id",
            "outbound_code",
            "outbound_date",
            "status",
            "container_no",
            "seal_no",
            "destination_port",
            "logistics_provider",
            "loader",
            "remark",
            "outbound_items",
        ]


class OutboundOrderSerializerForAdmin(OutboundOrderSerializer):
    """Admin can edit all outbound items."""

    outbound_items = OutboundItemSerializerForAdmin(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )

    class Meta(OutboundOrderSerializer.Meta):
        fields = OutboundOrderSerializer.Meta.fields


class OutboundOrderSerializerForSales(OutboundOrderSerializer):
    """Sales read-only."""

    outbound_items = OutboundItemSerializerForSales(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )

    class Meta(OutboundOrderSerializer.Meta):
        fields = OutboundOrderSerializer.Meta.fields
        read_only_fields = OutboundOrderSerializer.Meta.fields


class OutboundOrderSerializerForProduction(OutboundOrderSerializer):
    """Production read-only."""

    outbound_items = OutboundItemSerializerForProduction(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )

    class Meta(OutboundOrderSerializer.Meta):
        fields = OutboundOrderSerializer.Meta.fields
        read_only_fields = OutboundOrderSerializer.Meta.fields


class OutboundOrderSerializerForWarehouse(OutboundOrderSerializer):
    """Warehouse limited write."""

    outbound_items = OutboundItemSerializerForWarehouse(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )

    class Meta(OutboundOrderSerializer.Meta):
        fields = OutboundOrderSerializer.Meta.fields
