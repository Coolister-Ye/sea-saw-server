from django_filters import rest_framework as filters

from sea_saw_base.filtersets import BaseFilter, DateTimeAwareFilter
from .models import Account, Contact


class AccountFilter(BaseFilter):
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


class ContactFilter(BaseFilter):
    filter_fields = {
        "name": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "title": {
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
        model = Contact
        fields = []


# SupplierFilter removed - Supplier model does not exist in sea_saw_crm
# If needed, implement in the appropriate app where Supplier model is defined
