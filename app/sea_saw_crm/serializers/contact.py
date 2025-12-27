from django.utils.translation import gettext_lazy as _

from ..models.contact import Contact
from ..models.company import Company

from .base import BaseSerializer
from .company import CompanySerializer


class ContactSerializer(BaseSerializer):
    """
    Serializer for the Contact model.
    - 复用 BaseSerializer 的 owner/created_by/updated_by
    - 复用 BaseSerializer 的 assign_direct_relation
    - company 为只读展示，写入时从 initial_data 中解析
    """

    company = CompanySerializer(
        fields={"pk", "company_name", "address"},
        required=False,
        allow_null=True,
        read_only=True,
        label=_("Company"),
    )

    class Meta(BaseSerializer.Meta):
        model = Contact
        fields = ["id", "name", "title", "email", "mobile", "phone", "company"]

    # -----------------------------------------------------
    # CREATE
    # -----------------------------------------------------
    def create(self, validated_data):
        # 先移除 company，因为 company 是只读字段，由 assign_direct_relation 处理
        validated_data.pop("company", None)

        instance = super().create(validated_data)

        # 使用 BaseSerializer 提供的通用关系分配方法
        self.assign_direct_relation(instance, "company", Company)

        return instance

    # -----------------------------------------------------
    # UPDATE
    # -----------------------------------------------------
    def update(self, instance, validated_data):
        validated_data.pop("company", None)

        instance = super().update(instance, validated_data)

        self.assign_direct_relation(instance, "company", Company)

        return instance
