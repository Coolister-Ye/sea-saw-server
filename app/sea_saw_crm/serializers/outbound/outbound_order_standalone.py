"""
Outbound Order Serializers - Standalone version for direct OutboundOrder access

用于 OutboundOrderViewSet，提供独立的 OutboundOrder 访问
显示关联的 Pipeline (Order) 信息
"""

from ..base import BaseSerializer
from ..shared import AttachmentSerializer
from .outbound_item import OutboundItemSerializer
from ...models.outbound import OutboundOrder
from ...models.order import Order

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
