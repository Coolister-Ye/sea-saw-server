"""
Django Admin for Purchase Order models
"""
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.translation import gettext_lazy as _

from sea_saw_attachment.models import Attachment
from ..models import (
    PurchaseOrder,
    PurchaseItem,
)


class PurchaseItemInline(admin.TabularInline):
    """Inline for PurchaseItem"""

    model = PurchaseItem
    extra = 1
    fields = [
        "product_name",
        "specification",
        "purchase_qty",
        "unit",
        "unit_price",
        "total_price",
    ]
    readonly_fields = ["total_price"]


class PurchaseAttachmentInline(GenericTabularInline):
    """Inline for Purchase Attachments (using unified Attachment model)"""

    model = Attachment
    extra = 0
    fields = ["file", "file_name", "description"]
    readonly_fields = ["file_name", "attachment_type"]
    ct_field = "content_type"
    ct_fk_field = "object_id"


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """Admin for PurchaseOrder"""

    list_display = [
        "purchase_code",
        "related_order",
        "account",
        "status",
        "purchase_order_date",
        "total_amount",
        "created_at",
    ]
    list_filter = ["status", "purchase_order_date", "created_at"]
    search_fields = ["purchase_code", "supplier__name", "related_order__order_code"]
    readonly_fields = ["purchase_code", "total_amount", "created_at", "updated_at"]
    inlines = [PurchaseItemInline, PurchaseAttachmentInline]

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "purchase_code",
                    "related_order",
                    "account",
                    "status",
                    "purchase_order_date",
                )
            },
        ),
        (
            _("Logistics Information"),
            {
                "fields": (
                    "etd",
                    "loading_port",
                    "destination_port",
                    "shipment_term",
                    "inco_terms",
                )
            },
        ),
        (
            _("Financial Information"),
            {
                "fields": (
                    "currency",
                    "total_amount",
                    "deposit",
                    "balance",
                )
            },
        ),
        (
            _("Additional Information"),
            {
                "fields": (
                    "comment",
                    "created_by",
                    "updated_by",
                    "owner",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    """Admin for PurchaseItem"""

    list_display = [
        "purchase_order",
        "product_name",
        "purchase_qty",
        "unit",
        "unit_price",
        "total_price",
    ]
    list_filter = ["purchase_order__status", "created_at"]
    search_fields = ["product_name", "purchase_order__purchase_code"]
    readonly_fields = ["total_price", "total_gross_weight", "total_net_weight"]


# PurchaseAttachment is now managed by unified AttachmentAdmin
# See admin/attachment.py
