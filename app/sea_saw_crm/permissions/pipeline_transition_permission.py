from rest_framework.permissions import BasePermission

from ..constants import PIPELINE_ROLE_ALLOWED_TARGET_STATES


class CanTransitionPipeline(BasePermission):
    """
    控制谁可以对 Pipeline 执行 transition action
    基于 PIPELINE_ROLE_ALLOWED_TARGET_STATES 配置
    """

    message = "You do not have permission to transition to this status."

    def has_permission(self, request, view):
        # 只拦 transition 这个 action
        if view.action != "transition":
            return True

        role = getattr(request.user.role, "role_type", None)
        if not role:
            return False

        # 获取角色允许的目标状态
        allowed_target_states = PIPELINE_ROLE_ALLOWED_TARGET_STATES.get(role)
        if not allowed_target_states:
            return False

        # admin 通配
        if "*" in allowed_target_states:
            return True

        # 检查请求的目标状态是否在允许列表中
        target_status = request.data.get("target_status")
        if not target_status:
            return False

        return target_status in allowed_target_states
