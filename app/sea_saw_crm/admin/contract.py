from django.contrib import admin
from safedelete.admin import SafeDeleteAdmin, highlight_deleted
from django.utils.translation import gettext_lazy as _

from ..models import Contract


@admin.register(Contract)
class ContractAdmin(SafeDeleteAdmin):
    """
    Admin configuration for Contract model.
    Includes:
    - Soft delete support
    - Search, filters, ordering
    - Clean, structured layout
    """

    list_display = (
        highlight_deleted,
        "id",
        "contract_code",
        "stage",
        "contract_date",
        "contact",
        "created_at",
    ) + SafeDeleteAdmin.list_display

    search_fields = ("contract_code", "contact__name", "contact__email")

    list_filter = ("stage", "contract_date", "created_at", "deleted")

    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "contract_code",
                    "stage",
                )
            },
        ),
        (
            _("Contract Info"),
            {"fields": ("contract_date", "contact")},
        ),
        (
            _("System Fields"),
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    field_to_highlight = "contract_code"
