from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from sea_saw_base.serializers import BaseSerializer
from ..models import BankAccount
from .account import AccountMinimalSerializer


class BankAccountMinimalSerializer(BaseSerializer):
    """
    Minimal BankAccount serializer for nested display in Account.
    """

    account_holder = AccountMinimalSerializer(
        required=False,
        allow_null=True,
        read_only=True,
        label=_("Account Holder"),
    )

    class Meta(BaseSerializer.Meta):
        model = BankAccount
        fields = [
            "id",
            "account_holder",
            "bank_name",
            "account_number",
            "currency",
            "swift_code",
            "branch",
            "bank_address",
            "is_primary",
        ]


class BankAccountSerializer(BaseSerializer):
    """
    Serializer for BankAccount model.
    """

    account_holder = AccountMinimalSerializer(
        required=False,
        allow_null=True,
        read_only=True,
        label=_("Account Holder"),
    )

    account_holder_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Account ID"),
        help_text=_("ID of the account this bank account belongs to."),
    )

    class Meta(BaseSerializer.Meta):
        model = BankAccount
        fields = [
            "id",
            "account_holder",
            "account_holder_id",
            "bank_name",
            "account_number",
            "currency",
            "swift_code",
            "branch",
            "bank_address",
            "is_primary",
            "remark",
            "owner",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]
