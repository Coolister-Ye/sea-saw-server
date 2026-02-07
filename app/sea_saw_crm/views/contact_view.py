from rest_framework.viewsets import ModelViewSet
from rest_access_policy import AccessViewSetMixin
from sea_saw_base.metadata import BaseMetadata

from ..models import Contact
from ..serializers import ContactSerializer
from ..permissions import ContactPermission


class ContactViewSet(ModelViewSet, AccessViewSetMixin):
    """View set for Contact model"""

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [ContactPermission]
    metadata_class = BaseMetadata

    search_fields = ["^name"]

    def get_queryset(self):
        user = self.request.user

        # Superusers and staff see all data
        if user.is_superuser or user.is_staff:
            return self.queryset

        role_type = getattr(user.role, "role_type", None)

        if role_type == "ADMIN":
            return self.queryset

        get_users = getattr(user, "get_all_visible_users", None)
        if not callable(get_users):
            return self.queryset.none()

        return self.queryset.filter(owner__in=get_users())
