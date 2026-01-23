"""
Unified Attachment Admin
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """
    Unified Attachment Admin - Manages all attachment types
    """

    list_display = [
        "id",
        "attachment_type",
        "file_name_display",
        "related_entity",
        "file_size_display",
        "created_at",
    ]
    list_filter = [
        "attachment_type",
        "content_type",
        "created_at",
    ]
    search_fields = [
        "file_name",
        "description",
        "object_id",
    ]
    readonly_fields = [
        "content_type",
        "object_id",
        "file_name",
        "file_size",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    fieldsets = (
        (
            _("Attachment Info"),
            {
                "fields": (
                    "attachment_type",
                    "file",
                    "file_name",
                    "file_size",
                    "description",
                )
            },
        ),
        (
            _("Related Entity"),
            {
                "fields": (
                    "content_type",
                    "object_id",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "owner",
                    "created_by",
                )
            },
        ),
    )

    def file_name_display(self, obj):
        """Display file name as a clickable link"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.file.url,
                obj.file_name or "Download",
            )
        return "-"

    file_name_display.short_description = _("File")

    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        if obj.file_size:
            size = obj.file_size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "-"

    file_size_display.short_description = _("Size")

    def related_entity(self, obj):
        """Display related entity with link to admin page"""
        if obj.related_object:
            entity = obj.related_object
            entity_name = entity._meta.verbose_name
            return format_html(
                '<a href="/admin/{}/{}/{}/change/">{}: {}</a>',
                entity._meta.app_label,
                entity._meta.model_name,
                entity.pk,
                entity_name,
                str(entity),
            )
        return "-"

    related_entity.short_description = _("Related To")
