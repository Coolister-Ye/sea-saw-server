from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from drf_writable_nested.mixins import UniqueFieldsMixin

from ..base import BaseSerializer
from ..shared import AttachmentSerializer
from ...models.payment import Payment
from sea_saw_attachment.models import Attachment
from ...mixins import ReusableAttachmentWriteMixin


# =====================================================
# Base Standalone Serializer
# =====================================================


class PaymentStandaloneSerializer(
    ReusableAttachmentWriteMixin, UniqueFieldsMixin, BaseSerializer
):
    """
    Payment standalone serializer with attachment handling.
    Used for direct CRUD operations on payments (not within Order/PurchaseOrder context).
    """

    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    # Write-only fields for creating/updating
    content_type = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all(),
        write_only=True,
        label=_("Content Type"),
    )
    object_id = serializers.IntegerField(
        write_only=True,
        label=_("Object ID"),
    )

    # Read-only display fields
    payment_type = serializers.ReadOnlyField(label=_("Payment Type"))

    attachment_model = Attachment

    class Meta(BaseSerializer.Meta):
        model = Payment
        fields = [
            "id",
            "payment_code",
            "content_type",
            "object_id",
            "payment_type",
            "payment_date",
            "amount",
            "currency",
            "payment_method",
            "bank_reference",
            "remark",
            "attachments",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["payment_code", "payment_type"]

    def validate_amount(self, value):
        """Validate that amount is greater than 0"""
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than 0"))
        return value

    def validate(self, attrs):
        """Validate content_type and object_id consistency"""
        # Prevent changing related object on update
        if self.instance:
            if "content_type" in attrs and attrs["content_type"] != self.instance.content_type:
                raise serializers.ValidationError(
                    {
                        "content_type": _(
                            "Related object type cannot be modified once payment is created"
                        )
                    }
                )
            if "object_id" in attrs and attrs["object_id"] != self.instance.object_id:
                raise serializers.ValidationError(
                    {
                        "object_id": _(
                            "Related object cannot be modified once payment is created"
                        )
                    }
                )

        # Ensure content_type and object_id are provided together for creation
        if not self.instance:
            if "content_type" in attrs and "object_id" not in attrs:
                raise serializers.ValidationError(
                    {"object_id": _("object_id is required when content_type is provided")}
                )
            if "object_id" in attrs and "content_type" not in attrs:
                raise serializers.ValidationError(
                    {"content_type": _("content_type is required when object_id is provided")}
                )

        return attrs


# =====================================================
# Role-based Standalone Serializers
# =====================================================


class PaymentStandaloneSerializerForAdmin(PaymentStandaloneSerializer):
    """
    Admin: full access to payment fields.
    """

    pass


class PaymentStandaloneSerializerForSales(PaymentStandaloneSerializer):
    """
    Sales: full access to own orders' payments.
    """

    pass


class PaymentStandaloneSerializerForProduction(PaymentStandaloneSerializer):
    """
    Production: read-only access, no financial details.
    """

    class Meta(PaymentStandaloneSerializer.Meta):
        fields = [
            "id",
            "payment_code",
            "content_type",
            "object_id",
            "related_order_id",
            "payment_type",
            "payment_date",
            "currency",
            "payment_method",
            "bank_reference",
            "remark",
            "attachments",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PaymentStandaloneSerializerForWarehouse(PaymentStandaloneSerializer):
    """
    Warehouse: read-only access, no financial details.
    """

    class Meta(PaymentStandaloneSerializer.Meta):
        fields = [
            "id",
            "payment_code",
            "content_type",
            "object_id",
            "related_order_id",
            "payment_type",
            "payment_date",
            "currency",
            "payment_method",
            "bank_reference",
            "remark",
            "attachments",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
