from django.contrib import admin
from .models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "file_name",
        "attachment_type",
        "content_type",
        "object_id",
        "file_size",
        "created_at",
    ]
    list_filter = ["attachment_type", "content_type", "created_at"]
    search_fields = ["file_name", "description"]
    readonly_fields = ["file_name", "file_size", "attachment_type", "created_at", "updated_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Attachment Info", {
            "fields": ("attachment_type", "file", "file_name", "file_size", "description")
        }),
        ("Related Entity", {
            "fields": ("content_type", "object_id")
        }),
        ("Audit Info", {
            "fields": ("owner", "created_by", "created_at", "updated_by", "updated_at"),
            "classes": ("collapse",)
        }),
    )
