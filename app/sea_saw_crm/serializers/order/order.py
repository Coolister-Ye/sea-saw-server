from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..base import BaseSerializer
from ...models import Order, Contact
from ...services import OrderStateService

from ..contact import ContactSerializer
from ..payment import PaymentRecordSerializer

from .order_item import (
    OrderItemSerializerForAdmin,
    OrderItemSerializerForSales,
    OrderItemSerializerForProduction,
    OrderItemSerializerForWarehouse,
)

from ..production import (
    ProductionOrderSerializerForAdmin,
    ProductionOrderSerializerForSales,
    ProductionOrderSerializerForProduction,
    ProductionOrderSerializerForWarehouse,
)

from ..outbound import (
    OutboundOrderSerializerForAdmin,
    OutboundOrderSerializerForSales,
    OutboundOrderSerializerForProduction,
    OutboundOrderSerializerForWarehouse,
)

# =====================================================
# Common mixins & base
# =====================================================


class OrderContactMixin:
    """
    统一处理 contact 的 create / update
    """

    def _handle_contact(self, instance, validated_data):
        validated_data.pop("contact", None)
        self.assign_direct_relation(instance, "contact", Contact)

    def create(self, validated_data):
        instance = super().create(validated_data)
        self._handle_contact(instance, validated_data)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self._handle_contact(instance, validated_data)
        return instance


class BaseOrderSerializer(BaseSerializer):
    """
    所有 Order serializer 的基类
    """

    allowed_actions = serializers.SerializerMethodField()
    contact = ContactSerializer(required=False, label=_("Contact"))

    class Meta(BaseSerializer.Meta):
        model = Order
        fields = "__all__"

    def get_allowed_actions(self, obj):
        request = self.context.get("request")
        if not request:
            return []
        return OrderStateService.get_allowed_actions(obj, request.user)


# =====================================================
# Shared field groups
# =====================================================

BASE_FIELDS = [
    "id",
    "order_code",
    "order_date",
    "contact",
    "etd",
    "status",
    "loading_port",
    "destination_port",
    "shipment_term",
    "comment",
]


# =====================================================
# Admin
# =====================================================


class OrderSerializerForAdmin(OrderContactMixin, BaseOrderSerializer):
    order_items = OrderItemSerializerForAdmin(
        many=True, required=False, label=_("Order Items")
    )
    production_orders = ProductionOrderSerializerForAdmin(
        many=True, required=False, label=_("Production Orders")
    )
    outbound_orders = OutboundOrderSerializerForAdmin(
        many=True, required=False, label=_("Outbound Orders")
    )
    payments = PaymentRecordSerializer(
        many=True, required=False, label=_("Payment Records")
    )

    class Meta(BaseOrderSerializer.Meta):
        fields = BASE_FIELDS + [
            "inco_terms",
            "currency",
            "deposit",
            "balance",
            "total_amount",
            "owner",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "order_items",
            "production_orders",
            "outbound_orders",
            "payments",
        ]


# =====================================================
# Sales
# =====================================================


class OrderSerializerForSales(OrderContactMixin, BaseOrderSerializer):
    order_items = OrderItemSerializerForSales(
        many=True, required=False, label=_("Order Items")
    )
    production_orders = ProductionOrderSerializerForSales(
        many=True, required=False, label=_("Production Orders")
    )
    outbound_orders = OutboundOrderSerializerForSales(
        many=True, required=False, label=_("Outbound Orders")
    )
    payments = PaymentRecordSerializer(
        many=True, required=False, label=_("Payment Records")
    )

    class Meta(BaseOrderSerializer.Meta):
        fields = BASE_FIELDS + [
            "inco_terms",
            "currency",
            "deposit",
            "balance",
            "total_amount",
            "owner",
            "order_items",
            "production_orders",
            "outbound_orders",
            "payments",
        ]
        read_only_fields = [
            "production_orders",
            "outbound_orders",
        ]


# =====================================================
# Production
# =====================================================


class OrderSerializerForProduction(BaseOrderSerializer):
    order_items = OrderItemSerializerForProduction(
        many=True, required=False, label=_("Order Items")
    )
    production_orders = ProductionOrderSerializerForProduction(
        many=True, required=False, label=_("Production Orders")
    )
    outbound_orders = OutboundOrderSerializerForProduction(
        many=True, required=False, label=_("Outbound Orders")
    )

    class Meta(BaseOrderSerializer.Meta):
        fields = BASE_FIELDS + [
            "order_items",
            "production_orders",
            "outbound_orders",
        ]
        read_only_fields = fields


# =====================================================
# Warehouse
# =====================================================


class OrderSerializerForWarehouse(BaseOrderSerializer):
    order_items = OrderItemSerializerForWarehouse(
        many=True, required=False, label=_("Order Items")
    )
    production_orders = ProductionOrderSerializerForWarehouse(
        many=True, required=False, label=_("Production Orders")
    )
    outbound_orders = OutboundOrderSerializerForWarehouse(
        many=True, required=False, label=_("Outbound Orders")
    )

    class Meta(BaseOrderSerializer.Meta):
        fields = BASE_FIELDS + [
            "order_items",
            "production_orders",
            "outbound_orders",
        ]
        read_only_fields = fields
