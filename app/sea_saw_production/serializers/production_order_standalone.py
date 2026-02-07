from sea_saw_base.serializers import BaseSerializer
from sea_saw_attachment.serializers import AttachmentSerializer
from .production_item import ProductionItemSerializer
from ..models import ProductionOrder
from sea_saw_sales.models import Order

from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin


class OrderNestedSerializer(BaseSerializer):
    """
    Simplified Order serializer for nested display in ProductionOrder.
    """

    class Meta(BaseSerializer.Meta):
        model = Order
        fields = ["id", "order_code", "order_date", "status", "etd"]


class ProductionOrderSerializerForProductionView(UniqueFieldsMixin, BaseSerializer):
    """
    Production Order serializer for ProductionOrderViewSet.
    Used by ADMIN and PRODUCTION roles only.
    - Displays related_order as nested object
    - Excludes created_by and updated_by fields
    """

    production_items = ProductionItemSerializer(
        many=True, required=False, allow_null=True, label=_("Production Items")
    )

    attachments = AttachmentSerializer(
        many=True, required=False, allow_null=True, label=_("Attachments")
    )

    related_order = OrderNestedSerializer(
        required=False,
        allow_null=True,
        read_only=False,
        label=_("Related Order"),
    )

    class Meta(BaseSerializer.Meta):
        model = ProductionOrder
        fields = [
            "id",
            "production_code",
            "status",
            "planned_date",
            "start_date",
            "end_date",
            "comment",
            "production_items",
            "attachments",
            "related_order",
            "owner",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """Handle related_order assignment."""
        validated_data.pop("related_order", None)
        instance = super().create(validated_data)
        self.assign_direct_relation(instance, "related_order", Order)
        return instance

    def update(self, instance, validated_data):
        """Handle related_order assignment."""
        validated_data.pop("related_order", None)
        instance = super().update(instance, validated_data)
        self.assign_direct_relation(instance, "related_order", Order)
        return instance
