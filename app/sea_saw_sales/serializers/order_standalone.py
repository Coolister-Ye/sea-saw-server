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
from sea_saw_pipeline.models.pipeline import ActiveEntityType
from sea_saw_pipeline.constants import (
    ORDER_TO_PIPELINE_STATUS,
    PIPELINE_STATE_MACHINE_BY_TYPE,
)
from sea_saw_pipeline.services.pipeline_state_service import PipelineStateService
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

    def validate_status(self, value):
        """
        验证 Order 状态变更是否被 Pipeline 状态机允许。
        - 无 Pipeline：允许任意变更
        - 有 Pipeline 且 active_entity ∉ {ORDER, NONE}：拒绝变更
        - 有 Pipeline 且有映射：检查 Pipeline 状态机是否允许对应转换
        """
        if not self.instance or value == self.instance.status:
            return value

        pipeline = getattr(self.instance, 'pipeline', None)
        if not pipeline:
            return value

        # active_entity 守卫
        if pipeline.active_entity not in (ActiveEntityType.ORDER, ActiveEntityType.NONE):
            raise serializers.ValidationError(
                _(
                    "Pipeline 已进入 %(entity)s 阶段，"
                    "无法直接修改订单状态。请先在 Pipeline 中回退状态。"
                )
                % {"entity": pipeline.get_active_entity_display()}
            )

        # 检查 Pipeline 状态机是否允许对应转换
        target = ORDER_TO_PIPELINE_STATUS.get(value)
        if target and target != pipeline.status:
            state_machine = PIPELINE_STATE_MACHINE_BY_TYPE.get(pipeline.pipeline_type, {})
            allowed = state_machine.get(pipeline.status, set())
            if target not in allowed:
                raise serializers.ValidationError(
                    _(
                        "Pipeline 当前状态 [%(current)s] "
                        "不允许转换到 [%(target)s]。"
                    )
                    % {
                        "current": pipeline.get_status_display(),
                        "target": target,
                    }
                )

        return value

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

        Status changes are routed through Pipeline state machine when a Pipeline exists,
        ensuring bidirectional sync consistency.
        """
        new_status = validated_data.get('status')
        old_status = instance.status
        status_changed = new_status and new_status != old_status

        # Pop status so super().update() only handles non-status fields
        if status_changed:
            validated_data.pop('status')

        # Note: 'pipeline' is popped because it's a reverse OneToOne relation
        # and cannot be set directly on Order update
        validated_data.pop("pipeline", None)

        # Attachments are handled by ReusableAttachmentWriteMixin
        instance = super().update(instance, validated_data)

        # Sync to pipeline if it exists (from PipelineSyncMixin)
        self.sync_to_pipeline(instance)

        # Handle status change
        if status_changed:
            pipeline = getattr(instance, 'pipeline', None)
            target = ORDER_TO_PIPELINE_STATUS.get(new_status) if pipeline else None

            if pipeline and target and target != pipeline.status:
                # Route through Pipeline state machine (which will set Order status via forward sync)
                PipelineStateService.transition(
                    pipeline=pipeline,
                    target_status=target,
                    user=self.context['request'].user,
                )
                instance.refresh_from_db()
            else:
                # No Pipeline / no mapping (completed) / Pipeline already at target status
                instance.status = new_status
                instance.save(update_fields=['status', 'updated_at'])

        return instance
