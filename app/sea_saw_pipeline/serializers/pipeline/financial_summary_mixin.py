from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum


FINANCIAL_SUMMARY_FIELDS = [
    "order_total_amount",
    "purchase_order_total_amount",
    "purchase_margin",
    "received_order_total_amount",
    "paid_purchase_order_total_amount",
]


class FinancialSummaryMixin(serializers.Serializer):
    """
    Adds five read-only computed financial fields to Admin and Sales serializers.

    Fields:
    - order_total_amount              : Order.total_amount (stored)
    - purchase_order_total_amount     : SUM of all PurchaseOrder.total_amount
    - purchase_margin                 : order_total_amount - purchase_order_total_amount
    - received_order_total_amount     : SUM of payments with type=order_payment
    - paid_purchase_order_total_amount: SUM of payments with type=purchase_payment

    Inherits from serializers.Serializer so that DRF's SerializerMetaclass
    processes this class and registers the SerializerMethodFields in
    _declared_fields, making them visible to subclasses via normal metaclass
    inheritance.
    """

    order_total_amount = serializers.SerializerMethodField(
        read_only=True,
        label=_("Order Total Amount"),
    )
    purchase_order_total_amount = serializers.SerializerMethodField(
        read_only=True,
        label=_("Purchase Order Total Amount"),
    )
    purchase_margin = serializers.SerializerMethodField(
        read_only=True,
        label=_("Purchase Margin"),
    )
    received_order_total_amount = serializers.SerializerMethodField(
        read_only=True,
        label=_("Received Order Total Amount"),
    )
    paid_purchase_order_total_amount = serializers.SerializerMethodField(
        read_only=True,
        label=_("Paid Purchase Order Total Amount"),
    )

    def get_order_total_amount(self, obj):
        try:
            return obj.order.total_amount if obj.order_id else None
        except Exception:
            return None

    def get_purchase_order_total_amount(self, obj):
        result = obj.purchase_orders.aggregate(total=Sum("total_amount"))
        return result["total"]

    def get_purchase_margin(self, obj):
        order_amount = self.get_order_total_amount(obj)
        purchase_amount = self.get_purchase_order_total_amount(obj)
        if order_amount is None or purchase_amount is None:
            return None
        return order_amount - purchase_amount

    def get_received_order_total_amount(self, obj):
        result = obj.payments.filter(payment_type="order_payment").aggregate(
            total=Sum("amount")
        )
        return result["total"]

    def get_paid_purchase_order_total_amount(self, obj):
        result = obj.payments.filter(payment_type="purchase_payment").aggregate(
            total=Sum("amount")
        )
        return result["total"]
