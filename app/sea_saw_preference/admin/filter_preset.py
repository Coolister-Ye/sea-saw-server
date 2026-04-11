from django.contrib import admin

from sea_saw_preference.models import UserFilterPreset


@admin.register(UserFilterPreset)
class UserFilterPresetAdmin(admin.ModelAdmin):
    list_display = ("preset_type", "entity", "name", "key", "user", "created_at", "updated_at")
    search_fields = ("user__username", "entity", "name", "key")
    list_filter = ("preset_type", "entity", "created_at")
    ordering = ("preset_type", "entity", "created_at")
    fields = ("preset_type", "entity", "name", "key", "user", "params")
