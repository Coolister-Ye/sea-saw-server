from django_filters import rest_framework as filters

from sea_saw_base.filtersets import BaseFilter
from sea_saw_auth.models import User


class AdminUserFilter(BaseFilter):
    filter_fields = {
        "username": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "email": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "department": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "is_active": {
            "filter_type": filters.BooleanFilter,
            "lookup_expr": ["exact"],
        },
        "is_staff": {
            "filter_type": filters.BooleanFilter,
            "lookup_expr": ["exact"],
        },
    }

    class Meta:
        model = User
        fields = []
