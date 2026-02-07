from rest_framework.viewsets import ModelViewSet
from sea_saw_base.metadata import BaseMetadata

from ..models import Account
from ..serializers import AccountSerializer
from ..permissions import AccountPermission


class AccountViewSet(ModelViewSet):
    """
    ViewSet for unified Account model.

    Supports role filtering via query parameter:
    - ?role=customer  - Accounts with sales orders
    - ?role=supplier  - Accounts with purchase orders
    - ?role=prospect  - Accounts with no business relationships
    """

    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [AccountPermission]
    metadata_class = BaseMetadata

    search_fields = ["^account_name"]

    def get_queryset(self):
        user = self.request.user

        # Start with base queryset
        qs = self.queryset

        # Superusers and staff see all data
        if user.is_superuser or user.is_staff:
            base_qs = qs
        else:
            role_type = getattr(user.role, "role_type", None)

            # Admin sees all
            if role_type == "ADMIN":
                base_qs = qs
            else:
                # Filter by user visibility
                get_users = getattr(user, "get_all_visible_users", None)
                if not callable(get_users):
                    return qs.none()
                base_qs = qs.filter(owner__in=get_users())

        # Apply role filter if provided
        role_filter = self.request.query_params.get("role")
        if role_filter:
            base_qs = self._filter_by_role(base_qs, role_filter)

        return base_qs

    def _filter_by_role(self, queryset, role):
        """
        Filter accounts by their implicit role based on business relationships.

        Args:
            queryset: Base queryset to filter
            role: Role to filter by ('customer', 'supplier', 'prospect')

        Returns:
            Filtered queryset
        """
        role = role.lower()

        if role == "customer":
            # Accounts with at least one sales order
            return queryset.filter(orders__isnull=False).distinct()
        elif role == "supplier":
            # Accounts with at least one purchase order
            return queryset.filter(purchase_orders__isnull=False).distinct()
        elif role == "prospect":
            # Accounts with no business relationships
            return queryset.filter(orders__isnull=True, purchase_orders__isnull=True)

        return queryset
