# sea_saw_crm/services/order_service.py
from django.db import transaction
from django.core.exceptions import ValidationError
from ..models.order import Order
from ..models.production import ProductionOrder, ProductionItem
from ..models.outbound import OutboundOrder, OutboundItem
from ..services.order_state_service import OrderStateService


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_production(order: Order, user=None) -> ProductionOrder:
        """
        根据 Order 创建 ProductionOrder
        每个 OrderItem 生成对应的 ProductionItem
        使用 OrderStateService 状态机判断
        """
        target_status = "in_production"
        allowed_actions = OrderStateService.get_allowed_actions(order, user)
        if target_status not in allowed_actions:
            raise ValidationError(
                f"Cannot create production order from current status '{order.status}'"
            )

        # 创建生产单
        production = ProductionOrder.objects.create(
            related_order=order, created_by=user, owner=user, status="draft"
        )

        # 创建生产明细
        items = [
            ProductionItem(
                production_order=production,
                order_item=item,
                planned_qty=item.order_qty or 0,
                owner=user,
                created_by=user,
            )
            for item in order.order_items.all()
        ]
        ProductionItem.objects.bulk_create(items)

        # 更新订单状态
        OrderStateService.transition(
            order=order, target_status=target_status, user=user
        )

        return production

    @staticmethod
    @transaction.atomic
    def create_outbound(order: Order, user=None) -> OutboundOrder:
        """
        根据 Order 创建 OutboundOrder
        每个 OrderItem 生成对应的 OutboundItem
        使用 OrderStateService 状态机判断
        """
        target_status = "in_outbound"
        allowed_actions = OrderStateService.get_allowed_actions(order, user)
        if target_status not in allowed_actions:
            raise ValidationError(
                f"Cannot create outbound order from current status '{order.status}'"
            )

        # 创建出库单
        outbound = OutboundOrder.objects.create(
            order=order, created_by=user, owner=user, status="draft"
        )

        # 创建出库明细
        items = [
            OutboundItem(
                outbound_order=outbound,
                order_item=item,
                owner=user,
                created_by=user,
            )
            for item in order.order_items.all()
        ]
        OutboundItem.objects.bulk_create(items)

        # 更新订单状态
        OrderStateService.transition(
            order=order, target_status=target_status, user=user
        )

        return outbound
