from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from safedelete.admin import SafeDeleteAdmin, highlight_deleted
from django.utils.translation import gettext_lazy as _

from sea_saw_attachment.models import Attachment
from ..models import Order, OrderItem 


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        "product_name",
        "specification",
        "outter_packaging",
        "inner_packaging",
        "size",
        "unit",
        "glazing",
        "gross_weight",
        "net_weight",
        "order_qty",
        "unit_price",
        "total_price",
        "total_gross_weight",
        "total_net_weight",
    )
    readonly_fields = (
        "net_weight",
        "total_price",
        "total_gross_weight",
        "total_net_weight",
    )
    show_change_link = True


class OrderAttachmentInline(GenericTabularInline):
    """Inline for Order Attachments (using unified Attachment model)"""

    model = Attachment
    extra = 0
    fields = ["file", "file_name", "description"]
    readonly_fields = ["file_name", "attachment_type"]
    ct_field = "content_type"
    ct_fk_field = "object_id"


@admin.register(Order)
class OrderAdmin(SafeDeleteAdmin):
    """
    Admin for Order model with:
    - Soft delete support
    - Full search/filter
    - Inline Order Items
    - Readonly calculated totals
    """

    list_display = (
        highlight_deleted,
        "order_code",
        "order_date",
        "account",
        "contact",
        "status",
        "etd",
        "total_amount",
        "created_at",
    ) + SafeDeleteAdmin.list_display

    search_fields = (
        "order_code",
        "company__company_name",
        "contact__name",
        "contact__email",
        "destination_port",
        "loading_port",
    )

    list_filter = (
        "status",
        "order_date",
        "etd",
        "currency",
        "created_at",
        "deleted",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "total_amount",
        "created_at",
        "updated_at",
    )

    inlines = [OrderItemInline, OrderAttachmentInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order_code",
                    "order_date",
                    "status",
                    "account",
                    "contact",
                    "comment",
                )
            },
        ),
        (
            _("Logistics"),
            {
                "fields": (
                    "loading_port",
                    "destination_port",
                    "shipment_term",
                    "etd",
                )
            },
        ),
        (
            _("Finance"),
            {
                "fields": (
                    "inco_terms",
                    "currency",
                    "deposit",
                    "balance",
                    "total_amount",
                )
            },
        ),
        (
            _("System Info"),
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                    "created_by",
                    "updated_by",
                    "owner",
                ),
            },
        ),
    )

    field_to_highlight = "order_code"

    def save_model(self, request, obj, form, change):
        """
        Ensure audit fields are set correctly in Admin.
        """
        if not change:
            if not obj.owner:
                obj.owner = request.user
            if not obj.created_by:
                obj.created_by = request.user
        else:
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)
