import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from decimal import Decimal

from .base import BaseModel
from .order import Order


class PaymentMethodType(models.TextChoices):
    TT = "TT", _("Telegraphic Transfer")
    LC = "LC", _("Letter of Credit")
    PAYPAL = "PayPal", _("PayPal")
    CASH = "Cash", _("Cash")
    BANK_TRANSFER = "Bank Transfer", _("Bank Transfer")


class PaymentRecord(BaseModel):
    """
    收款单
    用于记录订单收到的付款（定金、尾款、多次付款）
    """

    payment_code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Payment Code"),
        help_text=_("Unique identifier for this payment record."),
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("Related Order"),
        help_text=_("The order this payment is associated with."),
    )

    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Payment Date"),
    )

    amount = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        verbose_name=_("Amount"),
        help_text=_("Payment amount received."),
    )

    currency = models.CharField(
        max_length=10,
        default="USD",
        verbose_name=_("Currency"),
        help_text=_("Currency of the payment, e.g., USD, EUR."),
    )

    payment_method = models.CharField(
        max_length=50,
        choices=PaymentMethodType.choices,
        null=True,
        blank=True,
        verbose_name=_("Payment Method"),
        help_text=_("Method of payment, e.g., TT, LC, PayPal."),
    )

    bank_reference = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Bank Reference"),
        help_text=_("Bank transaction reference number."),
    )

    attachment = models.FileField(
        upload_to="payment_attachments/",
        null=True,
        blank=True,
        verbose_name=_("Attachment"),
        help_text=_("Upload bank slip or proof of payment."),
    )

    remark = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Remark"),
        help_text=_("Additional notes regarding this payment."),
    )

    class Meta:
        verbose_name = _("Payment Record")
        verbose_name_plural = _("Payment Records")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.payment_code} - {self.amount} {self.currency}"

    @property
    def order_unpaid_amount(self):
        """
        自动计算订单剩余未收金额
        """
        total_paid = self.order.payments.aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.0")
        return (self.order.total_amount or Decimal("0.0")) - total_paid

    def save(self, *args, **kwargs):
        """自动生成编号"""
        if not self.payment_code:
            self.payment_code = f"PAY-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
