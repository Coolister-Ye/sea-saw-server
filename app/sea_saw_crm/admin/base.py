from safedelete.admin import SafeDeleteAdmin


# Base Admin Mixin
class BaseSafeAdmin(SafeDeleteAdmin):
    list_per_page = 50
    ordering = ("created_at",)
    readonly_fields = ("created_at", "updated_at")
