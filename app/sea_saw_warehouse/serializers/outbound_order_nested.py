"""
Outbound Order Serializers - Nested version for operations under Pipeline

用于 NestedOutboundOrderViewSet，处理嵌套在 Pipeline 下的 OutboundOrder 操作
Nested serializers exclude the pipeline field since it's managed by the parent
"""

from decimal import Decimal
from rest_framework import serializers
from sea_saw_base.serializers import BaseSerializer
from sea_saw_attachment.serializers import AttachmentSerializer
from .outbound_item import (
    OutboundItemSerializer,
    OutboundItemSerializerForAdmin,
    OutboundItemSerializerForSales,
    OutboundItemSerializerForProduction,
    OutboundItemSerializerForWarehouse,
)

from sea_saw_warehouse.models import OutboundOrder
from sea_saw_attachment.models import Attachment
from sea_saw_attachment.mixins import ReusableAttachmentWriteMixin

from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin


class _OutboundAmountMixin:
    """
    Provides getter methods for order/purchase outbound amount fields.
    Field declarations must be added on each concrete serializer class
    so DRF's metaclass can register them properly.
    """

    def get_order_outbound_amount(self, obj):
        """订单出库金额：order_item.unit_price × outbound_gross_weight 的合计"""
        total = Decimal("0")
        for item in obj.outbound_items.all():
            if item.outbound_gross_weight is None:
                continue
            order_item = item.order_item
            if order_item is None or order_item.unit_price is None:
                continue
            total += order_item.unit_price * item.outbound_gross_weight
        return total

    def get_purchase_outbound_amount(self, obj):
        """采购出库金额：purchase_item.unit_price × outbound_gross_weight 的合计"""
        total = Decimal("0")
        for item in obj.outbound_items.all():
            if item.outbound_gross_weight is None:
                continue
            order_item = item.order_item
            if order_item is None:
                continue
            purchase_item = order_item.purchase_items.first()
            if purchase_item is None or purchase_item.unit_price is None:
                continue
            total += purchase_item.unit_price * item.outbound_gross_weight
        return total


_BASE_FIELDS = [
    "id",
    "outbound_code",
    "outbound_date",
    "eta",
    "status",
    "container_no",
    "seal_no",
    "destination_port",
    "logistics_provider",
    "loader",
    "remark",
    "outbound_items",
    "attachments",
    "owner",
    "created_at",
    "updated_at",
]

_AMOUNT_FIELDS = ["order_outbound_amount", "purchase_outbound_amount"]


class OutboundOrderSerializer(
    ReusableAttachmentWriteMixin, UniqueFieldsMixin, BaseSerializer
):
    """
    Base Outbound Order serializer for nested operations.
    Excludes pipeline field as it's managed by the parent Pipeline.
    """

    outbound_items = OutboundItemSerializer(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    attachment_model = Attachment

    class Meta(BaseSerializer.Meta):
        model = OutboundOrder
        fields = _BASE_FIELDS


class OutboundOrderSerializerForAdmin(_OutboundAmountMixin, OutboundOrderSerializer):
    """
    Outbound Order serializer for Admin role
    Full access to all fields including amount fields.
    """

    outbound_items = OutboundItemSerializerForAdmin(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )
    order_outbound_amount = serializers.SerializerMethodField(
        label=_("Order Outbound Amount"),
    )
    purchase_outbound_amount = serializers.SerializerMethodField(
        label=_("Purchase Outbound Amount"),
    )

    class Meta(OutboundOrderSerializer.Meta):
        fields = _BASE_FIELDS + _AMOUNT_FIELDS


class OutboundOrderSerializerForSales(_OutboundAmountMixin, OutboundOrderSerializer):
    """
    Outbound Order serializer for Sales role
    Read-only access, includes amount fields.
    """

    outbound_items = OutboundItemSerializerForSales(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )
    order_outbound_amount = serializers.SerializerMethodField(
        label=_("Order Outbound Amount"),
    )
    purchase_outbound_amount = serializers.SerializerMethodField(
        label=_("Purchase Outbound Amount"),
    )

    class Meta(OutboundOrderSerializer.Meta):
        fields = _BASE_FIELDS + _AMOUNT_FIELDS
        read_only_fields = _BASE_FIELDS + _AMOUNT_FIELDS


class OutboundOrderSerializerForProduction(OutboundOrderSerializer):
    """
    Outbound Order serializer for Production role
    Read-only access, no amount fields.
    """

    outbound_items = OutboundItemSerializerForProduction(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )

    class Meta(OutboundOrderSerializer.Meta):
        fields = _BASE_FIELDS
        read_only_fields = _BASE_FIELDS


class OutboundOrderSerializerForWarehouse(OutboundOrderSerializer):
    """
    Outbound Order serializer for Warehouse role
    Full write access, no amount fields.
    """

    outbound_items = OutboundItemSerializerForWarehouse(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    class Meta(OutboundOrderSerializer.Meta):
        fields = _BASE_FIELDS
