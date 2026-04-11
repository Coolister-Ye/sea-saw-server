from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from sea_saw_preference.models import UserFilterPreset
from sea_saw_preference.serializers import FilterPresetSerializer


class FilterPresetViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FilterPresetSerializer

    def get_queryset(self):
        # Return system presets (shared) + the current user's own presets
        qs = UserFilterPreset.objects.filter(
            Q(preset_type=UserFilterPreset.PRESET_TYPE_SYSTEM)
            | Q(user=self.request.user)
        )
        entity = self.request.query_params.get("entity")
        if entity:
            qs = qs.filter(entity=entity)
        # System presets first, then user presets ordered by creation time
        return qs.order_by("preset_type", "created_at")

    def perform_create(self, serializer):
        # Users can only create their own presets
        serializer.save(user=self.request.user, preset_type=UserFilterPreset.PRESET_TYPE_USER)

    def get_object(self):
        obj = super().get_object()
        if obj.preset_type == UserFilterPreset.PRESET_TYPE_SYSTEM and self.action in (
            "update",
            "partial_update",
            "destroy",
        ):
            raise PermissionDenied("System presets cannot be modified or deleted.")
        return obj
