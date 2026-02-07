from rest_framework.permissions import BasePermission, SAFE_METHODS

from sea_saw_pipeline.models.pipeline import PipelineStatusType
from ..constants import ROLE_PAYMENT_TYPE_ACCESS


class CanManagePayment(BasePermission):
    """
    Payment 权限规则：基于角色、Payment Type 和 Pipeline 状态控制

    角色与 Payment Type 访问权限：
    - ADMIN: 可以访问所有类型的 payment (ORDER, PURCHASE, PRODUCTION, OUTBOUND)
    - SALE: 可以管理 ORDER_PAYMENT（客户收款）和 PURCHASE_PAYMENT（采购付款）
    - PRODUCTION: 可以管理 PRODUCTION_PAYMENT（生产费用）
    - WAREHOUSE: 可以管理 OUTBOUND_PAYMENT（物流费用）

    Pipeline 状态限制：
    - 所有角色在 Pipeline 状态为 CANCELLED 或 COMPLETED 时：
        - 只读访问
        - 禁止 create / update / delete
    - 非 ADMIN 角色只能操作自己或下属的 pipeline 的 payment

    权限检查顺序：
    1. 角色是否有权限访问该 payment_type
    2. 是否为 pipeline 所有者或可见用户
    3. Pipeline 状态是否允许修改
    """

    def has_permission(self, request, view):
        """
        View-level permission: 检查用户角色是否可以访问 Payment API
        """
        role = getattr(request.user.role, "role_type", None)
        # 所有在 ROLE_PAYMENT_TYPE_ACCESS 中定义的角色都可以访问
        return role in ROLE_PAYMENT_TYPE_ACCESS

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission: 基于 payment_type、pipeline 所有权和状态控制
        """
        user = request.user
        role = getattr(user.role, "role_type", None)

        # ADMIN 无限制
        if role == "ADMIN":
            return True

        # 检查角色是否有权限访问该 payment_type
        allowed_payment_types = ROLE_PAYMENT_TYPE_ACCESS.get(role, set())
        if obj.payment_type not in allowed_payment_types:
            return False

        # 检查 pipeline 所有权
        pipeline = getattr(obj, "pipeline", None)
        if not pipeline:
            return False

        # 检查是否为当前用户或其下属的 pipeline
        visible_users = (
            user.get_all_visible_users()
            if callable(getattr(user, "get_all_visible_users", None))
            else [user]
        )
        if pipeline.owner not in visible_users:
            return False

        # 只读请求始终允许（在通过以上检查后）
        if request.method in SAFE_METHODS:
            return True

        # 非只读请求：检查 pipeline 状态
        # 当 pipeline 已取消或已完成时，禁止修改 payment
        forbidden_statuses = {
            PipelineStatusType.CANCELLED,
            PipelineStatusType.COMPLETED,
        }
        return pipeline.status not in forbidden_statuses
