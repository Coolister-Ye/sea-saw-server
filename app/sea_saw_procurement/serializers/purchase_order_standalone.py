from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin

from sea_saw_base.serializers import BaseSerializer
from sea_saw_attachment.serializers import AttachmentSerializer
from sea_saw_attachment.mixins import ReusableAttachmentWriteMixin
from sea_saw_crm.serializers import (
    AccountMinimalSerializer,
    ContactMinimalSerializer,
    BankAccountMinimalSerializer,
)
from sea_saw_crm.models import Account, Contact, BankAccount
from sea_saw_attachment.models import Attachment
from sea_saw_sales.serializers.pipeline_minimal import PipelineMinimalSerializer
from sea_saw_sales.models import Order

from .purchase_item import PurchaseItemSerializerForAdmin
from ..models import PurchaseOrder


class RelatedOrderMinimalSerializer(BaseSerializer):
    """Minimal Order serializer for display on Purchase Order."""

    class Meta(BaseSerializer.Meta):
        model = Order
        fields = ["id", "order_code", "status"]
        read_only_fields = fields


class PurchaseOrderSerializerForStandalone(
    ReusableAttachmentWriteMixin, UniqueFieldsMixin, BaseSerializer
):
    """
    Purchase Order serializer for standalone (direct) access.

    Exposes:
    - supplier/contact/bank_account as nested objects (read) + _id fields (write)
    - related_pipeline as minimal pipeline info (read-only, mapped from 'pipeline' FK)
    - related_order as minimal order info (read-only)
    - Full purchase_items and attachments
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

    supplier = AccountMinimalSerializer(read_only=True, label=_("Supplier"))
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        source="supplier",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Supplier ID"),
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

    # Expose the 'pipeline' FK as 'related_pipeline' to match frontend expectations
    related_pipeline = PipelineMinimalSerializer(
        source="pipeline",
        required=False,
        allow_null=True,
        read_only=True,
        label=_("Related Pipeline"),
    )

    related_order = RelatedOrderMinimalSerializer(
        read_only=True,
        allow_null=True,
        label=_("Related Order"),
    )
    related_order_id = serializers.PrimaryKeyRelatedField(
        source="related_order",
        queryset=Order.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Related Order ID"),
    )

    purchase_items = PurchaseItemSerializerForAdmin(
        many=True, required=False, allow_null=True, label=_("Purchase Items")
    )

    attachments = AttachmentSerializer(
        many=True, required=False, allow_null=True, label=_("Attachments")
    )

    attachment_model = Attachment

    class Meta(BaseSerializer.Meta):
        model = PurchaseOrder
        fields = [
            "id",
            "purchase_code",
            "purchase_date",
            "buyer",
            "buyer_id",
            "supplier",
            "supplier_id",
            "shipper",
            "shipper_id",
            "contact",
            "contact_id",
            "bank_account",
            "bank_account_id",
            "status",
            "etd",
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
            "related_order",
            "related_order_id",
            "related_pipeline",
            "purchase_items",
            "attachments",
            "owner",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["total_amount", "purchase_code"]
