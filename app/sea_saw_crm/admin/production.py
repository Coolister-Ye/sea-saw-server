from django.contrib import admin
from safedelete.admin import SafeDeleteAdmin, highlight_deleted

from ..models import ProductionOrder, ProductionItem
from .order import OrderItem


class ProductionItemInline(admin.TabularInline):
    """
    内联显示 ProductionItem
    """

    model = ProductionItem
    extra = 0
    fields = (
        "order_item",
        "planned_qty",
        "produced_qty",
        "progress_rate",
    )
    readonly_fields = ("progress_rate",)
    show_change_link = True


@admin.register(ProductionOrder)
class ProductionOrderAdmin(SafeDeleteAdmin):
    """
    Admin for ProductionOrder
    - 内联显示明细
    - 支持搜索、过滤、排序
    """

    list_display = (
        highlight_deleted,
        "production_code",
        "related_order",
        "planned_date",
        "start_date",
        "end_date",
        "status",
        "remark",
        "created_by",
    ) + SafeDeleteAdmin.list_display

    search_fields = (
        "production_code",
        "related_order__order_code",
        "remark",
        "comment",
    )

    list_filter = (
        "status",
        "planned_date",
        "start_date",
        "end_date",
        "created_at",
        "deleted",
    )

    ordering = ("-created_at",)
    inlines = [ProductionItemInline]

    readonly_fields = ("production_code", "created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "production_code",
                    "related_order",
                    "planned_date",
                    "start_date",
                    "end_date",
                    "status",
                    "remark",
                    "comment",
                    "production_files",
                )
            },
        ),
        (
            "System Info",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )

    field_to_highlight = "production_code"


@admin.register(ProductionItem)
class ProductionItemAdmin(SafeDeleteAdmin):
    """
    Admin for ProductionItem
    """

    list_display = (
        highlight_deleted,
        "production_order",
        "order_item",
        "planned_qty",
        "produced_qty",
        "progress_rate",
        "created_by",
    ) + SafeDeleteAdmin.list_display

    search_fields = (
        "production_order__production_code",
        "order_item__product_name",
    )

    list_filter = (
        "production_order",
        "production_order__status",
        "created_at",
        "deleted",
    )

    readonly_fields = ("progress_rate",)
    ordering = ("-created_at",)
