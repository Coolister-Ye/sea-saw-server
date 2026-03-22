from django_filters import rest_framework as filters

from sea_saw_base.filtersets import BaseFilter, DateTimeAwareFilter
from ..models import BankAccount


class BankAccountFilter(BaseFilter):
    account_id = filters.NumberFilter(field_name="account", lookup_expr="exact")

    filter_fields = {
        "bank_name": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "account_number": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "account_holder": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "currency": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["exact"],
        },
        "is_primary": {
            "filter_type": filters.BooleanFilter,
            "lookup_expr": ["exact"],
        },
        "account": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in"],
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
        model = BankAccount
        fields = []
