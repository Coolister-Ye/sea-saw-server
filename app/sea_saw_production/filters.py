"""
Production Order Filters for sea_saw_production app
"""
from django_filters import rest_framework as filters

from sea_saw_base.filtersets import BaseFilter, DateTimeAwareFilter
from .models import ProductionOrder


class ProductionOrderFilter(BaseFilter):
    """
    Filter for ProductionOrder model.

    Supports filtering by:
    - Production fields: production_code, status
    - Related entities: related_order, pipeline
    - Dates: planned_date, start_date, end_date
    - Text fields: remark, comment
    - Audit fields: owner, created_by, updated_by, created_at, updated_at
    """

    # Exact-match filters for FK IDs sent by frontend selectors
    related_order_id = filters.NumberFilter(field_name="related_order", lookup_expr="exact")
    pipeline_id = filters.NumberFilter(field_name="pipeline", lookup_expr="exact")

    filter_fields = {
        "production_code": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "status": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["iexact", "in", "isnull"],
        },
        "related_order": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },
        "pipeline": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },
        "planned_date": {
            "filter_type": filters.DateFilter,
            "lookup_expr": ["__all__"],
        },
        "start_date": {
            "filter_type": filters.DateFilter,
            "lookup_expr": ["__all__"],
        },
        "end_date": {
            "filter_type": filters.DateFilter,
            "lookup_expr": ["__all__"],
        },
        "remark": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["icontains", "isnull"],
        },
        "comment": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["icontains", "isnull"],
        },
        "owner": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },
        "created_by": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },
        "updated_by": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
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
        model = ProductionOrder
        fields = []
