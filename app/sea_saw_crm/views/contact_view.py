from rest_framework.viewsets import ModelViewSet
from rest_access_policy import AccessViewSetMixin

from ..models import Contact
from ..serializers import ContactSerializer

from ..permissions import ContactPermission


class ContactViewSet(ModelViewSet, AccessViewSetMixin):
    """View set for Contact model"""

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [ContactPermission]

    search_fields = ["^name"]

    def get_queryset(self):
        """
        列表权限控制：
        - ADMIN 可以查看所有
        - SALE 只能看到可见的联系人
        """
        user = self.request.user
        role_type = getattr(user.role, "role_type", None)

        if role_type == "ADMIN":
            return self.queryset

        # SALE: 只显示可见联系人
        get_users = getattr(user, "get_all_visible_users", None)
        if not callable(get_users):
            return self.queryset.none()

        return self.queryset.filter(owner__in=get_users())
