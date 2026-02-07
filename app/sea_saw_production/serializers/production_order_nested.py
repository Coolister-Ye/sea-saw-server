from sea_saw_base.serializers import BaseSerializer
from sea_saw_attachment.serializers import AttachmentSerializer
from .production_item import (
    ProductionItemSerializer,
    ProductionItemSerializerForAdmin,
    ProductionItemSerializerForSales,
    ProductionItemSerializerForProduction,
    ProductionItemSerializerForWarehouse,
)

from ..models import ProductionOrder
from sea_saw_attachment.models import Attachment

from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin
from sea_saw_attachment.mixins import ReusableAttachmentWriteMixin


class ProductionOrderSerializer(
    ReusableAttachmentWriteMixin, UniqueFieldsMixin, BaseSerializer
):
    """
    Production Order serializer with optimized field order.
    Excludes created_by and updated_by fields.
    """

    production_items = ProductionItemSerializer(
        many=True, required=False, allow_null=True, label=_("Production Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    attachment_model = Attachment

    class Meta(BaseSerializer.Meta):
        model = ProductionOrder
        fields = [
            "id",
            "production_code",
            "status",
            "planned_date",
            "start_date",
            "end_date",
            "remark",
            "comment",
            "production_items",
            "attachments",
            "owner",
            "created_at",
            "updated_at",
        ]


class ProductionOrderSerializerForAdmin(ProductionOrderSerializer):
    """
    Order serializer for admin users.
    """

    production_items = ProductionItemSerializerForAdmin(
        many=True, required=False, allow_null=True, label=_("Production Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    class Meta(ProductionOrderSerializer.Meta):
        fields = ProductionOrderSerializer.Meta.fields


class ProductionOrderSerializerForSales(ProductionOrderSerializer):
    """
    Order serializer for sales users.
    """

    production_items = ProductionItemSerializerForSales(
        many=True, required=False, allow_null=True, label=_("Production Items")
    )

    class Meta(ProductionOrderSerializer.Meta):
        """设置全部字段为read-only"""

        fields = ProductionOrderSerializer.Meta.fields
        read_only_fields = ProductionOrderSerializer.Meta.fields


class ProductionOrderSerializerForProduction(ProductionOrderSerializer):
    """
    Order serializer for production users.
    """

    production_items = ProductionItemSerializerForProduction(
        many=True, required=False, allow_null=True, label=_("Production Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    class Meta(ProductionOrderSerializer.Meta):
        fields = ProductionOrderSerializer.Meta.fields


class ProductionOrderSerializerForWarehouse(ProductionOrderSerializer):
    """
    Order serializer for warehouse users.
    """

    production_items = ProductionItemSerializerForWarehouse(
        many=True, required=False, allow_null=True, label=_("Production Items")
    )

    class Meta(ProductionOrderSerializer.Meta):
        """设置全部字段为read-only"""

        fields = ProductionOrderSerializer.Meta.fields
        read_only_fields = ProductionOrderSerializer.Meta.fields
