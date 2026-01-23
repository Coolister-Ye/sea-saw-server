"""
Outbound Order Serializers - Nested version for operations under Pipeline

用于 NestedOutboundOrderViewSet，处理嵌套在 Pipeline 下的 OutboundOrder 操作
Nested serializers exclude the pipeline field since it's managed by the parent
"""

from ..base import BaseSerializer
from ..shared import AttachmentSerializer
from .outbound_item import (
    OutboundItemSerializer,
    OutboundItemSerializerForAdmin,
    OutboundItemSerializerForSales,
    OutboundItemSerializerForProduction,
    OutboundItemSerializerForWarehouse,
)

from ...models.outbound import OutboundOrder
from ...models import Attachment
from ...mixins import ReusableAttachmentWriteMixin

from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin


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
            "owner",
            "created_at",
            "updated_at",
        ]


class OutboundOrderSerializerForAdmin(OutboundOrderSerializer):
    """
    Outbound Order serializer for Admin role
    Full access to all fields
    """

    outbound_items = OutboundItemSerializerForAdmin(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    class Meta(OutboundOrderSerializer.Meta):
        fields = OutboundOrderSerializer.Meta.fields


class OutboundOrderSerializerForSales(OutboundOrderSerializer):
    """
    Outbound Order serializer for Sales role
    Read-only access
    """

    outbound_items = OutboundItemSerializerForSales(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )

    class Meta(OutboundOrderSerializer.Meta):
        fields = OutboundOrderSerializer.Meta.fields
        read_only_fields = OutboundOrderSerializer.Meta.fields


class OutboundOrderSerializerForProduction(OutboundOrderSerializer):
    """
    Outbound Order serializer for Production role
    Read-only access
    """

    outbound_items = OutboundItemSerializerForProduction(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )

    class Meta(OutboundOrderSerializer.Meta):
        fields = OutboundOrderSerializer.Meta.fields
        read_only_fields = OutboundOrderSerializer.Meta.fields


class OutboundOrderSerializerForWarehouse(OutboundOrderSerializer):
    """
    Outbound Order serializer for Warehouse role
    Full write access for warehouse operations
    """

    outbound_items = OutboundItemSerializerForWarehouse(
        many=True, required=False, allow_null=True, label=_("Outbound Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    class Meta(OutboundOrderSerializer.Meta):
        fields = OutboundOrderSerializer.Meta.fields
