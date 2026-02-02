"""
Attachment Serializers
"""
from rest_framework import serializers
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..models import Attachment

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class AttachmentSerializer(serializers.ModelSerializer):
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

    # File upload (write-only)
    file = serializers.FileField(
        required=False,
        allow_null=True,
        write_only=True,
        label=_("File"),
    )

    # File URL (read-only)
    file_url = serializers.SerializerMethodField(label=_("File URL"))

    # Generic field for the related entity ID (read-only)
    related_id = serializers.IntegerField(
        source="object_id", read_only=True, label=_("Related Entity ID")
    )

    # Attachment type (auto-set by model)
    attachment_type = serializers.CharField(read_only=True, label=_("Attachment Type"))

    # Owner fields (read-only)
    owner = serializers.CharField(
        source="owner.username", read_only=True, allow_null=True, label=_("Owner")
    )
    created_by = serializers.CharField(
        source="created_by.username",
        read_only=True,
        allow_null=True,
        label=_("Created By"),
    )
    created_at = serializers.DateTimeField(
        read_only=True, format=DATETIME_FORMAT, allow_null=True, label=_("Created At")
    )
    updated_at = serializers.DateTimeField(
        read_only=True, format=DATETIME_FORMAT, allow_null=True, label=_("Updated At")
    )

    class Meta:
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
            "owner",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "related_id",
            "attachment_type",
            "file_name",
            "file_size",
            "owner",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def to_internal_value(self, data):
        """
        Ignore file field when frontend sends back URL string during update.
        """
        # Make data mutable if it's a QueryDict
        if hasattr(data, "_mutable"):
            data._mutable = True
        elif not isinstance(data, dict):
            data = dict(data)
        else:
            data = data.copy() if hasattr(data, "copy") else dict(data)

        # Remove file field if it's a string (URL)
        file_value = data.get("file")
        if isinstance(file_value, str):
            data.pop("file", None)

        return super().to_internal_value(data)

    def get_file_url(self, obj):
        """
        Generate secure download URL for attachment.

        Uses the protected download endpoint instead of direct media URL.
        This ensures permission checks are enforced on every download.

        Returns:
            str: URL to the secure download endpoint
        """
        if not obj.file or not obj.pk:
            return None

        request = self.context.get("request")

        # Generate URL to the secure download endpoint
        download_path = reverse(
            "sea-saw-attachment:attachment-download", kwargs={"attachment_id": obj.pk}
        )

        if request:
            return request.build_absolute_uri(download_path)
        return download_path
