from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter, SearchFilter

from ..models import Company
from ..serializers import CompanySerializer
from ..permissions import CompanyAdminPermission, CompanySalePermission


class CompanyViewSet(ModelViewSet):
    """View set for Company model"""

    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [
        IsAuthenticated,
        CompanyAdminPermission | CompanySalePermission,
    ]

    filter_backends = (OrderingFilter, SearchFilter)
    search_fields = ["^company_name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        role_type = getattr(user.role, "role_type", None)

        # Filter out soft-deleted records
        base_queryset = self.queryset.filter(deleted__isnull=True)

        # ADMIN 可以查看所有
        if role_type == "ADMIN":
            return base_queryset

        # SALE: 只显示可见的联系人
        get_users = getattr(user, "get_all_visible_users", None)
        if not callable(get_users):
            return base_queryset.none()

        return base_queryset.filter(owner__in=get_users())
