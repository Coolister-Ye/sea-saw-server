from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from ..models.contract import Contract
from ..models.contact import Contact

from .base import BaseSerializer
from .contact import ContactSerializer


class ContractSerializer(BaseSerializer):
    """
    Contract serializer for admin and sales users.
    - contact 显示为嵌套对象，写入时使用 contact_id
    - orders 设置为只读（一般合同不允许直接编辑订单）
    """

    contact = ContactSerializer(
        fields={
            "pk",
            "name",
            "title",
            "email",
            "mobile",
            "phone",
            "company",
        },
        read_only=True,
        label=_("Contact"),
    )
    contact_id = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        source="contact",
        required=True,
        allow_null=False,
        write_only=True,
        label=_("Contact ID"),
    )

    class Meta(BaseSerializer.Meta):
        model = Contract
        fields = [
            "pk",
            "contract_code",
            "contract_date",
            "stage",
            "owner",
            "created_at",
            "updated_at",
            "contact",
            "contact_id",
            "orders",
        ]
