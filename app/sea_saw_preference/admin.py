from django.contrib import admin

from sea_saw_preference.models import UserColumnPreference


@admin.register(UserColumnPreference)
class UserColumnPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'table_name', 'created_at', 'updated_at')  # Fields to display in the list view
    search_fields = ('user__username', 'table_name')  # Enable search by username and table_name
    list_filter = ('created_at', 'updated_at')  # Enable filter by date
    ordering = ('-created_at',)  # Default ordering by creation date
