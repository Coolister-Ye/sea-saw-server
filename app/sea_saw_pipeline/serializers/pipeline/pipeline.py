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

from sea_saw_base.serializers import BaseSerializer
from sea_saw_pipeline.models import Pipeline
from sea_saw_crm.models import Account, Contact
from ...services import PipelineStateService

from sea_saw_crm.serializers import AccountMinimalSerializer, ContactMinimalSerializer
# Order serializers moved to sea_saw_sales app
from sea_saw_sales.serializers import (
    OrderSerializerForAdmin,
    OrderSerializerForSales,
    OrderSerializerForProduction,
    OrderSerializerForWarehouse,
)
# ProductionOrder serializers moved to sea_saw_production app
from sea_saw_production.serializers import (
    ProductionOrderSerializerForAdmin,
    ProductionOrderSerializerForSales,
    ProductionOrderSerializerForProduction,
    ProductionOrderSerializerForWarehouse,
)
# PurchaseOrder serializers moved to sea_saw_procurement app
from sea_saw_procurement.serializers import (
    PurchaseOrderSerializerForAdmin,
    PurchaseOrderSerializerForSales,
    PurchaseOrderSerializerForProduction,
    PurchaseOrderSerializerForWarehouse,
)
from sea_saw_warehouse.serializers import (
    OutboundOrderSerializerForAdmin,
    OutboundOrderSerializerForSales,
    OutboundOrderSerializerForProduction,
    OutboundOrderSerializerForWarehouse,
)
# Payment serializers moved to sea_saw_finance app
from sea_saw_finance.serializers import PaymentNestedSerializer as PaymentRecordSerializer


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
    "account",
    "account_id",
    "contact",
    "contact_id",
    "order_date",
    # Stage-level timestamps (all read-only, set automatically on transition)
    "confirmed_at",
    "in_purchase_at",
    "purchase_completed_at",
    "in_production_at",
    "production_completed_at",
    "in_purchase_and_production_at",
    "purchase_and_production_completed_at",
    "in_outbound_at",
    "outbound_completed_at",
    "completed_at",
    "cancelled_at",
    "remark",
]


# =====================================================
# Base Serializers
# =====================================================


class BasePipelineSerializer(BaseSerializer):
    """
    所有 Pipeline serializer 的基类
    """

    allowed_actions = serializers.SerializerMethodField()
    account = AccountMinimalSerializer(read_only=True, label=_("Company"))
    account_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        source="account",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Company ID"),
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

    class Meta(BaseSerializer.Meta):
        model = Pipeline
        # Explicitly define all fields to prevent mass assignment vulnerability
        # Child classes can extend this list with additional fields
        fields = BASE_FIELDS + [
            "owner",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "allowed_actions",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at", "allowed_actions"]

    def get_allowed_actions(self, obj):
        request = self.context.get("request")
        if not request:
            return []
        # Use PipelineStateService for state management
        return PipelineStateService.get_allowed_actions(obj, request.user)


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
            "active_entity",
            "confirmed_at",
            "in_purchase_at",
            "purchase_completed_at",
            "in_production_at",
            "production_completed_at",
            "in_purchase_and_production_at",
            "purchase_and_production_completed_at",
            "in_outbound_at",
            "outbound_completed_at",
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
            "active_entity",
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
            "active_entity",
            "pipeline_code",
            "pipeline_type",
            "status",
            "order",
            "contact",
            "order_date",
            "total_amount",
            "paid_amount",
        ]
