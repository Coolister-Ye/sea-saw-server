from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.serializers import ListSerializer

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class BaseSerializer(WritableNestedModelSerializer):
    """
    Base Serializer for all models in the system.
    Provides:
    - owner / created_by / updated_by
    - nested serializer context forwarding
    - field filtering via `fields=[...]`
    - safe nested delete/update handling
    """

    # --------------------------
    # Common system fields
    # --------------------------
    owner = serializers.CharField(
        source="owner.username",
        read_only=True,
        allow_null=True,
        label=_("Owner"),
    )
    created_by = serializers.CharField(
        source="created_by.username",
        read_only=True,
        allow_null=True,
        label=_("Created By"),
    )
    updated_by = serializers.CharField(
        source="owner.username",
        read_only=True,
        allow_null=True,
        label=_("Updated By"),
    )
    created_at = serializers.DateTimeField(
        read_only=True,
        format=DATETIME_FORMAT,
        allow_null=True,
        label=_("Created At"),
    )
    updated_at = serializers.DateTimeField(
        read_only=True,
        format=DATETIME_FORMAT,
        allow_null=True,
        label=_("Updated At"),
    )

    class Meta:
        abstract = True
        fields = ["id", "owner", "created_by", "updated_by", "created_at", "updated_at"]

    # --------------------------
    # Utility methods
    # --------------------------
    def get_context_user(self):
        """Retrieve user from request context."""
        request = self.context.get("request")
        return getattr(request, "user", None)

    # --------------------------
    # Nested serializer handling
    # --------------------------
    def _clone_nested(self, field):
        """Clone nested field with forwarded context."""
        field_class = field.__class__
        kwargs = getattr(field, "_kwargs", {})
        return field_class(context=self.context, **kwargs)

    def forward_context(self):
        """
        Forward context to nested BaseSerializer fields (single or list).
        Ensures nested objects can access the request/user.
        """
        for name, field in self.fields.items():

            # Case: many=True (ListSerializer)
            if isinstance(field, ListSerializer) and isinstance(
                field.child, BaseSerializer
            ):
                field.child = self._clone_nested(field.child)

            # Case: single nested serializer
            elif isinstance(field, BaseSerializer):
                self.fields[name] = self._clone_nested(field)

    # --------------------------
    # Field filtering
    # --------------------------
    def _apply_field_filtering(self, include_fields):
        """Remove fields not in `fields=[..]`."""
        allowed = set(include_fields)
        for name in list(self.fields.keys()):
            if name not in allowed:
                self.fields.pop(name)

    # --------------------------
    # Init
    # --------------------------
    def __init__(self, *args, **kwargs):
        fields_to_include = kwargs.pop("fields", None)
        self.display_fields = kwargs.pop("display_fields", [])

        super().__init__(*args, **kwargs)

        # Forward context to nested serializers
        self.forward_context()

        # Apply field filtering
        if fields_to_include:
            self._apply_field_filtering(fields_to_include)

    # --------------------------
    # Assign direct relation utility
    # --------------------------
    def assign_direct_relation(
        self, instance, relation_name, model_class, relation_data=None
    ):
        """
        Generic method to assign fk relations (contact, owner, etc.).
        Acceptable input:
            - pk
            - {"pk": 1}
            - model instance
            - filter dict (e.g., {"email": "..."} )
        """
        data = (
            relation_data
            or self.initial_data.get(relation_name)
            or self.validated_data.get(relation_name)
        )

        if data is None:
            setattr(instance, relation_name, None)
            instance.save(update_fields=[relation_name])
            return instance

        try:
            # If instance already passed in
            if isinstance(data, model_class):
                relation_instance = data

            # Case: {"pk": ...}
            elif isinstance(data, dict) and "pk" in data:
                relation_instance = model_class.objects.get(pk=data["pk"])

            # Case: {"id": ...}
            elif isinstance(data, dict) and "id" in data:
                relation_instance = model_class.objects.get(pk=data["id"])

            # Case: pk directly
            elif isinstance(data, (str, int)):
                relation_instance = model_class.objects.get(pk=data)

            # Case: filter dict
            elif isinstance(data, dict):
                relation_instance = model_class.objects.get(**data)

            else:
                raise serializers.ValidationError(
                    {
                        relation_name: f"Invalid data for assigning {model_class.__name__}."
                    }
                )

            # Update relation only if needed
            if getattr(instance, relation_name) != relation_instance:
                setattr(instance, relation_name, relation_instance)
                instance.save(update_fields=[relation_name])

        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                {relation_name: f"{model_class.__name__} does not exist."}
            )

        return instance

    # --------------------------
    # Create
    # --------------------------
    def create(self, validated_data):
        user = self.get_context_user()
        if user:
            validated_data["_user"] = user
        return super().create(validated_data)

    # --------------------------
    # Update
    # --------------------------
    def update(self, instance, validated_data):
        user = self.get_context_user()
        if user:
            validated_data["_user"] = user
        return super().update(instance, validated_data)
