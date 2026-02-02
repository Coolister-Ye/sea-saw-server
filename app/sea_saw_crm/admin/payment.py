from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from safedelete.admin import SafeDeleteAdmin, highlight_deleted

from ..models.payment import Payment
from sea_saw_attachment.models import Attachment


class PaymentAttachmentInline(GenericTabularInline):
    """Inline for payment attachments (using unified Attachment model)"""
    model = Attachment
    extra = 1
    fields = ('file', 'file_name', 'description')
    readonly_fields = ("file_name", "attachment_type")
    ct_field = "content_type"
    ct_fk_field = "object_id"


@admin.register(Payment)
class PaymentAdmin(SafeDeleteAdmin):
    """
    Admin for Payment model with GenericForeignKey
    - Supports both Order and PurchaseOrder payments
    - Search, filter, and sorting capabilities
    """

    list_display = (
        highlight_deleted,
        "payment_code",
        "payment_type",
        "related_object_display",
        "payment_date",
        "amount",
        "currency",
        "payment_method",
        "created_by",
    ) + SafeDeleteAdmin.list_display

    search_fields = (
        "payment_code",
        "bank_reference",
        "remark",
    )

    list_filter = (
        "payment_method",
        "currency",
        "payment_date",
        "content_type",
        "created_at",
        "deleted",
    )

    ordering = ("-payment_date", "-created_at")

    readonly_fields = (
        "payment_code",
        "payment_type",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "payment_code",
                    "payment_type",
                    "content_type",
                    "object_id",
                    "payment_date",
                    "amount",
                    "currency",
                    "payment_method",
                    "bank_reference",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    field_to_highlight = "payment_code"
    inlines = [PaymentAttachmentInline]

    def related_object_display(self, obj):
        """Display the related object (Order or PurchaseOrder)"""
        if obj.related_object:
            return str(obj.related_object)
        return "-"

    related_object_display.short_description = "Related Object"


# Legacy alias for backward compatibility
PaymentRecordAdmin = PaymentAdmin


# PaymentAttachment is now managed by unified AttachmentAdmin
# See admin/attachment.py
