"""
Django Admin for Supplier model
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Admin for Supplier"""

    list_display = [
        "supplier_code",
        "name",
        "company",
        "contact_person",
        "email",
        "phone",
        "rating",
        "is_active",
        "is_approved",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "is_approved",
        "rating",
        "country",
        "created_at",
    ]
    search_fields = [
        "supplier_code",
        "name",
        "company__name",
        "contact_person",
        "email",
        "phone",
        "mobile",
    ]
    readonly_fields = ["supplier_code", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "supplier_code",
                    "name",
                    "company",
                )
            },
        ),
        (
            _("Contact Information"),
            {
                "fields": (
                    "contact_person",
                    "email",
                    "phone",
                    "mobile",
                    "fax",
                )
            },
        ),
        (
            _("Address Information"),
            {
                "fields": (
                    "address",
                    "country",
                    "state",
                    "city",
                    "postal_code",
                )
            },
        ),
        (
            _("Business Information"),
            {
                "fields": (
                    "tax_id",
                    "website",
                    "payment_terms",
                    "currency",
                    "credit_limit",
                )
            },
        ),
        (
            _("Rating & Status"),
            {
                "fields": (
                    "rating",
                    "is_active",
                    "is_approved",
                )
            },
        ),
        (
            _("Additional Information"),
            {
                "fields": (
                    "remark",
                    "created_by",
                    "updated_by",
                    "owner",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
