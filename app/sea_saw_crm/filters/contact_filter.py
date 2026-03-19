from django_filters import rest_framework as filters

from sea_saw_base.filtersets import BaseFilter, DateTimeAwareFilter
from ..models import Contact


class ContactFilter(BaseFilter):
    # Exact-match filter for FK ID sent by the frontend AccountSelector (account_id=2)
    account_id = filters.NumberFilter(field_name="account", lookup_expr="exact")

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
