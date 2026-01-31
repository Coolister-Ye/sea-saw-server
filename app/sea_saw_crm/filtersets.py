from django_filters import Filter
from django_filters.fields import DateRangeWidget, RangeField
from django.utils.dateparse import parse_date
from datetime import datetime, time


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
