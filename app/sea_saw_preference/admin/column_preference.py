from django.contrib import admin

from sea_saw_preference.models import UserColumnPreference


@admin.register(UserColumnPreference)
class UserColumnPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "table_name", "created_at", "updated_at")
    search_fields = ("user__username", "table_name")
    list_filter = ("created_at", "updated_at")
    ordering = ("-created_at",)
