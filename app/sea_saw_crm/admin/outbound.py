from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from safedelete.admin import SafeDeleteAdmin, highlight_deleted

from ..models import OutboundOrder, OutboundItem, Attachment


class OutboundItemInline(admin.TabularInline):
    model = OutboundItem
    extra = 0
    fields = (
        "order_item",
        "production_item",
        "outbound_qty",
        "outbound_net_weight",
        "outbound_gross_weight",
    )
    readonly_fields = ()
    show_change_link = True


class OutboundAttachmentInline(GenericTabularInline):
    """Inline for Outbound Attachments (using unified Attachment model)"""

    model = Attachment
    extra = 0
    fields = ["file", "file_name", "description"]
    readonly_fields = ["file_name", "attachment_type"]
    ct_field = "content_type"
    ct_fk_field = "object_id"


@admin.register(OutboundOrder)
class OutboundOrderAdmin(SafeDeleteAdmin):
    """
    Admin for OutboundOrder:
    - Inline OutboundItems
    - Status display
    - Soft delete support
    """

    list_display = (
        highlight_deleted,
        "outbound_code",
        "outbound_date",
        "status",
        "container_no",
        "seal_no",
        "destination_port",
        "logistics_provider",
        "loader",
        "created_at",
    ) + SafeDeleteAdmin.list_display

    search_fields = (
        "outbound_code",
        "order__order_code",
        "container_no",
        "seal_no",
        "destination_port",
        "logistics_provider",
        "loader",
    )

    list_filter = (
        "status",
        "outbound_date",
        "destination_port",
        "logistics_provider",
        "created_at",
        "deleted",
    )

    ordering = ("-created_at",)

    readonly_fields = ("outbound_code", "created_at", "updated_at")

    inlines = [OutboundItemInline, OutboundAttachmentInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "outbound_code",
                    "order",
                    "outbound_date",
                    "status",
                    "remark",
                )
            },
        ),
        (
            "Logistics Info",
            {
                "fields": (
                    "container_no",
                    "seal_no",
                    "destination_port",
                    "logistics_provider",
                    "loader",
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

    field_to_highlight = "outbound_code"


@admin.register(OutboundItem)
class OutboundItemAdmin(admin.ModelAdmin):
    """
    Standalone admin for OutboundItem
    (optional, if you want to edit items separately)
    """

    list_display = (
        "outbound_order",
        "order_item",
        "production_item",
        "outbound_qty",
        "outbound_net_weight",
        "outbound_gross_weight",
        "created_at",
    )

    search_fields = (
        "outbound_order__outbound_code",
        "order_item__product_name",
        "production_item__order_item__product_name",
    )

    list_filter = ("outbound_order__status", "created_at")
    ordering = ("-created_at",)
