from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin

from sea_saw_base.serializers import BaseSerializer
from sea_saw_crm.serializers import (
    AccountMinimalSerializer,
    ContactMinimalSerializer,
    BankAccountMinimalSerializer,
)
from sea_saw_attachment.serializers import AttachmentSerializer
from sea_saw_attachment.mixins import ReusableAttachmentWriteMixin
from sea_saw_crm.models import Account, Contact, BankAccount
from sea_saw_attachment.models import Attachment

from .mixins import PipelineSyncMixin
from .order_item import OrderItemSerializerForAdmin
from .pipeline_minimal import PipelineMinimalSerializer
from ..models import Order


class OrderSerializerForOrderView(
    PipelineSyncMixin, ReusableAttachmentWriteMixin, UniqueFieldsMixin, BaseSerializer
):
    """
    Order serializer for OrderViewSet (standalone access).
    Used by all roles for direct Order access.
    - Displays related_pipeline as nested object
    - Includes full order items and attachments
    """

    buyer = AccountMinimalSerializer(read_only=True, label=_("Buyer"))
    buyer_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        source="buyer",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Buyer ID"),
    )

    seller = AccountMinimalSerializer(read_only=True, label=_("Seller"))
    seller_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        source="seller",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Seller ID"),
    )

    shipper = AccountMinimalSerializer(read_only=True, label=_("Shipper"))
    shipper_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        source="shipper",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Shipper ID"),
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

    bank_account = BankAccountMinimalSerializer(read_only=True, label=_("Bank Account"))
    bank_account_id = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all(),
        source="bank_account",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Bank Account ID"),
    )

    order_items = OrderItemSerializerForAdmin(
        many=True, required=False, allow_null=True, label=_("Order Items")
    )

    attachments = AttachmentSerializer(
        many=True, required=False, allow_null=True, label=_("Attachments")
    )

    related_pipeline = PipelineMinimalSerializer(
        source="pipeline",
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
            "buyer",
            "buyer_id",
            "seller",
            "seller_id",
            "shipper",
            "shipper_id",
            "contact",
            "contact_id",
            "bank_account",
            "bank_account_id",
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
            "payment_terms",
            "additional_info",
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
