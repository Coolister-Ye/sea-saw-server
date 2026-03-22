from django.contrib import admin
from safedelete.admin import SafeDeleteAdmin, highlight_deleted

from ..models import BankAccount


@admin.register(BankAccount)
class BankAccountAdmin(SafeDeleteAdmin):
    list_display = (
        highlight_deleted,
        "id",
        "account",
        "bank_name",
        "account_number",
        "account_holder",
        "currency",
        "is_primary",
        "created_at",
    ) + SafeDeleteAdmin.list_display

    search_fields = ("bank_name", "account_number", "account_holder", "account__account_name")

    list_filter = ("currency", "is_primary", "created_at", "deleted")

    ordering = ("-is_primary", "bank_name")

    field_to_highlight = "bank_name"

    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
