from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..base import BaseSerializer


class BaseAttachmentSerializer(BaseSerializer):
    """
    Base serializer for all attachment types.
    Handles:
    - write-only file upload
    - safe update when file is URL string
    - file_url generation
    """

    file = serializers.FileField(
        required=False,
        allow_null=True,
        write_only=True,
        label=_("File"),
    )
    file_url = serializers.SerializerMethodField(label=_("File URL"))

    def to_internal_value(self, data):
        """
        Ignore file field when frontend sends back URL string during update.
        """
        if hasattr(data, "_mutable"):
            data._mutable = True
        elif not isinstance(data, dict):
            data = dict(data)
        else:
            data = data.copy() if hasattr(data, "copy") else dict(data)

        file_value = data.get("file")
        if isinstance(file_value, str):
            data.pop("file", None)

        return super().to_internal_value(data)

    def get_file_url(self, obj):
        if not obj.file:
            return None

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url
