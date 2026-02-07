import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from sea_saw_base.models import BaseModel
from sea_saw_base.models import CurrencyType
from .enums import PaymentMethodType, PaymentType


class Payment(BaseModel):
    """
    统一的付款单模型
    Unified payment model

    新设计说明 / New Design Notes:
    - pipeline: 直接外键,标识付款所属的业务流程(必须)
    - content_type + object_id: GenericForeignKey,绑定Pipeline下的具体子流程实体

    Pipeline下的子流程实体包括:
    1. Order (订单 - 流程起点)
    2. ProductionOrder (生产订单)
    3. PurchaseOrder (采购订单)
    4. OutboundOrder (出库订单)

    使用场景 / Usage Examples:

    1. Order Payment (订单收款 - 客户支付):
       pipeline = pipeline_instance
       content_type = ContentType.objects.get_for_model(Order)
       object_id = order.id
       payment_type = ORDER_PAYMENT

    2. PurchaseOrder Payment (采购付款 - 支付给供应商):
       pipeline = pipeline_instance
       content_type = ContentType.objects.get_for_model(PurchaseOrder)
       object_id = purchase_order.id
       payment_type = PURCHASE_PAYMENT

    3. ProductionOrder Payment (生产费用):
       pipeline = pipeline_instance
       content_type = ContentType.objects.get_for_model(ProductionOrder)
       object_id = production_order.id
       payment_type = PRODUCTION_PAYMENT

    4. OutboundOrder Payment (物流费用):
       pipeline = pipeline_instance
       content_type = ContentType.objects.get_for_model(OutboundOrder)
       object_id = outbound_order.id
       payment_type = OUTBOUND_PAYMENT

    关系链 / Relationship Chain:
    Payment → Pipeline (必须)
    Payment → Order/PurchaseOrder/ProductionOrder/OutboundOrder (通过GenericFK)
    """

    payment_code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Payment Code"),
        help_text=_("Auto-generated unique payment code"),
    )

    payment_type = models.CharField(
        max_length=50,
        choices=PaymentType.choices,
        default=PaymentType.ORDER_PAYMENT,
        verbose_name=_("Payment Type"),
        help_text=_("Type of payment (order, purchase, production, outbound)"),
    )

    # Pipeline关联 (必须 - 标识所属业务流程)
    pipeline = models.ForeignKey(
        "sea_saw_pipeline.Pipeline",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("Pipeline"),
        help_text=_("The business pipeline this payment belongs to"),
    )

    # GenericForeignKey绑定具体的子流程实体 (Order, PurchaseOrder, ProductionOrder, OutboundOrder)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Related Entity Type"),
        help_text=_(
            "Type of entity: Order, PurchaseOrder, ProductionOrder, or OutboundOrder"
        ),
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Related Entity ID"),
        help_text=_("ID of the related entity"),
    )
    related_object = GenericForeignKey("content_type", "object_id")

    payment_date = models.DateField(
        verbose_name=_("Payment Date"),
        help_text=_("Date when the payment was made"),
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        verbose_name=_("Amount"),
        help_text=_("Payment amount"),
    )
    currency = models.CharField(
        max_length=10,
        choices=CurrencyType.choices,
        default=CurrencyType.USD,
        verbose_name=_("Currency"),
        help_text=_("Currency code (e.g., USD, CNY)"),
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PaymentMethodType.choices,
        verbose_name=_("Payment Method"),
        help_text=_("Method used for payment"),
    )
    bank_reference = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Bank Reference"),
        help_text=_("Bank transaction reference number"),
    )
    remark = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Remark"),
        help_text=_("Additional notes about the payment"),
    )

    # GenericRelation to unified Attachment model
    attachments = GenericRelation(
        "sea_saw_attachment.Attachment",
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="payment",
    )

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["payment_type"]),
            models.Index(fields=["pipeline"]),  # 新索引: pipeline FK
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["payment_code"]),
        ]

    def save(self, *args, **kwargs):
        # Auto-set payment_type if not set
        if not self.payment_type and self.content_type:
            model_name = self.content_type.model
            if model_name == "order":
                self.payment_type = PaymentType.ORDER_PAYMENT
            elif model_name == "purchaseorder":
                self.payment_type = PaymentType.PURCHASE_PAYMENT
            elif model_name == "productionorder":
                self.payment_type = PaymentType.PRODUCTION_PAYMENT
            elif model_name == "outboundorder":
                self.payment_type = PaymentType.OUTBOUND_PAYMENT
            else:
                # Default to order payment if unknown
                self.payment_type = PaymentType.ORDER_PAYMENT

        # Generate payment code if not set
        if not self.payment_code:
            # Prefix based on payment type
            prefix_map = {
                PaymentType.ORDER_PAYMENT: "OPAY",
                PaymentType.PURCHASE_PAYMENT: "PPAY",
                PaymentType.PRODUCTION_PAYMENT: "PRPAY",
                PaymentType.OUTBOUND_PAYMENT: "OBPAY",
            }
            prefix = prefix_map.get(self.payment_type, "PAY")

            timestamp = timezone.now().strftime("%Y%m%d")
            unique_id = uuid.uuid4().hex[:8].upper()
            self.payment_code = f"{prefix}-{timestamp}-{unique_id}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.payment_code} - {self.amount} {self.currency}"
