from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from sea_saw_base.serializers import BaseSerializer
from ..models import Contact, Account
from .account import AccountMinimalSerializer


class ContactSerializer(BaseSerializer):
    """
    Serializer for the Contact model.
    """

    account = AccountMinimalSerializer(
        required=False,
        allow_null=True,
        read_only=True,
        label=_("Account"),
    )

    account_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Account ID"),
        help_text=_("ID of the account this contact belongs to."),
    )

    class Meta(BaseSerializer.Meta):
        model = Contact
        fields = [
            "id",
            "name",
            "title",
            "email",
            "mobile",
            "phone",
            "account",
            "account_id",
            "owner",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]


class ContactMinimalSerializer(BaseSerializer):
    """
    Minimal Contact serializer for nested display
    """

    class Meta(BaseSerializer.Meta):
        model = Contact
        fields = ["id", "name", "email", "title", "phone", "mobile"]
