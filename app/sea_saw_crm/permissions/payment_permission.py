# sea_saw_crm/permissions/payment.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


FORBIDDEN_EDIT_STATUSES = {"cancelled", "completed"}


class CanManagePayment(BasePermission):
    """
    Payment 权限规则：

    - ADMIN:
        - 全部允许
    - SALE:
        - 只能操作自己订单的 payment
        - 当 order.status 为 cancelled / completed 时：
            - 只读
            - 禁止 create / update / delete
    """

    def has_permission(self, request, view):
        role = getattr(request.user.role, "role_type", None)

        # 只有 ADMIN / SALE 能访问 Payment API
        return role in ("ADMIN", "SALE")

    def has_object_permission(self, request, view, obj):
        user = request.user
        role = getattr(user.role, "role_type", None)

        # ADMIN 无限制
        if role == "ADMIN":
            return True

        if role != "SALE":
            return False

        order = getattr(obj, "order", None)
        if not order or order.owner != user:
            return False

        # 只读请求始终允许
        if request.method in SAFE_METHODS:
            return True

        # 非只读：检查订单状态
        return order.status not in FORBIDDEN_EDIT_STATUSES
