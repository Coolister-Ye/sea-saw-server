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

    def validate_status(self, value):
        """
        验证 Order 状态变更。

        Order.status 由 Pipeline 驱动，用户只能在无 Pipeline 时将 draft → cancelled。
        - 无 Pipeline：仅允许 draft → cancelled
        - 有 Pipeline：拒绝直接修改（通过 Pipeline 操作触发）
        """
        if not self.instance or value == self.instance.status:
            return value

        pipeline = getattr(self.instance, 'pipeline', None)
        if pipeline:
            raise serializers.ValidationError(
                _(
                    "订单状态由 Pipeline 管理，"
                    "请通过 Pipeline 操作确认或取消订单。"
                )
            )

        current = self.instance.status
        if current == "draft" and value == "cancelled":
            return value

        raise serializers.ValidationError(
            _("无效的状态变更：%(current)s → %(value)s")
            % {"current": current, "value": value}
        )

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

        Status changes are validated by validate_status() and saved directly.
        Pipeline state machine is NOT triggered by Order status changes.
        """
        new_status = validated_data.get('status')
        old_status = instance.status
        status_changed = new_status and new_status != old_status

        # Pop status so super().update() handles non-status fields first
        if status_changed:
            validated_data.pop('status')

        # Note: 'pipeline' is popped because it's a reverse OneToOne relation
        # and cannot be set directly on Order update
        validated_data.pop("pipeline", None)

        # Attachments are handled by ReusableAttachmentWriteMixin
        instance = super().update(instance, validated_data)

        # Sync order fields to pipeline if it exists (from PipelineSyncMixin)
        self.sync_to_pipeline(instance)

        # Save status change directly (validate_status already enforced the rules)
        if status_changed:
            instance.status = new_status
            instance.save(update_fields=['status', 'updated_at'])

        return instance
