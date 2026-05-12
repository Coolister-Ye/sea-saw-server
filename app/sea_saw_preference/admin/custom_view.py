from django.contrib import admin

from sea_saw_preference.models import CustomView


@admin.register(CustomView)
class CustomViewAdmin(admin.ModelAdmin):
    list_display = ("owner", "entity", "name", "visibility", "is_default", "created_at")
    list_filter = ("entity", "visibility", "is_default")
    search_fields = ("owner__username", "name", "entity")
    filter_horizontal = ("shared_users", "shared_roles")
    readonly_fields = ("created_at", "updated_at")
