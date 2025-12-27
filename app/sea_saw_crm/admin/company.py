from django.contrib import admin
from safedelete.admin import SafeDeleteAdmin, highlight_deleted

from ..models import Company


@admin.register(Company)
class CompanyAdmin(SafeDeleteAdmin):
    """
    Admin config for Company model.
    Includes soft delete support, searching, filters, and clean layout.
    """

    list_display = (
        highlight_deleted,
        "id",
        "company_name",
        "email",
        "mobile",
        "phone",
        "address",
        "created_at",
    ) + SafeDeleteAdmin.list_display

    search_fields = ("company_name", "email", "mobile", "phone", "address")

    list_filter = ("created_at", "updated_at", "deleted")

    ordering = ("company_name",)

    field_to_highlight = "company_name"

    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
