from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from ..models.payment import OrderPayment, OrderPaymentAttachment, PaymentRecord, PaymentAttachment
from .base import BaseSerializer
from .shared import BaseAttachmentSerializer


class PaymentAttachmentSerializer(BaseAttachmentSerializer):
    """
    Serializer for Payment Record Attachments (Legacy - will be replaced)
    """

    class Meta(BaseSerializer.Meta):
        model = OrderPaymentAttachment
        fields = [
            "id",
            "order_payment",
            "file",
            "file_url",
            "file_name",
            "file_size",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "order_payment",
            "file_name",
            "file_size",
            "created_at",
            "updated_at",
        ]


class PaymentRecordSerializer(BaseSerializer):
    attachments = PaymentAttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    class Meta:
        model = OrderPayment
        fields = [
            "id",
            "payment_code",
            "order",
            "payment_date",
            "amount",
            "currency",
            "payment_method",
            "bank_reference",
            "remark",
            "attachments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["payment_code"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than 0"))
        return value

    def validate(self, attrs):
        # update 时禁止改 order
        if self.instance and "order" in attrs:
            # 只有当 order 真的变了才报错
            if attrs["order"] != self.instance.order:
                raise serializers.ValidationError(
                    {"order": _("Order cannot be modified once payment is created")}
                )

        return attrs
