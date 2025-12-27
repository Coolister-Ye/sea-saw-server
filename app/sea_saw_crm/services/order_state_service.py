from django.db import transaction
from django.core.exceptions import ValidationError
from ..constants import ORDER_STATE_MACHINE, ROLE_ALLOWED_TARGET_STATES


class OrderStateService:
    """
    Order 状态机服务
    action == target_status
    """

    @classmethod
    @transaction.atomic
    def transition(cls, *, order, target_status: str, user=None):
        current_status = order.status

        allowed_targets = ORDER_STATE_MACHINE.get(current_status, set())
        if target_status not in allowed_targets:
            raise ValidationError(
                f"Invalid transition: {current_status} -> {target_status}"
            )

        order.status = target_status
        if user:
            order.updated_by = user

        order.save(update_fields=["status", "updated_by"])
        return order

    @staticmethod
    def get_allowed_actions(order, user):
        """
        返回：当前用户在该订单下允许切换到的目标状态列表
        """
        role = getattr(getattr(user, "role", None), "role_type", None)
        if not role:
            return []

        # 当前状态允许到达的状态
        state_targets = ORDER_STATE_MACHINE.get(order.status, set())

        # 角色允许到达的状态
        role_targets = ROLE_ALLOWED_TARGET_STATES.get(role, set())

        # ADMIN
        if "*" in role_targets:
            return sorted(state_targets)

        return sorted(state_targets & role_targets)
