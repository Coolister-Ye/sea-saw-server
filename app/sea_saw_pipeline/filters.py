"""
Pipeline Filters for sea_saw_pipeline app
"""
from django_filters import rest_framework as filters

from sea_saw_base.filtersets import BaseFilter, DateTimeAwareFilter
from sea_saw_pipeline.models.pipeline import Pipeline


class PipelineFilter(BaseFilter):
    """
    Filter for Pipeline model.

    Supports filtering by:
    - Pipeline fields: pipeline_code, pipeline_type, status, order_date
    - Related entities: account, contact
    - Finance: total_amount, paid_amount
    - Audit fields: owner, created_by, updated_by, created_at, updated_at
    """

    # Exact-match filters for FK IDs sent by the frontend selector
    account_id = filters.NumberFilter(field_name="account", lookup_expr="exact")
    contact_id = filters.NumberFilter(field_name="contact", lookup_expr="exact")

    filter_fields = {
        "pipeline_code": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "pipeline_type": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["iexact", "in", "isnull"],
        },
        "status": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["iexact", "in", "isnull"],
        },
        "order_date": {
            "filter_type": filters.DateFilter,
            "lookup_expr": ["__all__"],
        },

        # Related entities
        "account": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },
        "contact": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },

        # Finance fields
        "total_amount": {
            "filter_type": filters.NumberFilter,
            "lookup_expr": ["__all__"],
        },
        "paid_amount": {
            "filter_type": filters.NumberFilter,
            "lookup_expr": ["__all__"],
        },

        # Audit fields
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
        model = Pipeline
        fields = []
