from sea_saw_base.serializers import BaseSerializer
from sea_saw_attachment.serializers import AttachmentSerializer
from .purchase_item import (
    PurchaseItemSerializer,
    PurchaseItemSerializerForAdmin,
    PurchaseItemSerializerForSales,
    PurchaseItemSerializerForProduction,
    PurchaseItemSerializerForWarehouse,
)

from ..models import PurchaseOrder
from sea_saw_attachment.models import Attachment

from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin
from sea_saw_attachment.mixins import ReusableAttachmentWriteMixin


class PurchaseOrderSerializer(
    ReusableAttachmentWriteMixin, UniqueFieldsMixin, BaseSerializer
):
    """
    Purchase Order serializer with nested items and attachments.
    """

    purchase_items = PurchaseItemSerializer(
        many=True, required=False, allow_null=True, label=_("Purchase Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    attachment_model = Attachment

    class Meta(BaseSerializer.Meta):
        model = PurchaseOrder
        fields = [
            "id",
            "purchase_code",
            "purchase_date",
            "supplier",
            "contact",
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
            "purchase_items",
            "attachments",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["purchase_code", "total_amount"]


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
        fields = PurchaseOrderSerializer.Meta.fields


class PurchaseOrderSerializerForSales(PurchaseOrderSerializer):
    """
    Purchase Order serializer for sales users.
    """

    purchase_items = PurchaseItemSerializerForSales(
        many=True, required=False, allow_null=True, label=_("Purchase Items")
    )

    class Meta(PurchaseOrderSerializer.Meta):
        """设置全部字段为read-only"""

        fields = PurchaseOrderSerializer.Meta.fields
        read_only_fields = PurchaseOrderSerializer.Meta.fields


class PurchaseOrderSerializerForProduction(PurchaseOrderSerializer):
    """
    Purchase Order serializer for production users.
    Excludes financial fields (currency, deposit, balance, total_amount).
    """

    purchase_items = PurchaseItemSerializerForProduction(
        many=True, required=False, allow_null=True, label=_("Purchase Items")
    )

    class Meta(PurchaseOrderSerializer.Meta):
        """设置全部字段为read-only，排除金钱相关字段"""

        fields = [
            "id",
            "purchase_code",
            "purchase_date",
            "supplier",
            "contact",
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
        """设置全部字段为read-only，排除金钱相关字段"""

        fields = [
            "id",
            "purchase_code",
            "purchase_date",
            "supplier",
            "contact",
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
        read_only_fields = fields
