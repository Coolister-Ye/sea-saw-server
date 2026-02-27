"""
Order Filters for sea_saw_sales app
"""
from django_filters import rest_framework as filters

from sea_saw_base.filtersets import BaseFilter, DateTimeAwareFilter
from .models import Order


class OrderFilter(BaseFilter):
    """
    Filter for Order model with support for various lookup expressions.

    Supports filtering by:
    - Order fields: order_code, order_date, status
    - Customer fields: account, contact
    - Logistics: etd, loading_port, destination_port, shipment_term, inco_terms
    - Finance: currency, deposit, balance, total_amount
    - Audit fields: owner, created_by, updated_by, created_at, updated_at
    - Text fields: comment
    """

    # Exact-match filters for FK IDs sent by the frontend selector (account_id=2, contact_id=3)
    account_id = filters.NumberFilter(field_name="account", lookup_expr="exact")
    contact_id = filters.NumberFilter(field_name="contact", lookup_expr="exact")

    filter_fields = {
        # Order basic fields
        "order_code": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "order_date": {
            "filter_type": filters.DateFilter,
            "lookup_expr": ["__all__"],
        },
        "status": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["iexact", "in", "isnull"],
        },

        # Related entities (ForeignKey)
        "account": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },
        "contact": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },

        # Logistics fields
        "etd": {
            "filter_type": filters.DateFilter,
            "lookup_expr": ["__all__"],
        },
        "loading_port": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "destination_port": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "shipment_term": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["iexact", "in", "isnull"],
        },
        "inco_terms": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["iexact", "in", "isnull"],
        },

        # Finance fields
        "currency": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["iexact", "in", "isnull"],
        },
        "deposit": {
            "filter_type": filters.NumberFilter,
            "lookup_expr": ["__all__"],
        },
        "balance": {
            "filter_type": filters.NumberFilter,
            "lookup_expr": ["__all__"],
        },
        "total_amount": {
            "filter_type": filters.NumberFilter,
            "lookup_expr": ["__all__"],
        },

        # Text field
        "comment": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["icontains", "isnull"],
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
        model = Order
        fields = []
