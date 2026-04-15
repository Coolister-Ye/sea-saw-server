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
from sea_saw_pipeline.models.pipeline import Pipeline

from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin


class PipelineNestedSerializer(BaseSerializer):
    """
    Simplified Pipeline serializer for nested display in OutboundOrder.
    """

    class Meta(BaseSerializer.Meta):
        model = Pipeline
        fields = [
            "id",
            "pipeline_code",
            "pipeline_type",
            "status",
            "active_entity",
            "confirmed_at",
            "in_purchase_at",
            "purchase_completed_at",
            "in_production_at",
            "production_completed_at",
            "in_purchase_and_production_at",
            "purchase_and_production_completed_at",
            "in_outbound_at",
            "outbound_completed_at",
            "completed_at",
            "cancelled_at",
        ]


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
        source="pipeline",  # Map to the actual ForeignKey field
        required=False,
        allow_null=True,
        read_only=True,
        label=_("Related Pipeline (Order)"),
    )
    related_pipeline_id = serializers.PrimaryKeyRelatedField(
        source="pipeline",
        queryset=Pipeline.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Related Pipeline ID"),
    )

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
            "outbound_items",
            "attachments",
            "related_pipeline",
            "related_pipeline_id",
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
