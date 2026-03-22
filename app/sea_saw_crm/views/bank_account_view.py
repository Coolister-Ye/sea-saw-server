from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet
from sea_saw_base.metadata import BaseMetadata

from ..models import BankAccount
from ..serializers import BankAccountSerializer
from ..permissions import BankAccountPermission
from ..filters import BankAccountFilter


class BankAccountViewSet(ModelViewSet):
    """
    ViewSet for BankAccount model.

    Supports filtering by account:
    - ?account_id=1  - Bank accounts for a specific account
    - ?is_primary=true  - Only primary bank accounts
    """

    queryset = BankAccount.objects.select_related("account").all()
    serializer_class = BankAccountSerializer
    permission_classes = [BankAccountPermission]
    metadata_class = BaseMetadata

    filter_backends = (OrderingFilter, SearchFilter, filters.DjangoFilterBackend)
    filterset_class = BankAccountFilter
    search_fields = ["^bank_name", "^account_number", "^account_holder"]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset

        if user.is_superuser or user.is_staff:
            return qs

        role_type = getattr(user.role, "role_type", None)

        if role_type == "ADMIN":
            return qs

        get_users = getattr(user, "get_all_visible_users", None)
        if not callable(get_users):
            return qs.none()

        # Visibility follows the parent account's owner
        return qs.filter(account__owner__in=get_users())
