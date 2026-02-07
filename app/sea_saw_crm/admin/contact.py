from django.contrib import admin
from safedelete.admin import SafeDeleteAdmin, highlight_deleted

from ..models import Contact


@admin.register(Contact)
class ContactAdmin(SafeDeleteAdmin):
    """
    Admin configuration for Contact model.
    Includes SafeDelete support, search, filters, and clean list layout.
    """

    list_display = (
        highlight_deleted,
        "id",
        "name",
        "title",
        "email",
        "mobile",
        "phone",
        "company_name",
        "created_at",
    ) + SafeDeleteAdmin.list_display

    search_fields = ("name", "email", "mobile", "phone", "company__company_name")

    list_filter = ("account", "created_at", "updated_at", "deleted")

    ordering = ("name",)

    field_to_highlight = "name"

    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")

    def company_name(self, obj):
        if obj.company:
            return obj.company.company_name
        return "-"

    company_name.short_description = "Company"
