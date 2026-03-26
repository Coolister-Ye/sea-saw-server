"""Filters for OutboundOrder ViewSet."""

from django_filters import rest_framework as filters
from sea_saw_warehouse.models import OutboundOrder


class OutboundOrderFilter(filters.FilterSet):
    status = filters.CharFilter(field_name="status", lookup_expr="exact")
    pipeline = filters.NumberFilter(field_name="pipeline_id")
    outbound_date_after = filters.DateFilter(field_name="outbound_date", lookup_expr="gte")
    outbound_date_before = filters.DateFilter(field_name="outbound_date", lookup_expr="lte")
    eta_after = filters.DateFilter(field_name="eta", lookup_expr="gte")
    eta_before = filters.DateFilter(field_name="eta", lookup_expr="lte")

    class Meta:
        model = OutboundOrder
        fields = {
            "status": ["exact"],
            "destination_port": ["exact", "icontains"],
            "logistics_provider": ["exact", "icontains"],
            "container_no": ["exact", "icontains"],
        }
