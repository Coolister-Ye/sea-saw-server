from django.contrib import admin
from safedelete.admin import SafeDeleteAdmin, highlight_deleted

from ..models import PaymentRecord
from .order import Order


@admin.register(PaymentRecord)
class PaymentRecordAdmin(SafeDeleteAdmin):
    """
    Admin for PaymentRecord
    - 支持搜索、过滤、排序
    - 显示订单剩余未收金额
    """

    list_display = (
        highlight_deleted,
        "payment_code",
        "order",
        "payment_date",
        "amount",
        "currency",
        "payment_method",
        "order_unpaid_amount",
        "created_by",
    ) + SafeDeleteAdmin.list_display

    search_fields = (
        "payment_code",
        "order__order_code",
        "bank_reference",
        "remark",
    )

    list_filter = (
        "payment_method",
        "currency",
        "payment_date",
        "created_at",
        "deleted",
    )

    ordering = ("-payment_date", "-created_at")

    readonly_fields = (
        "payment_code",
        "created_at",
        "updated_at",
        "order_unpaid_amount",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "payment_code",
                    "order",
                    "payment_date",
                    "amount",
                    "currency",
                    "payment_method",
                    "bank_reference",
                    "attachment",
                    "remark",
                    "order_unpaid_amount",
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

    def order_unpaid_amount(self, obj):
        """显示订单剩余未收金额"""
        return obj.order_unpaid_amount

    order_unpaid_amount.short_description = "Unpaid Amount"
