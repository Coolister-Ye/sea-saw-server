from rest_framework import serializers

from sea_saw_preference.models import UserFilterPreset


class FilterPresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFilterPreset
        fields = ["id", "entity", "name", "key", "params", "preset_type", "created_at", "updated_at"]
        read_only_fields = ["id", "preset_type", "created_at", "updated_at"]
