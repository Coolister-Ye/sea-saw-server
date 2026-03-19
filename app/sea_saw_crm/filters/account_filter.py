from django_filters import rest_framework as filters

from sea_saw_base.filtersets import BaseFilter, DateTimeAwareFilter
from ..models import Account


class AccountFilter(BaseFilter):
    roles = filters.ChoiceFilter(
        choices=[
            ("customer", "Customer"),
            ("supplier", "Supplier"),
            ("prospect", "Prospect"),
        ],
        method="filter_by_role",
        label="Role",
    )

    def filter_by_role(self, queryset, name, value):
        if value == "customer":
            return queryset.filter(orders__isnull=False).distinct()
        elif value == "supplier":
            return queryset.filter(purchase_orders__isnull=False).distinct()
        elif value == "prospect":
            return queryset.filter(orders__isnull=True, purchase_orders__isnull=True)
        return queryset

    filter_fields = {
        "account_name": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "email": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "mobile": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "phone": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "address": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "industry": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "created_at": {
            "filter_type": DateTimeAwareFilter,
            "lookup_expr": ["__all__"],
        },
        "updated_at": {
            "filter_type": DateTimeAwareFilter,
            "lookup_expr": ["__all__"],
        },
    }

    class Meta:
        model = Account
        fields = []
