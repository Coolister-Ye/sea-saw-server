"""
Order Serializers - Standalone version for direct Order access

用于 OrderViewSet，提供独立的 Order 访问
显示关联的 Pipeline 信息
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from drf_writable_nested.mixins import UniqueFieldsMixin

from ..base import BaseSerializer
from ..shared import AttachmentSerializer
from ..contact import ContactSerializer
from ..company import CompanySerializer
from .order_item import OrderItemSerializerForAdmin
from ...models.order import Order
from ...models.pipeline import Pipeline
from sea_saw_attachment.models import Attachment
from ...models import Contact
from ...models.company import Company
from ...mixins import ReusableAttachmentWriteMixin
from ..mixins import PipelineSyncMixin


class PipelineNestedSerializer(BaseSerializer):
    """
    Simplified Pipeline serializer for nested display in Order.
    """

    class Meta(BaseSerializer.Meta):
        model = Pipeline
        fields = ["id", "pipeline_code", "status", "active_entity", "pipeline_type", "order_date"]


class OrderSerializerForOrderView(
    PipelineSyncMixin, ReusableAttachmentWriteMixin, UniqueFieldsMixin, BaseSerializer
):
    """
    Order serializer for OrderViewSet (standalone access).
    Used by all roles for direct Order access.
    - Displays related_pipeline as nested object
    - Includes full order items and attachments
    """

    company = CompanySerializer(read_only=True, label=_("Company"))
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source="company",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Company ID"),
    )

    contact = ContactSerializer(read_only=True, label=_("Contact"))
    contact_id = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        source="contact",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Contact ID"),
    )

    order_items = OrderItemSerializerForAdmin(
        many=True, required=False, allow_null=True, label=_("Order Items")
    )

    attachments = AttachmentSerializer(
        many=True, required=False, allow_null=True, label=_("Attachments")
    )

    related_pipeline = PipelineNestedSerializer(
        source='pipeline',  # Map to the actual OneToOne reverse relation field
        required=False,
        allow_null=True,
        read_only=True,
        label=_("Related Pipeline"),
    )

    # Add active_entity from related Pipeline (read-only)
    active_entity = serializers.SerializerMethodField(
        label=_("Active Entity"),
        help_text=_("Currently active sub-entity type from the related Pipeline")
    )

    attachment_model = Attachment

    def get_active_entity(self, obj):
        """Get active_entity from related Pipeline if it exists"""
        try:
            return obj.pipeline.active_entity if hasattr(obj, 'pipeline') and obj.pipeline else None
        except Exception:
            return None

    class Meta(BaseSerializer.Meta):
        model = Order
        fields = [
            "id",
            "order_code",
            "order_date",
            "company",
            "company_id",
            "contact",
            "contact_id",
            "etd",
            "status",
            "active_entity",
            "loading_port",
            "destination_port",
            "shipment_term",
            "inco_terms",
            "currency",
            "deposit",
            "balance",
            "total_amount",
            "comment",
            "order_items",
            "attachments",
            "related_pipeline",
            "owner",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """Handle related_pipeline assignment."""
        # Note: 'pipeline' is popped because it's a reverse OneToOne relation
        # and cannot be set directly on Order creation
        validated_data.pop("pipeline", None)

        # Attachments are handled by ReusableAttachmentWriteMixin
        instance = super().create(validated_data)
        # Pipeline should be created/assigned from Pipeline side, not Order side
        return instance

    def update(self, instance, validated_data):
        """
        Handle Order update with automatic Pipeline synchronization.

        When order fields are updated, related pipeline fields are automatically synced:
        - contact → pipeline.contact
        - order_date → pipeline.order_date
        """
        # Note: 'pipeline' is popped because it's a reverse OneToOne relation
        # and cannot be set directly on Order update
        validated_data.pop("pipeline", None)

        # Attachments are handled by ReusableAttachmentWriteMixin
        instance = super().update(instance, validated_data)

        # Sync to pipeline if it exists (from PipelineSyncMixin)
        self.sync_to_pipeline(instance)

        return instance
