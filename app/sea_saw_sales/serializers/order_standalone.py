"""
Order Serializers - Standalone version for direct Order access

用于 OrderViewSet，提供独立的 Order 访问：
- 列表页：显示 Order 基本信息 + Pipeline 状态概览
- 详情页：提供 Order CRUD + 生成 Pipeline 功能
- 完整流程管理请使用 Pipeline API
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin

from sea_saw_base.serializers import BaseSerializer
from sea_saw_crm.serializers import AccountMinimalSerializer, ContactMinimalSerializer
from sea_saw_attachment.serializers import AttachmentSerializer
from sea_saw_attachment.mixins import ReusableAttachmentWriteMixin
from .mixins import PipelineSyncMixin
from sea_saw_pipeline.models import Pipeline
from sea_saw_crm.models import Account, Contact
from sea_saw_attachment.models import Attachment
from .order_item import OrderItemSerializerForAdmin
from ..models import Order


class PipelineMinimalSerializer(BaseSerializer):
    """
    Minimal Pipeline serializer for Order list/overview display.
    Only shows essential pipeline status info - for full pipeline data, use Pipeline API.
    """

    class Meta(BaseSerializer.Meta):
        model = Pipeline
        fields = [
            "id",
            "pipeline_code",
            "status",
            "active_entity",
            "pipeline_type",
        ]
        read_only_fields = fields


class OrderSerializerForOrderView(
    PipelineSyncMixin, ReusableAttachmentWriteMixin, UniqueFieldsMixin, BaseSerializer
):
    """
    Order serializer for OrderViewSet (standalone access).
    Used by all roles for direct Order access.
    - Displays related_pipeline as nested object
    - Includes full order items and attachments
    """

    account = AccountMinimalSerializer(read_only=True, label=_("Company"))
    account_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        source="account",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Company ID"),
    )

    contact = ContactMinimalSerializer(read_only=True, label=_("Contact"))
    contact_id = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        source="contact",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Contact ID"),
    )

    order_items = OrderItemSerializerForAdmin(
        many=True, required=False, allow_null=True, label=_("Order Items")
    )

    attachments = AttachmentSerializer(
        many=True, required=False, allow_null=True, label=_("Attachments")
    )

    related_pipeline = PipelineMinimalSerializer(
        source="pipeline",  # Map to the actual OneToOne reverse relation field
        required=False,
        allow_null=True,
        read_only=True,
        label=_("Related Pipeline"),
    )

    attachment_model = Attachment

    class Meta(BaseSerializer.Meta):
        model = Order
        fields = [
            "id",
            "order_code",
            "order_date",
            "account",
            "account_id",
            "contact",
            "contact_id",
            "etd",
            "status",
            "loading_port",
            "destination_port",
            "shipment_term",
            "inco_terms",
            "currency",
            "deposit",
            "balance",
            "total_amount",
            "comment",
            "order_items",
            "attachments",
            "related_pipeline",
            "owner",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """Handle related_pipeline assignment."""
        # Note: 'pipeline' is popped because it's a reverse OneToOne relation
        # and cannot be set directly on Order creation
        validated_data.pop("pipeline", None)

        # Attachments are handled by ReusableAttachmentWriteMixin
        instance = super().create(validated_data)
        # Pipeline should be created/assigned from Pipeline side, not Order side
        return instance

    def update(self, instance, validated_data):
        """
        Handle Order update with automatic Pipeline synchronization.

        When order fields are updated, related pipeline fields are automatically synced:
        - contact → pipeline.contact
        - order_date → pipeline.order_date
        """
        # Note: 'pipeline' is popped because it's a reverse OneToOne relation
        # and cannot be set directly on Order update
        validated_data.pop("pipeline", None)

        # Attachments are handled by ReusableAttachmentWriteMixin
        instance = super().update(instance, validated_data)

        # Sync to pipeline if it exists (from PipelineSyncMixin)
        self.sync_to_pipeline(instance)

        return instance
