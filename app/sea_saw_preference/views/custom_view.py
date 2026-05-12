from django.db import transaction
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from sea_saw_preference.models import CustomView
from sea_saw_preference.permissions import CanMutateCustomView
from sea_saw_preference.serializers import CustomViewSerializer


class CustomViewViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, CanMutateCustomView]
    serializer_class = CustomViewSerializer

    def get_object(self):
        if not hasattr(self, "_object"):
            self._object = super().get_object()
        return self._object

    def get_queryset(self):
        user = self.request.user
        qs = CustomView.objects.filter(
            Q(is_system=True)
            | Q(owner=user)
            | Q(visibility=CustomView.VisibilityChoice.PUBLIC)
            | Q(visibility=CustomView.VisibilityChoice.SHARED, shared_users=user)
            | Q(visibility=CustomView.VisibilityChoice.SHARED, shared_roles__users=user)
        ).distinct().select_related("owner").prefetch_related("shared_users", "shared_roles")

        entity = self.request.query_params.get("entity")
        if entity:
            qs = qs.filter(entity=entity)

        return qs.order_by("-is_default", "name")

    def _clear_existing_default(self, owner, entity, exclude_pk=None):
        qs = CustomView.objects.filter(owner=owner, entity=entity, is_default=True)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        qs.update(is_default=False)

    def perform_create(self, serializer):
        with transaction.atomic():
            if serializer.validated_data.get("is_default", False):
                self._clear_existing_default(
                    owner=self.request.user,
                    entity=serializer.validated_data["entity"],
                )
            serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        with transaction.atomic():
            if serializer.validated_data.get("is_default", False):
                self._clear_existing_default(
                    owner=self.request.user,
                    entity=serializer.instance.entity,
                    exclude_pk=serializer.instance.pk,
                )
            serializer.save()
