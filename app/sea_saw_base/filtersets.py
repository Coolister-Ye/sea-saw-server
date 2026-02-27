from django_filters import Filter
from django_filters.fields import DateRangeWidget, RangeField
from django.utils.dateparse import parse_date
from datetime import datetime, time
from django_filters import rest_framework as filters


class DateTimeAwareFilter(Filter):
    """
    A generic date filter that supports all lookup expressions.
    Converts date strings to datetime objects internally.
    """

    def filter(self, qs, value):
        if value is None or value == "":
            return qs

        lookup = self.lookup_expr or "exact"
        field_name = self.field_name

        # Single value (non-range)
        if lookup != "range":
            # Convert string to datetime if needed
            if isinstance(value, str):
                parsed = parse_date(value)
                if not parsed:
                    return qs.none()
                # For exact match, convert to full-day range
                if lookup == "exact":
                    start = datetime.combine(parsed, time.min)
                    end = datetime.combine(parsed, time.max)
                    return qs.filter(**{f"{field_name}__range": (start, end)})
                else:
                    value = datetime.combine(parsed, time.min)

            return qs.filter(**{f"{field_name}__{lookup}": value})

        # Range value: should be a tuple/list or dict
        elif lookup == "range":
            start, end = None, None
            if isinstance(value, (list, tuple)) and len(value) == 2:
                start = parse_date(value[0]) if isinstance(value[0], str) else value[0]
                end = parse_date(value[1]) if isinstance(value[1], str) else value[1]
            elif isinstance(value, dict):
                start = (
                    parse_date(value.get("start"))
                    if isinstance(value.get("start"), str)
                    else value.get("start")
                )
                end = (
                    parse_date(value.get("end"))
                    if isinstance(value.get("end"), str)
                    else value.get("end")
                )

            if start:
                start = datetime.combine(start, time.min)
            if end:
                end = datetime.combine(end, time.max)

            if start and end:
                return qs.filter(**{f"{field_name}__range": (start, end)})
            elif start:
                return qs.filter(**{f"{field_name}__gte": start})
            elif end:
                return qs.filter(**{f"{field_name}__lte": end})
            else:
                return qs

        return qs


class BaseFilter(filters.FilterSet):
    """
    Base filter with dynamic filter generation support.
    Subclasses define `filter_fields` dict to specify which fields and
    lookup expressions to expose as query parameters.
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

                filter_name = f"{field}__{expr}"

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
