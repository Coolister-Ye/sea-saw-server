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


class BaseMetadata(SimpleMetadata):
    """
    Base DRF Metadata
    - serializer schema (POST / PUT)
    - filter operations
    - nested serializer support
    """

    LOOKUP_TYPES = [
        "exact",
        "iexact",
        "contains",
        "icontains",
        "in",
        "gt",
        "gte",
        "lt",
        "lte",
        "startswith",
        "istartswith",
        "endswith",
        "iendswith",
        "range",
        "isnull",
        "date",
        "year",
        "month",
        "day",
        "regex",
        "iregex",
    ]

    lookup_pattern = re.compile(r"__(?:%s)$" % "|".join(LOOKUP_TYPES))

    def __init__(self):
        super().__init__()
        self.filter_info = {}

    # =====================================================
    # Entry
    # =====================================================
    def determine_metadata(self, request, view):
        metadata = super().determine_metadata(request, view)
        metadata["actions"] = self.determine_actions(request, view)
        return metadata

    # =====================================================
    # CRUD schema
    # =====================================================
    def determine_actions(self, request, view):
        actions = {}

        for method in {"POST", "PUT"} & set(view.allowed_methods):
            view.request = clone_request(request, method)
            try:
                view.check_permissions(view.request)
                if method == "PUT":
                    view.get_object()
            except (exceptions.APIException, PermissionDenied, Http404):
                continue
            else:
                serializer = view.get_serializer()
                self.filter_info = self.get_filters_info(view)
                actions[method] = self.get_serializer_info(serializer)
            finally:
                view.request = request

        return actions

    # =====================================================
    # Filters
    # =====================================================
    def get_base_field_name(self, field_name: str) -> str:
        field_name = self.lookup_pattern.sub("", field_name)
        return field_name.replace("__", ".")

    def get_filters_info(self, view):
        filters_info = defaultdict(lambda: {"operations": []})

        for backend in getattr(view, "filter_backends", []):
            if not issubclass(backend, DjangoFilterBackend):
                continue

            filterset_class = getattr(view, "filterset_class", None)
            if not filterset_class:
                continue

            filterset = filterset_class()
            for field_name, f in filterset.filters.items():
                base = self.get_base_field_name(field_name)
                filters_info[base]["operations"].append(f.lookup_expr)

        return dict(filters_info)

    # =====================================================
    # Serializer schema
    # =====================================================
    def get_serializer_info(self, serializer):
        if hasattr(serializer, "child"):
            serializer = serializer.child

        ret = {}

        # Retrieve model field info if available
        model = getattr(serializer.Meta, "model", None)
        model_field_info = {}
        if model:
            content_type = ContentType.objects.get_for_model(model)
            model_field_info = {
                field.field_name: field.extra_info
                for field in Field.objects.filter(content_type=content_type)
            }

        for field_name, field in serializer.fields.items():
            if isinstance(field, serializers.HiddenField):
                continue

            # Base field info
            info = self.get_field_info(field)

            # Filter info
            filter_info = self.filter_info.get(field_name, {})
            info.update(filter_info)

            # Model field info
            field_info = model_field_info.get(field_name, {})
            info.update(field_info)

            ret[field_name] = info

        return ret

    def get_field_info(self, field):
        """
        Given an instance of a serializer field, return a dictionary
        of metadata about it.
        """
        field_info = {
            "type": self.label_lookup[field],
            "required": getattr(field, "required", False),
        }

        attrs = [
            "read_only",
            "label",
            "help_text",
            "min_length",
            "max_length",
            "min_value",
            "max_value",
            "max_digits",
            "decimal_places",
        ]

        for attr in attrs:
            value = getattr(field, attr, None)
            if value is not None and value != "":
                field_info[attr] = force_str(value, strings_only=True)

        if getattr(field, "child", None):
            field_info["child"] = self.get_field_info(field.child)
        elif getattr(field, "fields", None):
            field_info["children"] = self.get_serializer_info(field)

        if (
            not field_info.get("read_only")
            and not isinstance(
                field, (serializers.RelatedField, serializers.ManyRelatedField)
            )
            and hasattr(field, "choices")
        ):
            field_info["choices"] = [
                {
                    "value": choice_value,
                    "label": force_str(choice_name, strings_only=True),
                }
                for choice_value, choice_name in field.choices.items()
            ]

        return field_info
