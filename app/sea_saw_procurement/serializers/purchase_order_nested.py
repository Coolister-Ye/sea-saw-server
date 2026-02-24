from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin
from sea_saw_attachment.mixins import ReusableAttachmentWriteMixin

from sea_saw_base.serializers import BaseSerializer
from sea_saw_attachment.serializers import AttachmentSerializer
from sea_saw_crm.serializers import AccountMinimalSerializer, ContactMinimalSerializer
from sea_saw_crm.models import Account, Contact
from .purchase_item import (
    PurchaseItemSerializer,
    PurchaseItemSerializerForAdmin,
    PurchaseItemSerializerForSales,
    PurchaseItemSerializerForProduction,
    PurchaseItemSerializerForWarehouse,
)

from ..models import PurchaseOrder
from sea_saw_attachment.models import Attachment

BASE_FIELDS = [
    "id",
    "purchase_code",
    "purchase_date",
    "supplier",
    "supplier_id",
    "contact",
    "contact_id",
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
    "comment",
    "owner",
    "created_at",
    "updated_at",
]


class PurchaseOrderSerializer(
    ReusableAttachmentWriteMixin, UniqueFieldsMixin, BaseSerializer
):
    """
    Purchase Order serializer with nested items and attachments.
    """

    supplier = AccountMinimalSerializer(read_only=True, label=_("Supplier"))
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        source="supplier",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Supplier ID"),
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

    purchase_items = PurchaseItemSerializer(
        many=True, required=False, allow_null=True, label=_("Purchase Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    attachment_model = Attachment

    class Meta(BaseSerializer.Meta):
        model = PurchaseOrder
        fields = BASE_FIELDS + [
            "purchase_items",
            "attachments",
        ]
        read_only_fields = ["total_amount"]


NON_FINANCIAL_FIELDS = [
    "id",
    "purchase_code",
    "purchase_date",
    "supplier",
    "supplier_id",
    "contact",
    "contact_id",
    "status",
    "etd",
    "loading_port",
    "destination_port",
    "shipment_term",
    "inco_terms",
    "comment",
    "purchase_items",
    "attachments",
    "owner",
    "created_at",
    "updated_at",
]


class PurchaseOrderSerializerForAdmin(PurchaseOrderSerializer):
    """
    Purchase Order serializer for admin users.
    """

    purchase_items = PurchaseItemSerializerForAdmin(
        many=True, required=False, allow_null=True, label=_("Purchase Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    class Meta(PurchaseOrderSerializer.Meta):
        fields = BASE_FIELDS + ["purchase_items", "attachments"]


class PurchaseOrderSerializerForSales(PurchaseOrderSerializer):
    """
    Purchase Order serializer for sales users.
    """

    purchase_items = PurchaseItemSerializerForSales(
        many=True, required=False, allow_null=True, label=_("Purchase Items")
    )

    class Meta(PurchaseOrderSerializer.Meta):
        fields = BASE_FIELDS + ["purchase_items", "attachments"]
        read_only_fields = fields


class PurchaseOrderSerializerForProduction(PurchaseOrderSerializer):
    """
    Purchase Order serializer for production users.
    Excludes financial fields (currency, deposit, balance, total_amount).
    """

    purchase_items = PurchaseItemSerializerForProduction(
        many=True, required=False, allow_null=True, label=_("Purchase Items")
    )

    class Meta(PurchaseOrderSerializer.Meta):
        fields = NON_FINANCIAL_FIELDS
        read_only_fields = fields


class PurchaseOrderSerializerForWarehouse(PurchaseOrderSerializer):
    """
    Purchase Order serializer for warehouse users.
    Excludes financial fields (currency, deposit, balance, total_amount).
    """

    purchase_items = PurchaseItemSerializerForWarehouse(
        many=True, required=False, allow_null=True, label=_("Purchase Items")
    )

    class Meta(PurchaseOrderSerializer.Meta):
        fields = NON_FINANCIAL_FIELDS
        read_only_fields = fields
