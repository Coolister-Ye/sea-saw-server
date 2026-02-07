from rest_framework import serializers
from sea_saw_base.serializers import BaseSerializer
from ..models import Account, Contact


class AccountMinimalSerializer(BaseSerializer):
    """
    Minimal Account serializer for nested display.
    Used in Order, PurchaseOrder, Contact serializers.
    """

    roles = serializers.SerializerMethodField(read_only=True)

    class Meta(BaseSerializer.Meta):
        model = Account
        fields = ["id", "account_name", "address", "roles"]

    def get_roles(self, obj) -> list:
        """Return computed roles based on business relationships."""
        return obj.roles


# Import ContactMinimalSerializer after AccountMinimalSerializer is defined
# This avoids circular import issues
from .contact import ContactMinimalSerializer


class AccountSerializer(BaseSerializer):
    """
    Account serializer with computed roles field and nested contacts.
    Roles are derived from business relationships:
    - CUSTOMER: Has sales orders
    - SUPPLIER: Has purchase orders
    - PROSPECT: No relationships yet
    """

    roles = serializers.SerializerMethodField(read_only=True)
    # Use nested serializer directly instead of SerializerMethodField
    # This allows OPTIONS to return detailed field metadata for frontend rendering
    contacts = ContactMinimalSerializer(
        many=True,
        read_only=True
    )
    contact_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Contact.objects.all(),
        source='contacts',
        write_only=True,
        required=False,
        help_text="List of contact IDs to associate with this account"
    )

    class Meta(BaseSerializer.Meta):
        model = Account
        fields = [
            "id",
            "owner",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "roles",
            "contacts",
            "contact_ids",
            "account_name",
            "email",
            "mobile",
            "phone",
            "address",
            "website",
            "industry",
            "description",
        ]

    def get_roles(self, obj) -> list:
        """Return computed roles based on business relationships."""
        return obj.roles
