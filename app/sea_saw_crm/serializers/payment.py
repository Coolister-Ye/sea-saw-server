from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from ..models.payment import PaymentRecord
from .base import BaseSerializer


class PaymentRecordSerializer(BaseSerializer):
    class Meta:
        model = PaymentRecord
        fields = [
            "id",
            "payment_code",
            "order",
            "payment_date",
            "amount",
            "currency",
            "payment_method",
            "bank_reference",
            "attachment",
            "remark",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["payment_code"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than 0"))
        return value

    def validate(self, attrs):
        request = self.context.get("request")

        # update 时禁止改 order
        if self.instance and "order" in attrs:
            raise serializers.ValidationError(
                {"order": _("Order cannot be modified once payment is created")}
            )

        return attrs
