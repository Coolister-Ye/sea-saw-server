from django.utils.translation import gettext_lazy as _

from sea_saw_base.serializers import BaseSerializer
from sea_saw_crm.serializers import (
    AccountMinimalSerializer,
    ContactMinimalSerializer,
    BankAccountMinimalSerializer,
)

from .order_item import OrderItemSerializerForAdmin
from .pipeline_minimal import PipelineMinimalSerializer
from ..models import Order


class OrderSerializerForDownload(BaseSerializer):
    """
    Read-only Order serializer for CSV export.
    Excludes attachments and write-only fields to keep the output clean.
    """

    buyer = AccountMinimalSerializer(read_only=True, label=_("Buyer"))
    seller = AccountMinimalSerializer(read_only=True, label=_("Seller"))
    shipper = AccountMinimalSerializer(read_only=True, label=_("Shipper"))
    contact = ContactMinimalSerializer(read_only=True, label=_("Contact"))
    bank_account = BankAccountMinimalSerializer(read_only=True, label=_("Bank Account"))
    order_items = OrderItemSerializerForAdmin(
        many=True, read_only=True, label=_("Order Items")
    )
    related_pipeline = PipelineMinimalSerializer(
        source="pipeline",
        read_only=True,
        label=_("Related Pipeline"),
    )

    class Meta(BaseSerializer.Meta):
        model = Order
        fields = [
            "id",
            "order_code",
            "order_date",
            "buyer",
            "seller",
            "shipper",
            "contact",
            "bank_account",
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
            "related_pipeline",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
