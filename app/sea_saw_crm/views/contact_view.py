from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_access_policy import AccessViewSetMixin

from ..models import Contact
from ..serializers import ContactSerializer
from ..metadata import BaseMetadata
from ..permissions import ContactAdminPermission, ContactSalePermission


class ContactViewSet(ModelViewSet, AccessViewSetMixin):
    """View set for Contact model"""

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [
        IsAuthenticated,
        ContactAdminPermission | ContactSalePermission,
    ]
    metadata_class = BaseMetadata

    search_fields = ["^name"]

    def get_queryset(self):
        """
        列表权限控制：
        - ADMIN 可以查看所有
        - SALE 只能看到可见的联系人
        """
        user = self.request.user
        role_type = getattr(user.role, "role_type", None)

        # Filter out soft-deleted records
        base_queryset = self.queryset.filter(deleted__isnull=True)

        if role_type == "ADMIN":
            return base_queryset

        # SALE: 只显示可见联系人
        get_users = getattr(user, "get_all_visible_users", None)
        if not callable(get_users):
            return base_queryset.none()

        return base_queryset.filter(owner__in=get_users())
