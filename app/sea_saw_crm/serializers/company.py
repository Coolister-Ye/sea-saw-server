from .base import BaseSerializer

from ..models.company import Company


class CompanySerializer(BaseSerializer):
    """
    Company serializer
    """

    class Meta(BaseSerializer.Meta):
        model = Company
        fields = "__all__"
