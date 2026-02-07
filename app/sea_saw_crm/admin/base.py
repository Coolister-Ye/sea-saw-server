from safedelete.admin import SafeDeleteAdmin


# Base Admin Mixin
class BaseSafeAdmin(SafeDeleteAdmin):
    list_per_page = 50
