from django.contrib import admin
from safedelete.admin import SafeDeleteAdmin, highlight_deleted

from ..models import Account


@admin.register(Account)
class AccountAdmin(SafeDeleteAdmin):
    """
    Admin config for unified Account model.
    Includes soft delete support, searching, filters, and clean layout.
    """

    list_display = (
        highlight_deleted,
        "id",
        "account_name",
        "email",
        "mobile",
        "phone",
        "address",
        "get_roles",
        "created_at",
    ) + SafeDeleteAdmin.list_display

    search_fields = (
        "account_name",
        "email",
        "mobile",
        "phone",
        "address",
        "industry",
    )

    list_filter = ("industry", "created_at", "updated_at", "deleted")

    ordering = ("account_name",)

    field_to_highlight = "account_name"

    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "get_roles",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "account_name",
                    "email",
                    "mobile",
                    "phone",
                    "address",
                )
            },
        ),
        (
            "Extended Info",
            {
                "fields": ("website", "industry", "description"),
                "classes": ("collapse",),
            },
        ),
        (
            "System Info",
            {
                "fields": (
                    "owner",
                    "created_by",
                    "updated_by",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Roles")
    def get_roles(self, obj):
        """Display computed roles in admin list."""
        return ", ".join(obj.roles) if obj.roles else "-"
