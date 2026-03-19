from django.contrib import admin

from sea_saw_download.models import DownloadTask


@admin.register(DownloadTask)
class DownloadTaskAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "file_name", "status", "total_records", "created_at", "expires_at"]
    list_filter = ["status"]
    search_fields = ["user__username", "file_name"]
    readonly_fields = ["task_id", "created_at", "completed_at", "expires_at", "download_url", "error_message"]
