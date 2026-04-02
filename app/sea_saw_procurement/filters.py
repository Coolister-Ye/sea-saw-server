"""
Purchase Order Filters for sea_saw_procurement app
"""
from django_filters import rest_framework as filters

from sea_saw_base.filtersets import BaseFilter, DateTimeAwareFilter
from .models import PurchaseOrder


class PurchaseOrderFilter(BaseFilter):
    """
    Filter for PurchaseOrder model.

    Supports filtering by:
    - Purchase fields: purchase_code, purchase_date, status
    - Supplier fields: supplier, contact
    - Logistics: etd, loading_port, destination_port, shipment_term, inco_terms
    - Finance: currency, deposit, balance, total_amount
    - Audit fields: owner, created_by, updated_by, created_at, updated_at
    - Text fields: comment
    """

    buyer_id = filters.NumberFilter(field_name="buyer", lookup_expr="exact")
    supplier_id = filters.NumberFilter(field_name="supplier", lookup_expr="exact")
    shipper_id = filters.NumberFilter(field_name="shipper", lookup_expr="exact")
    contact_id = filters.NumberFilter(field_name="contact", lookup_expr="exact")
    bank_account_id = filters.NumberFilter(field_name="bank_account", lookup_expr="exact")

    filter_fields = {
        "purchase_code": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["__all__"],
        },
        "purchase_date": {
            "filter_type": filters.DateFilter,
            "lookup_expr": ["__all__"],
        },
        "status": {
            "filter_type": filters.CharFilter,
            "lookup_expr": ["iexact", "in", "isnull"],
        },
        "buyer": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },
        "supplier": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },
        "shipper": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },
        "contact": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },
        "bank_account": {
            "filter_type": filters.BaseInFilter,
            "lookup_expr": ["in", "isnull"],
        },
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
        model = PurchaseOrder
        fields = []
