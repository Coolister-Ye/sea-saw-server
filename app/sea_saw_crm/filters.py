from django_filters import rest_framework as filters

from sea_saw_base.filtersets import DateTimeAwareFilter
from .models import Company, Contact, Supplier


class BaseFilter(filters.FilterSet):
    """
    Base filter with dynamic filter generation support
    """
    filter_mapper = {
        filters.CharFilter: [
            "iexact",
            "icontains",
            "istartswith",
            "iendswith",
            "isnull",
            "iexact_ex",
            "icontains_ex",
            "isnull_ex",
        ],
        filters.NumberFilter: [
            "iexact",
            "gt",
            "gte",
            "lt",
            "lte",
            "isnull",
            "range",
            "iexact_ex",
            "isnull_ex",
        ],
        filters.DateFilter: [
            "iexact",
            "gt",
            "gte",
            "lt",
            "lte",
            "isnull",
            "range",
            "iexact_ex",
            "isnull_ex",
        ],
        DateTimeAwareFilter: [
            "iexact",
            "gt",
            "gte",
            "lt",
            "lte",
            "isnull",
            "range",
            "iexact_ex",
            "isnull_ex",
        ],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        filter_fields = getattr(self, "filter_fields", {})

        for field, options in filter_fields.items():
            filter_type = options.get("filter_type", filters.CharFilter)
            lookup_exprs = options.get("lookup_expr", ["exact"])

            if "__all__" in lookup_exprs:
                lookup_exprs = self.filter_mapper.get(filter_type, [])

            for expr in lookup_exprs:
                is_exclude = expr.endswith("_ex")
                actual_expr = expr.replace("_ex", "")

                filter_name = f"{field}__{expr}" if expr != "iexact" else field

                if actual_expr == "range":
                    if (
                        filter_type == filters.DateFilter
                        or filter_type == DateTimeAwareFilter
                    ):
                        self.filters[filter_name] = filters.DateFromToRangeFilter(
                            field_name=field, lookup_expr=actual_expr
                        )
                    else:
                        self.filters[filter_name] = filters.NumericRangeFilter(
                            field_name=f"{field}__pk", lookup_expr=actual_expr
                        )
                elif actual_expr == "isnull" or actual_expr == "isnull_ex":
                    self.filters[filter_name] = filters.BooleanFilter(
                        field_name=field, lookup_expr=actual_expr, exclude=is_exclude
                    )
                elif filter_type == filters.BaseInFilter:
                    self.filters[filter_name] = filters.BaseInFilter(
                        field_name=field, lookup_expr=actual_expr
                    )
                else:
                    self.filters[filter_name] = filter_type(
                        field_name=field,
                        lookup_expr=actual_expr,
                        exclude=is_exclude,
                    )

    class Meta:
        abstract = True


class CompanyFilter(BaseFilter):
    filter_fields = {
        "company_name": {
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
        model = Company
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


class SupplierFilter(BaseFilter):
    filter_fields = {
        "supplier_name": {
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
        model = Supplier
        fields = []
