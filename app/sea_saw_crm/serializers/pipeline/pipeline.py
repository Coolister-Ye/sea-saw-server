"""
Pipeline Serializers - Business Process Orchestration

Pipeline作为业务流程的主入口，包含:
- Order (销售订单)
- ProductionOrders (生产订单列表)
- PurchaseOrders (采购订单列表)
- OutboundOrders (出库订单列表)
- Payments (付款记录列表)
- Attachments (附件列表)
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin

from ..base import BaseSerializer
from ...models import Pipeline, Contact
from ...services import PipelineStateService

from ..contact import ContactSerializer
from ..order import (
    OrderSerializerForAdmin,
    OrderSerializerForSales,
    OrderSerializerForProduction,
    OrderSerializerForWarehouse,
)
from ..production import (
    ProductionOrderSerializerForAdmin,
    ProductionOrderSerializerForSales,
    ProductionOrderSerializerForProduction,
    ProductionOrderSerializerForWarehouse,
)
from ..purchase import (
    PurchaseOrderSerializerForAdmin,
    PurchaseOrderSerializerForSales,
    PurchaseOrderSerializerForProduction,
    PurchaseOrderSerializerForWarehouse,
)
from ..outbound import (
    OutboundOrderSerializerForAdmin,
    OutboundOrderSerializerForSales,
    OutboundOrderSerializerForProduction,
    OutboundOrderSerializerForWarehouse,
)
from ..payment.payment_nested import PaymentNestedSerializer as PaymentRecordSerializer


# =====================================================
# Base Serializers
# =====================================================


class BasePipelineSerializer(BaseSerializer):
    """
    所有 Pipeline serializer 的基类
    """

    allowed_actions = serializers.SerializerMethodField()
    contact = ContactSerializer(read_only=True, label=_("Contact"))
    contact_id = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        source="contact",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Contact ID"),
    )

    class Meta(BaseSerializer.Meta):
        model = Pipeline
        fields = "__all__"

    def get_allowed_actions(self, obj):
        request = self.context.get("request")
        if not request:
            return []
        # Use PipelineStateService for state management
        return PipelineStateService.get_allowed_actions(obj, request.user)


# =====================================================
# Shared field groups
# =====================================================

BASE_FIELDS = [
    "id",
    "pipeline_code",
    "pipeline_type",
    "status",
    "active_entity",
    "order",
    "contact",
    "contact_id",
    "order_date",
    "confirmed_at",
    "completed_at",
    "cancelled_at",
    "remark",
]


# =====================================================
# Admin Role Serializer
# =====================================================


class PipelineSerializerForAdmin(UniqueFieldsMixin, BasePipelineSerializer):
    """
    Pipeline serializer for Admin role - Full access to all fields and sub-entities
    """

    order = OrderSerializerForAdmin(required=False, label=_("Order"))
    production_orders = ProductionOrderSerializerForAdmin(
        many=True, required=False, label=_("Production Orders")
    )
    purchase_orders = PurchaseOrderSerializerForAdmin(
        many=True, required=False, label=_("Purchase Orders")
    )
    outbound_orders = OutboundOrderSerializerForAdmin(
        many=True, required=False, label=_("Outbound Orders")
    )
    payments = PaymentRecordSerializer(
        many=True,
        required=False,
        label=_("Payment Records"),
    )

    class Meta(BasePipelineSerializer.Meta):
        fields = BASE_FIELDS + [
            "production_orders",
            "purchase_orders",
            "outbound_orders",
            "payments",
            "owner",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "allowed_actions",
        ]
        read_only_fields = [
            "confirmed_at",
            "completed_at",
            "cancelled_at",
            "total_amount",
            "paid_amount",
        ]


# =====================================================
# Sales Role Serializer
# =====================================================


class PipelineSerializerForSales(UniqueFieldsMixin, BasePipelineSerializer):
    """
    Pipeline serializer for Sales role - Focus on order and payment info
    """

    order = OrderSerializerForSales(required=False, label=_("Order"))
    production_orders = ProductionOrderSerializerForSales(
        many=True, required=False, label=_("Production Orders")
    )
    purchase_orders = PurchaseOrderSerializerForSales(
        many=True, required=False, label=_("Purchase Orders")
    )
    outbound_orders = OutboundOrderSerializerForSales(
        many=True, required=False, label=_("Outbound Orders")
    )
    payments = PaymentRecordSerializer(
        many=True,
        required=False,
        label=_("Payment Records"),
    )

    class Meta(BasePipelineSerializer.Meta):
        fields = BASE_FIELDS + [
            "production_orders",
            "purchase_orders",
            "outbound_orders",
            "payments",
            "owner",
            "allowed_actions",
        ]
        read_only_fields = [
            "production_orders",
            "purchase_orders",
            "outbound_orders",
        ]


# =====================================================
# Production Role Serializer
# =====================================================


class PipelineSerializerForProduction(BasePipelineSerializer):
    """
    Pipeline serializer for Production role - Focus on production and manufacturing
    """

    order = OrderSerializerForProduction(required=False, label=_("Order"))
    production_orders = ProductionOrderSerializerForProduction(
        many=True, required=False, label=_("Production Orders")
    )
    purchase_orders = PurchaseOrderSerializerForProduction(
        many=True, required=False, label=_("Purchase Orders")
    )
    outbound_orders = OutboundOrderSerializerForProduction(
        many=True, required=False, label=_("Outbound Orders")
    )

    class Meta(BasePipelineSerializer.Meta):
        fields = BASE_FIELDS + [
            "production_orders",
            "purchase_orders",
            "outbound_orders",
            "allowed_actions",
        ]
        read_only_fields = fields


# =====================================================
# Warehouse Role Serializer
# =====================================================


class PipelineSerializerForWarehouse(BasePipelineSerializer):
    """
    Pipeline serializer for Warehouse role - Focus on inventory and outbound
    """

    order = OrderSerializerForWarehouse(required=False, label=_("Order"))
    production_orders = ProductionOrderSerializerForWarehouse(
        many=True, required=False, label=_("Production Orders")
    )
    purchase_orders = PurchaseOrderSerializerForWarehouse(
        many=True, required=False, label=_("Purchase Orders")
    )
    outbound_orders = OutboundOrderSerializerForWarehouse(
        many=True, required=False, label=_("Outbound Orders")
    )

    class Meta(BasePipelineSerializer.Meta):
        fields = BASE_FIELDS + [
            "production_orders",
            "purchase_orders",
            "outbound_orders",
            "allowed_actions",
        ]
        read_only_fields = [
            "pipeline_code",
            "pipeline_type",
            "status",
            "order",
            "contact",
            "order_date",
            "total_amount",
            "paid_amount",
        ]
