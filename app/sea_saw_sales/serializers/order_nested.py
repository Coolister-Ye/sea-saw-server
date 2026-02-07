"""
Order Serializers - Nested version for operations under Pipeline

用于 NestedOrderViewSet，处理嵌套在 Pipeline 下的 Order 操作
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin

from sea_saw_base.serializers import BaseSerializer
from sea_saw_crm.serializers import AccountMinimalSerializer, ContactMinimalSerializer
from sea_saw_attachment.serializers import AttachmentSerializer
from sea_saw_attachment.mixins import ReusableAttachmentWriteMixin
from .mixins import PipelineSyncMixin
from sea_saw_crm.models import Account, Contact
from ..models import Order, OrderStatusType

from .order_item import (
    OrderItemSerializerForAdmin,
    OrderItemSerializerForSales,
    OrderItemSerializerForProduction,
    OrderItemSerializerForWarehouse,
)

# =====================================================
# Shared field groups
# =====================================================

BASE_FIELDS = [
    "id",
    "order_code",
    "order_date",
    "account",
    "account_id",
    "contact",
    "contact_id",
    "etd",
    "status",
    "active_entity",
    "loading_port",
    "destination_port",
    "shipment_term",
]


# =====================================================
# Base Serializer for Nested Operations
# =====================================================


class BaseOrderSerializer(
    PipelineSyncMixin, ReusableAttachmentWriteMixin, BaseSerializer
):
    """
    所有 Order serializer 的基类
    统一处理 attachments 的 create / update
    """

    account = AccountMinimalSerializer(read_only=True, label=_("Account"))
    account_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        source="account",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Account ID"),
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

    # Add active_entity from related Pipeline (read-only)
    active_entity = serializers.SerializerMethodField(
        label=_("Active Entity"),
        help_text=_("Currently active sub-entity type from the related Pipeline")
    )

    def get_active_entity(self, obj):
        """Get active_entity from related Pipeline if it exists"""
        try:
            return obj.pipeline.active_entity if hasattr(obj, 'pipeline') and obj.pipeline else None
        except Exception:
            return None

    def update(self, instance, validated_data):
        # Let parent classes handle the update:
        # - ReusableAttachmentWriteMixin handles attachments
        # - UniqueFieldsMixin (in child classes) handles order_items
        instance = super().update(instance, validated_data)

        # Sync to pipeline if it exists (from PipelineSyncMixin)
        self.sync_to_pipeline(instance)

        return instance

    class Meta(BaseSerializer.Meta):
        model = Order
        # Explicitly define all fields to prevent mass assignment vulnerability
        # Child classes can extend this list with additional fields
        fields = BASE_FIELDS + [
            "inco_terms",
            "currency",
            "deposit",
            "balance",
            "total_amount",
            "comment",
            "owner",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "id", "created_at", "updated_at"]


# =====================================================
# Admin Role Serializer
# =====================================================


class OrderSerializerForAdmin(UniqueFieldsMixin, BaseOrderSerializer):
    """
    Order serializer for Admin role
    Includes order items and attachments
    """

    order_items = OrderItemSerializerForAdmin(
        many=True, required=False, label=_("Order Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    class Meta(BaseOrderSerializer.Meta):
        fields = BASE_FIELDS + [
            "inco_terms",
            "currency",
            "deposit",
            "balance",
            "total_amount",
            "comment",
            "attachments",
            "order_items",
            "owner",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]


# =====================================================
# Sales Role Serializer
# =====================================================


class OrderSerializerForSales(UniqueFieldsMixin, BaseOrderSerializer):
    """
    Order serializer for Sales role
    Full access to order data, items and attachments
    """

    order_items = OrderItemSerializerForSales(
        many=True, required=False, label=_("Order Items")
    )
    attachments = AttachmentSerializer(
        many=True, required=False, label=_("Attachments")
    )

    class Meta(BaseOrderSerializer.Meta):
        fields = BASE_FIELDS + [
            "inco_terms",
            "currency",
            "deposit",
            "balance",
            "total_amount",
            "comment",
            "owner",
            "attachments",
            "order_items",
        ]


# =====================================================
# Production Role Serializer
# =====================================================


class OrderSerializerForProduction(BaseOrderSerializer):
    """
    Order serializer for Production role
    Read-only view of order data for production planning
    """

    order_items = OrderItemSerializerForProduction(
        many=True, required=False, label=_("Order Items")
    )

    class Meta(BaseOrderSerializer.Meta):
        fields = BASE_FIELDS + [
            "comment",
            "owner",
            "order_items",
        ]
        read_only_fields = fields


# =====================================================
# Warehouse Role Serializer
# =====================================================


class OrderSerializerForWarehouse(BaseOrderSerializer):
    """
    Order serializer for Warehouse role
    Read-only view for shipping and logistics info
    """

    order_items = OrderItemSerializerForWarehouse(
        many=True, required=False, label=_("Order Items")
    )

    class Meta(BaseOrderSerializer.Meta):
        fields = BASE_FIELDS + [
            "comment",
            "owner",
            "order_items",
        ]
        read_only_fields = fields
