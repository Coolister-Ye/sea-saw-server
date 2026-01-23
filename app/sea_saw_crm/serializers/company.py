from .base import BaseSerializer

from ..models.company import Company


class CompanySerializer(BaseSerializer):
    """
    Company serializer with optimized field order for display.
    Excludes created_by and updated_by fields.
    """

    class Meta(BaseSerializer.Meta):
        model = Company
        fields = [
            "id",
            "company_name",
            "email",
            "mobile",
            "phone",
            "address",
            "owner",
            "created_at",
            "updated_at",
        ]
