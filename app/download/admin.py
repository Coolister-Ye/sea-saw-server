from django.contrib import admin

from download.models import DownloadTask


# Field Admin
@admin.register(DownloadTask)
class DownloadTaskAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "file_name", "status"]
