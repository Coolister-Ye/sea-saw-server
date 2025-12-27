from .base_model_manager import BaseModelManager
from django.db import models, transaction
from django.core.exceptions import ValidationError


class OrderModelManager(BaseModelManager):
    """
    Order 聚合根 Manager
    功能：
    - 从 Order 创建 ProductionOrder / OutboundOrder
    - 幂等控制（防重复）
    - 自动生成 ProductionItem / OutboundItem
    """

    # ------------------------
    # 创建 ProductionOrder
    # ------------------------
    @transaction.atomic
    def create_production(
        self,
        *,
        order,
        planned_date=None,
        remark=None,
        user=None,
        copy_items=True,
        force=False,
        **extra_fields,
    ):
        # 延迟导入，避免循环依赖
        from ..models.production import ProductionOrder

        # 幂等校验
        if not force and order.production_orders.exists():
            raise ValidationError("Production already created for this order.")

        # 创建 ProductionOrder
        production = ProductionOrder.objects.create_with_user(
            user=user,
            related_order=order,
            planned_date=planned_date,
            remark=remark or order.comment,
            **extra_fields,
        )

        # 自动生成 ProductionItem
        if copy_items:
            self._create_production_items(production, order, user)

        return production

    def _create_production_items(self, production, order, user=None):
        from ..models.production import ProductionItem

        items = [
            ProductionItem(
                production_order=production,
                order_item=oi,
                planned_qty=oi.order_qty or 0,
                owner=user,
                created_by=user,
            )
            for oi in order.order_items.all()
        ]

        if items:
            ProductionItem.objects.bulk_create(items)

    # ------------------------
    # 创建 OutboundOrder
    # ------------------------
    @transaction.atomic
    def create_outbound(
        self,
        *,
        order,
        etd=None,
        remark=None,
        user=None,
        copy_items=True,
        force=False,
        **extra_fields,
    ):
        # 延迟导入，避免循环依赖
        from ..models.outbound import OutboundOrder

        # 幂等校验
        if not force and order.outbound_orders.exists():
            raise ValidationError("Outbound already created for this order.")

        # 创建 OutboundOrder
        outbound = OutboundOrder.objects.create_with_user(
            user=user,
            related_order=order,
            etd=etd or order.etd,
            remark=remark or order.comment,
            **extra_fields,
        )

        # 自动生成 OutboundItem
        if copy_items:
            self._create_outbound_items(outbound, order, user)

        return outbound

    def _create_outbound_items(self, outbound, order, user=None):
        from ..models.outbound import OutboundItem

        items = [
            OutboundItem(
                outbound_order=outbound,
                order_item=oi,
                owner=user,
                created_by=user,
            )
            for oi in order.order_items.all()
        ]

        if items:
            OutboundItem.objects.bulk_create(items)
