from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from ..models.contact import Contact
from ..models.company import Company

from .base import BaseSerializer
from .company import CompanySerializer


class ContactSerializer(BaseSerializer):
    """
    Serializer for the Contact model with optimized field order.
    - Excludes created_by and updated_by fields
    - company is displayed as nested object but accepts company_id on write
    """

    company = CompanySerializer(read_only=True, label=_("Company"))
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source="company",
        required=False,
        allow_null=True,
        write_only=True,
        label=_("Company ID"),
    )

    class Meta(BaseSerializer.Meta):
        model = Contact
        fields = [
            "id",
            "name",
            "title",
            "company",
            "company_id",
            "email",
            "mobile",
            "phone",
            "owner",
            "created_at",
            "updated_at",
        ]
