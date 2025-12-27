from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import BaseModel
from .contact import Contact
from ..manager import OrderModelManager

from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class OrderStatusType(models.TextChoices):
    """Order Status Enum"""

    DRAFT = "draft", _("Draft")
    ORDER_CONFIRMED = "order_confirmed", _("Order Confirmed")
    IN_PRODUCTION = "in_production", _("In Production")
    PRODUCTION_COMPLETED = "production_completed", _("Production Completed")
    IN_OUTBOUND = "in_outbound", _("In Outbound")
    OUTBOUND_COMPLETED = "outbound_completed", _("Outbound Completed")
    COMPLETED = "completed", _("Completed")
    CANCELLED = "cancelled", _("Cancelled")
    ISSUE_REPORTED = "issue_reported", _("Issue Reported")


class UnitType(models.TextChoices):
    """Unit Enum"""

    KGS = "kgs", _("KGS")
    LBS = "lbs", _("LBS")


class Order(BaseModel):
    """
    Sales Order
    Contains shipment info, linked contract, price summary and status.
    """

    objects = OrderModelManager()

    order_code = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Order Code"),
        help_text=_("Unique identifier for this order."),
    )

    order_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Order Date"),
    )

    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts",
        verbose_name=_("Contact"),
    )

    etd = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("ETD"),
        help_text=_("Estimated time of departure."),
    )

    status = models.CharField(
        max_length=32,
        choices=OrderStatusType.choices,
        default=OrderStatusType.DRAFT,
        verbose_name=_("Order Status"),
    )

    # Logistic Info
    loading_port = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default="Any port of CHINA",
        verbose_name=_("Loading Port"),
    )

    destination_port = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Destination Port"),
    )

    shipment_term = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("Shipment Term"),
    )

    # Finance
    inco_terms = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name=_("Inco Terms"),
    )

    currency = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name=_("Currency"),
    )

    deposit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Deposit"),
    )

    balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Balance"),
    )

    total_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Total Amount"),
    )

    comment = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Comment"),
    )

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_code"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.order_code or _("Unnamed Order")

    def generate_code(self):
        """Auto-generate order code"""

        year = timezone.now().year
        count = Order.objects.filter(created_at__year=year).count() + 1
        return f"SO{year}-{count:06d}"

    def update_total_amount(self):
        """直接用 QuerySet update 避免递归 save()"""
        total = self.order_items.aggregate(total=Sum("total_price"))[
            "total"
        ] or Decimal("0")
        Order.objects.filter(pk=self.pk).update(total_amount=total)

    def transition(self, action: str, user=None):
        from ..services.order_state_service import OrderStateService

        return OrderStateService.transition(
            order=self,
            action=action,
            user=user,
        )

    def create_production(self, user=None):
        from ..services import OrderService

        return OrderService.create_production(self, user=user)

    def create_outbound(self, user=None):
        from ..services import OrderService

        return OrderService.create_outbound(self, user=user)

    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = self.generate_code()
        super().save(*args, **kwargs)
        # 保存后自动更新 total_amount
        if hasattr(self, "order_items"):
            self.update_total_amount()


class OrderItem(BaseModel):
    """
    Order line item:
    Product + packaging + weights + pricing.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name=_("Order"),
    )

    # Product Info
    product_name = models.CharField(
        max_length=200,
        verbose_name=_("Product Name"),
    )

    specification = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name=_("Specification"),
    )

    outter_packaging = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Outter Packaging"),
    )

    inner_packaging = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Inner Packaging"),
    )

    size = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Size"),
    )

    unit = models.CharField(
        max_length=20,
        choices=UnitType.choices,
        default=UnitType.KGS,
        verbose_name=_("Unit"),
    )

    # Weight
    glazing = models.DecimalField(
        max_digits=5,
        decimal_places=5,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("1")),
        ],
        verbose_name=_("Glazing (%)"),
    )

    gross_weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Gross Weight"),
    )

    net_weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Net Weight"),
    )

    order_qty = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Order Quantity"),
    )

    # Auto-calculated (optional)
    total_gross_weight = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Total Gross Weight"),
    )

    total_net_weight = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Total Net Weight"),
    )

    # Finance
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Unit Price"),
    )

    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Total Price"),
    )

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["product_name"]),
        ]

    def __str__(self):
        return self.product_name or _("Unnamed Item")

    def save(self, *args, **kwargs):
        """计算净重、总重、总价"""
        if self.glazing and self.gross_weight:
            self.net_weight = self.gross_weight * (1 - self.glazing)

        if self.net_weight and self.order_qty:
            self.total_net_weight = self.net_weight * self.order_qty

        if self.gross_weight and self.order_qty:
            self.total_gross_weight = self.gross_weight * self.order_qty

        if self.unit_price and self.order_qty:
            self.total_price = self.unit_price * self.order_qty

        super().save(*args, **kwargs)
        # 保存后触发 order total_amount 更新
        if self.order_id:
            self.order.update_total_amount()
