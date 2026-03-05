"""
Outbound Order Serializers - Standalone version for direct OutboundOrder access

用于 OutboundOrderViewSet，提供独立的 OutboundOrder 访问
显示关联的 Pipeline (Order) 信息
"""

from decimal import Decimal
from rest_framework import serializers
from sea_saw_base.serializers import BaseSerializer
from sea_saw_attachment.serializers import AttachmentSerializer
from .outbound_item import OutboundItemSerializer
from sea_saw_warehouse.models import OutboundOrder
from sea_saw_sales.models import Order

from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin


class PipelineNestedSerializer(BaseSerializer):
    """
    Simplified Pipeline (Order) serializer for nested display in OutboundOrder.
    """

    class Meta(BaseSerializer.Meta):
        model = Order
        fields = ["id", "order_code", "order_date", "status", "etd"]


class OutboundOrderSerializerForOutboundView(UniqueFieldsMixin, BaseSerializer):
    """
    Outbound Order serializer for OutboundOrderViewSet (standalone access).
    Used by all roles for direct OutboundOrder access.
    - Displays related_pipeline as nested object
    - Includes full outbound items and attachments
    """

    outbound_items = OutboundItemSerializer(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )

    attachments = AttachmentSerializer(
        many=True, required=False, allow_null=True, label=_("Attachments")
    )

    related_pipeline = PipelineNestedSerializer(
        source='pipeline',  # Map to the actual ForeignKey field
        required=False,
        allow_null=True,
        read_only=True,
        label=_("Related Pipeline (Order)"),
    )

    order_outbound_amount = serializers.SerializerMethodField(
        label=_("Order Outbound Amount"),
    )
    purchase_outbound_amount = serializers.SerializerMethodField(
        label=_("Purchase Outbound Amount"),
    )

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

    class Meta(BaseSerializer.Meta):
        model = OutboundOrder
        fields = [
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
            "order_outbound_amount",
            "purchase_outbound_amount",
            "outbound_items",
            "attachments",
            "related_pipeline",
            "owner",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """Handle related_pipeline assignment."""
        # Pipeline is a direct ForeignKey, so it should be handled normally
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        """Handle related_pipeline assignment."""
        # Pipeline is a direct ForeignKey, so it should be handled normally
        instance = super().update(instance, validated_data)
        return instance
