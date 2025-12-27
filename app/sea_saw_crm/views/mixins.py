from django.db.models import ManyToOneRel, Prefetch


class RoleFilterMixin:
    """
    A Mixin that provides common functionality for performing create, update,
    and customizing the queryset for the viewset.
    """

    def get_queryset(self):
        """
        Customize the queryset based on the user's permissions and visibility.
        """
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_anonymous:
            return queryset.none()  # No records for anonymous users
        if user.is_superuser or user.is_staff:
            return queryset.all()  # Admins can see all records
        return queryset.filter(owner__in=user.get_all_visible_users())  # Filter by visible users


class DjangoFilterMixin:
    """
    A Mixin that provide nested filter with filters.DjangoFilterBackend.
    The original function dosen't filter unmatched records inside a OneToManyField,
    as it filter based on foreginKey fields to identify the parent records.
    """

    def get_queryset(self):
        """Retrieve and filter the queryset based on the provided query parameters."""
        queryset = super().get_queryset()  # Start with the base queryset
        filter_params = self.request.query_params
        filterset = self.filterset_class(data=filter_params)

        # Filter out the filters that are actually being used
        used_filters = {key: value for key, value in filterset.filters.items() if filter_params.get(key)}

        # Build a nested structure for filters in an optimized way
        used_filters_nested = self.build_nested_filters(used_filters, filter_params)
        model_mapping = self.get_model_mapping()  # Get related model mappings for prefetch

        # Generate prefetch queries and apply filters
        prefetchs, filters = self.make_prefetch(used_filters_nested, model_mapping)
        queryset = self.apply_prefetch(queryset, prefetchs, filters)

        return queryset

    def get_model_mapping(self):
        """Dynamically map related fields in the model for prefetching."""
        model_mapping = {}

        def traverse_model(model):
            """Recursively inspect the model's fields and identify related models."""
            for field in getattr(model, '_meta').get_fields():
                if isinstance(field, ManyToOneRel):
                    related_model_name = field.related_name
                    if related_model_name not in model_mapping:
                        model_mapping[related_model_name] = field.related_model
                        traverse_model(field.related_model)  # Traverse recursively on related models

        traverse_model(self.queryset.model)
        return model_mapping

    def build_nested_filters(self, used_filters, filter_params):
        """Construct a nested filter structure from the filters and their parameters."""
        used_filters_nested = {}

        for key, value in used_filters.items():
            field_name = value.field_name
            lookup_expr = value.lookup_expr

            # Determine the lookup expression and build the lookup field
            lookup_field = f"{field_name}__{lookup_expr}" if lookup_expr != "exact" else field_name

            lookup_value = filter_params.get(lookup_field)  # Fetch the filter value

            field_path = field_name.split("__")  # Split field name to determine if it's nested

            if len(field_path) > 1:
                # Handle nested structures by traversing the path
                nested = used_filters_nested
                for part in field_path[:-1]:  # Traverse all but the last part
                    nested = nested.setdefault(part, {})

                _lookup_expr = field_path[-1] + (f"__{lookup_expr}" if lookup_expr != "exact" else "")
                nested[_lookup_expr] = lookup_value
            else:
                # For non-nested fields, assign directly to the dictionary
                used_filters_nested[field_name] = lookup_value

        return used_filters_nested

    def make_prefetch(self, filter_nested, model_mapping):
        """Generate prefetch queries based on the nested filters."""
        prefetch_queries, filters_queries = {}, {}

        for key, value in filter_nested.items():
            if isinstance(value, dict):  # If the value is a nested dictionary, recurse
                child_prefetch, child_filters = self.make_prefetch(value, model_mapping)
                if key in model_mapping:
                    model_class = model_mapping.get(key)
                    prefetch_qs = model_class.objects.all()

                    # Apply prefetch and filter for each child
                    for child_key, child_qs in child_prefetch.items():
                        prefetch_qs = prefetch_qs.prefetch_related(Prefetch(child_key, queryset=child_qs))

                    for child_key, child_filter in child_filters.items():
                        prefetch_qs = prefetch_qs.filter(**{child_key: child_filter})

                    prefetch_queries[key] = prefetch_qs
            else:
                filters_queries[key] = value  # For non-nested fields, return as filter queries

        return prefetch_queries, filters_queries

    def apply_prefetch(self, queryset, prefetchs, filters):
        """Apply prefetch queries and filters to the queryset."""
        for key, prefetch in prefetchs.items():
            queryset = queryset.prefetch_related(Prefetch(key, queryset=prefetch))

        for key, filter in filters.items():
            queryset = queryset.filter(**{key: filter})

        return queryset
