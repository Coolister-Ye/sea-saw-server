from rest_framework.viewsets import ModelViewSet

from ..models import Company
from ..serializers import CompanySerializer
from ..permissions import CompanyPermission


class CompanyViewSet(ModelViewSet):
    """View set for Contact model"""

    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [CompanyPermission]

    search_fields = ["^company_name"]

    def get_queryset(self):
        user = self.request.user
        role_type = getattr(user.role, "role_type", None)

        # ADMIN 可以查看所有
        if role_type == "ADMIN":
            return self.queryset

        # SALE: 只显示可见的联系人
        get_users = getattr(user, "get_all_visible_users", None)
        if not callable(get_users):
            return self.queryset.none()

        return self.queryset.filter(owner__in=get_users())
