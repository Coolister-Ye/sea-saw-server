from django.utils.translation import gettext_lazy as _

from ..models.contract import Contract
from ..models.contact import Contact

from .base import BaseSerializer
from .contact import ContactSerializer


class ContractSerializer(BaseSerializer):
    """
    Contract serializer for admin and sales users.
    - 使用 BaseSerializer 的 assign_direct_relation 来处理 contact 关系
    - orders 设置为只读（一般合同不允许直接编辑订单）
    """

    contact = ContactSerializer(
        fields={
            "pk",
            "full_name",
            "title",
            "email",
            "mobile",
            "phone",
            "company",
        },
        required=True,
        allow_null=False,
        label=_("Contact"),
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
            "orders",
        ]

    # -----------------------------------------------------
    # CREATE
    # -----------------------------------------------------
    def create(self, validated_data):
        validated_data.pop("contact", None)

        instance = super().create(validated_data)

        # 使用 BaseSerializer 的通用关系方法
        self.assign_direct_relation(instance, "contact", Contact)

        return instance

    # -----------------------------------------------------
    # UPDATE
    # -----------------------------------------------------
    def update(self, instance, validated_data):
        validated_data.pop("contact", None)

        instance = super().update(instance, validated_data)

        self.assign_direct_relation(instance, "contact", Contact)

        return instance
