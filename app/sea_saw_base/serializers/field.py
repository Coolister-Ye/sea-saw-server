from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from sea_saw_base.models import Field
from .base import BaseSerializer


class FieldSerializer(BaseSerializer):
    """
    Serializer for the Field model.
    - @field_option: The choice of field for picklist type.
    - @content_type: Use the name of the model for serialization/deserialization.
    """

    content_type = serializers.CharField(
        source="content_type.model",
        label=_("Content Type"),
        help_text=_("The model associated with this field."),
    )

    class Meta:
        model = Field
        fields = [
            "pk",
            "field_name",
            "field_type",
            "is_active",
            "is_mandatory",
            "content_type",
            "extra_info",
            "owner",
        ]

    def validate(self, data):
        """
        Validate the field data:
        - Picklist fields must include a 'picklist' key in `extra_info`.
        """
        if data.get("field_type") == "picklist" and not data.get("extra_info", {}).get(
            "choices"
        ):
            raise serializers.ValidationError(
                'Picklist field requires a "picklist" key in extra_info.'
            )
        return data

    @staticmethod
    def get_content_model(content_type_data):
        """
        Resolve content_type from the provided model name.
        """
        try:
            return ContentType.objects.get_by_natural_key(
                app_label="sea_saw_crm", model=content_type_data["model"]
            )
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                {
                    "content_type": f"ContentType for model '{content_type_data['model']}' does not exist."
                }
            )

    def handle_content_type(self, validated_data):
        """
        Convert content_type data to ContentType instance.
        """
        content_type_data = validated_data.pop("content_type", None)
        if content_type_data:
            validated_data["content_type"] = self.get_content_model(content_type_data)
        return validated_data

    def create(self, validated_data):
        """
        Support creating objects using model names for content_type.
        """
        validated_data = self.handle_content_type(validated_data)
        return Field.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Validate immutable fields and update the instance.
        """
        immutable_fields = ["field_name", "field_type"]
        for field in immutable_fields:
            if field in validated_data and validated_data[field] != getattr(
                instance, field
            ):
                raise serializers.ValidationError(
                    {field: f"The field '{field}' cannot be updated."}
                )

        validated_data = self.handle_content_type(validated_data)
        return super().update(instance, validated_data)
