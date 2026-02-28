"""
Pipeline Model - Business Process Orchestration

Pipeline模型作为业务流程的主入口,串联整个订单处理流程:
1. Order (销售订单)
2. ProductionOrder / PurchaseOrder (生产订单/采购订单)
3. OutboundOrder (出库订单)
4. Payments (付款记录)

Pipeline负责:
- 流程编排和状态管理
- 子订单创建和关联
- 业务逻辑控制
- 数据聚合展示
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.db.models import Sum

from sea_saw_base.models import BaseModel
from .enums import PipelineStatusType, PipelineType, ActiveEntityType
from ...manager.pipeline_model_manager import PipelineModelManager


class Pipeline(BaseModel):
    """
    Pipeline - Business Process Orchestration Model

    设计说明:
    - Pipeline作为业务流程的顶层容器和编排器
    - Order作为销售订单数据容器,不再包含流程控制逻辑
    - 通过FK关联Order、ProductionOrder、PurchaseOrder、OutboundOrder
    - 支持多种业务流程类型(生产流程、采购流程、混合流程)
    """

    objects = PipelineModelManager()

    pipeline_code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Pipeline Code"),
        help_text=_("Unique identifier for this business process pipeline"),
    )

    pipeline_type = models.CharField(
        max_length=50,
        choices=PipelineType.choices,
        default=PipelineType.PRODUCTION_FLOW,
        verbose_name=_("Pipeline Type"),
        help_text=_("Type of business process flow"),
    )

    status = models.CharField(
        max_length=50,
        choices=PipelineStatusType.choices,
        default=PipelineStatusType.DRAFT,
        verbose_name=_("Pipeline Status"),
        help_text=_("Current status of the business process"),
    )

    active_entity = models.CharField(
        max_length=25,
        choices=ActiveEntityType.choices,
        default=ActiveEntityType.NONE,
        verbose_name=_("Active Entity"),
        help_text=_("Currently active sub-entity type in this pipeline"),
    )

    # Core Business Entities
    # Sales Order (required - the starting point)
    order = models.OneToOneField(
        "sea_saw_sales.Order",
        on_delete=models.CASCADE,
        related_name="pipeline",
        verbose_name=_("Sales Order"),
        help_text=_("The main sales order for this pipeline"),
    )

    # 客户账户
    account = models.ForeignKey(
        "sea_saw_crm.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pipelines",
        verbose_name=_("Account"),
        help_text=_("Customer account for this pipeline"),
    )

    # 联系人
    contact = models.ForeignKey(
        "sea_saw_crm.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pipelines",
        verbose_name=_("Contact"),
        help_text=_("Contact person for this pipeline"),
    )

    # Production Orders (one-to-many, optional)
    # Accessed via reverse relation: pipeline.production_orders.all()

    # Purchase Orders (one-to-many, optional)
    # Accessed via reverse relation: pipeline.purchase_orders.all()

    # Outbound Orders (one-to-many, optional)
    # Accessed via reverse relation: pipeline.outbound_orders.all()

    # Timeline
    order_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Order Date"),
        help_text=_("Date when the order was created"),
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Confirmed At"),
        help_text=_("When the order was confirmed"),
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Completed At"),
        help_text=_("When the entire pipeline was completed"),
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Cancelled At"),
        help_text=_("When the pipeline was cancelled"),
    )

    # Stage-level timestamps — set automatically on each status transition
    in_purchase_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("In Purchase At"),
        help_text=_("When purchase stage started"),
    )

    purchase_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Purchase Completed At"),
        help_text=_("When purchase was completed"),
    )

    in_production_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("In Production At"),
        help_text=_("When production stage started"),
    )

    production_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Production Completed At"),
        help_text=_("When production was completed"),
    )

    in_purchase_and_production_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("In Purchase And Production At"),
        help_text=_("When combined purchase+production stage started"),
    )

    purchase_and_production_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Purchase And Production Completed At"),
        help_text=_("When combined purchase+production was completed"),
    )

    in_outbound_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("In Outbound At"),
        help_text=_("When outbound process started"),
    )

    outbound_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Outbound Completed At"),
        help_text=_("When outbound was completed"),
    )

    # Additional Info
    remark = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Remark"),
        help_text=_("Additional notes for this pipeline"),
    )

    class Meta:
        verbose_name = _("Pipeline")
        verbose_name_plural = _("Pipelines")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["pipeline_code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["pipeline_type"]),
            models.Index(fields=["order_date"]),
            models.Index(fields=["account"]),
        ]

    def __str__(self):
        return f"{self.pipeline_code} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Auto-generate pipeline code if not set
        if not self.pipeline_code:
            self.pipeline_code = self.generate_code()

        # Sync account from order if not set
        if not self.account and self.order and self.order.account:
            self.account = self.order.account

        # Sync contact from order if not set
        if not self.contact and self.order and self.order.contact:
            self.contact = self.order.contact

        # Sync order_date from order if not set
        if not self.order_date and self.order and self.order.order_date:
            self.order_date = self.order.order_date

        super().save(*args, **kwargs)

    def generate_code(self):
        """Auto-generate pipeline code"""
        year = timezone.now().year
        count = Pipeline.objects.filter(created_at__year=year).count() + 1
        return f"PL{year}-{count:06d}"

    # State Transition Methods
    def transition(self, target_status: str, user=None):
        """
        Transition pipeline to target status

        Args:
            target_status: Target status to transition to
            user: User performing the transition

        Returns:
            bool: True if transition successful
        """
        from ...services.pipeline_state_service import PipelineStateService

        return PipelineStateService.transition(
            pipeline=self,
            target_status=target_status,
            user=user,
        )

    # Sub-Entity Creation Methods
    def create_order(self, user=None, **kwargs):
        """
        Create an order for this pipeline

        This is useful when pipeline is created first without an order,
        or when duplicating an order workflow.

        Returns:
            Order: Created order
        """
        return Pipeline.objects.create_order(pipeline=self, user=user, **kwargs)

    def create_production_order(self, user=None, **kwargs):
        """
        Create a production order for this pipeline

        Returns:
            ProductionOrder: Created production order
        """
        return Pipeline.objects.create_production_order(
            pipeline=self, user=user, **kwargs
        )

    def create_purchase_order(self, user=None, **kwargs):
        """
        Create a purchase order for this pipeline

        Returns:
            PurchaseOrder: Created purchase order
        """
        return Pipeline.objects.create_purchase_order(
            pipeline=self, user=user, **kwargs
        )

    def create_outbound_order(self, user=None, **kwargs):
        """
        Create an outbound order for this pipeline

        Returns:
            OutboundOrder: Created outbound order
        """
        return Pipeline.objects.create_outbound_order(
            pipeline=self, user=user, **kwargs
        )
