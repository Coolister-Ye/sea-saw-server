import re
from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.encoding import force_str
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import exceptions, serializers
from rest_framework.metadata import SimpleMetadata
from rest_framework.request import clone_request

from sea_saw_crm.models import Field


class CustomMetadata(SimpleMetadata):
    LOOKUP_TYPES = [
        "exact",
        "iexact",
        "contains",
        "icontains",
        "in",
        "gt",
        "lt",
        "gte",
        "lte",
        "startswith",
        "istartswith",
        "endswith",
        "iendswith",
        "range",
        "date",
        "year",
        "month",
        "day",
        "week_day",
        "isnull",
        "search",
        "regex",
        "iregex",
        "hour",
        "minute",
        "second",
        "time",
    ]

    # Regex pattern that matches any of the lookups at the end of the string
    lookup_pattern = r'__(?:' + '|'.join(LOOKUP_TYPES) + r')$'

    def __init__(self):
        super().__init__()
        self.filter_info = {}

    def determine_actions(self, request, view):
        """
        For generic class based views we return information about
        the fields that are accepted for 'PUT' and 'POST' methods.
        """
        actions = {}
        for method in {'PUT', 'POST'} & set(view.allowed_methods):
            view.request = clone_request(request, method)
            try:
                # Test global permissions
                if hasattr(view, 'check_permissions'):
                    view.check_permissions(view.request)
                # Test object permissions
                if method == 'PUT' and hasattr(view, 'get_object'):
                    view.get_object()
            except (exceptions.APIException, PermissionDenied, Http404):
                pass
            else:
                # If user has appropriate permissions for the view, include
                # appropriate metadata about the fields that should be supplied.
                serializer = view.get_serializer()
                self.filter_info = self.get_filters_info(view)
                actions[method] = self.get_serializer_info(serializer)
            finally:
                view.request = request

        return actions

    def get_base_field_name(self, field_name):
        # Remove lookup pattern at the end of field name
        field_name = re.sub(self.lookup_pattern, '', field_name)
        # Convert Django lookup pattern to chain pattern
        return re.sub(r'__', '.', field_name)

    def get_filters_info(self, view):
        filters_info = defaultdict(lambda: {"operations": []})
        filter_backends = getattr(view, 'filter_backends', [])

        # Loop through all filter backends
        for backend in filter_backends:
            if issubclass(backend, DjangoFilterBackend):
                filterset_class = getattr(view, 'filterset_class', None)
                if filterset_class:
                    filterset = filterset_class()

                    # Iterate through the filter fields and populate filters_info
                    for field_name, field_object in filterset.filters.items():
                        base_field_name = self.get_base_field_name(field_name)
                        filters_info[base_field_name]["operations"].append(field_object.lookup_expr)

        # Convert defaultdict back to a regular dict before returning
        return dict(filters_info)

    def get_serializer_info(self, serializer, parent=None):
        """
        Given an instance of a serializer, return a dictionary of metadata
        about its fields, including extra field info from the associated model.
        """
        # Handle ListSerializer by examining the child serializer
        if hasattr(serializer, 'child'):
            serializer = serializer.child

        # Initialize the return data structure
        ret_field_info = {}

        # Retrieve model field info if available
        model = getattr(serializer.Meta, 'model', None)
        if model:
            content_type = ContentType.objects.get_for_model(model)
            model_field_info = {
                field.field_name: {**field.extra_info, **{'field_type': field.field_type}}
                for field in Field.objects.filter(content_type=content_type)
            }
        else:
            model_field_info = {}

        # Iterate over serializer fields and collect metadata
        for field_name, field in serializer.fields.items():
            if isinstance(field, serializers.HiddenField):
                continue

            # Field name now
            field_whole_name = parent + "." + field_name if parent else field_name

            # Basic field info
            field_info = self.get_field_info(field, field_whole_name)

            # Add filter info
            # filter_name = parent + "." + field_name if parent else field_name
            filter_info = self.filter_info.get(field_whole_name, {})
            field_info = {**field_info, **filter_info}

            # Add extra info from the model (if available)
            if extra_info := model_field_info.get(field_name):
                field_info = {**field_info, **extra_info}

            ret_field_info[field_name] = field_info

        return ret_field_info

    def get_field_info(self, field, parent=None):
        """
        Given an instance of a serializer field, return a dictionary
        of metadata about it.
        """
        field_info = {"type": self.label_lookup[field], "required": getattr(field, "required", False)}

        attrs = [
            'read_only',
            'label',
            'help_text',
            'min_length',
            'max_length',
            'min_value',
            'max_value',
            'max_digits',
            'decimal_places',
        ]

        for attr in attrs:
            value = getattr(field, attr, None)
            if value is not None and value != '':
                field_info[attr] = force_str(value, strings_only=True)

        if getattr(field, 'child', None):
            field_info['child'] = self.get_field_info(field.child, parent)
        elif getattr(field, 'fields', None):
            field_info['children'] = self.get_serializer_info(field, parent)

        if (
            not field_info.get('read_only')
            and not isinstance(field, (serializers.RelatedField, serializers.ManyRelatedField))
            and hasattr(field, 'choices')
        ):
            field_info['choices'] = [
                {'value': choice_value, 'label': force_str(choice_name, strings_only=True)}
                for choice_value, choice_name in field.choices.items()
            ]

        return field_info
