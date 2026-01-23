"""
Unified Attachment Serializer for GenericForeignKey-based Attachment model
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..base import BaseSerializer
from ...models import Attachment
from .base_attachment import BaseAttachmentSerializer


class AttachmentSerializer(BaseAttachmentSerializer):
    """
    Unified serializer for all attachment types.

    Works with the unified Attachment model that uses GenericForeignKey.
    The related entity (order, production_order, etc.) is read from object_id.

    Usage:
        # In Order serializer
        attachments = AttachmentSerializer(many=True, required=False)

        # In ProductionOrder serializer
        attachments = AttachmentSerializer(many=True, required=False)

    The serializer automatically handles:
    - File upload and URL generation
    - Auto-population of file_name and file_size
    - Attachment type detection from content_type
    """

    # Generic field for the related entity ID (read-only)
    related_id = serializers.IntegerField(
        source='object_id',
        read_only=True,
        label=_("Related Entity ID")
    )

    # Attachment type (auto-set by model)
    attachment_type = serializers.CharField(
        read_only=True,
        label=_("Attachment Type")
    )

    class Meta(BaseSerializer.Meta):
        model = Attachment
        fields = [
            "id",
            "related_id",
            "attachment_type",
            "file",
            "file_url",
            "file_name",
            "file_size",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "related_id",
            "attachment_type",
            "file_name",
            "file_size",
            "created_at",
            "updated_at",
        ]
