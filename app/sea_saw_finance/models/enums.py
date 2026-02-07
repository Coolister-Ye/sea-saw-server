
"""
Payment-related enumerations
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentMethodType(models.TextChoices):
    """Payment Method Enum"""

    TT = "TT", _("Telegraphic Transfer")
    LC = "LC", _("Letter of Credit")
    PAYPAL = "PayPal", _("PayPal")
    CASH = "Cash", _("Cash")
    BANK_TRANSFER = "Bank Transfer", _("Bank Transfer")


class PaymentType(models.TextChoices):
    """Payment Type Enum - distinguishes between different payment scenarios"""

    ORDER_PAYMENT = "order_payment", _("Order Payment")
    PURCHASE_PAYMENT = "purchase_payment", _("Purchase Payment")
    PRODUCTION_PAYMENT = "production_payment", _("Production Payment")
    OUTBOUND_PAYMENT = "outbound_payment", _("Outbound Payment")
