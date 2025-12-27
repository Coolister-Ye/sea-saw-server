from rest_framework.permissions import BasePermission

ROLE_ALLOWED_ACTIONS = {
    "SALE": {"confirm", "cancel"},
    "PRODUCTION": {"start_production", "finish_production", "issue"},
    "WAREHOUSE": {"finish_outbound"},
    "ADMIN": {"*"},
}


class CanTransitionOrder(BasePermission):
    """
    控制谁可以对 Order 执行 transition action
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        # 只拦 transition 这个 action
        if view.action != "transition":
            return True

        role = getattr(request.user.role, "role_type", None)
        if not role:
            return False

        allowed = ROLE_ALLOWED_ACTIONS.get(role)
        if not allowed:
            return False

        # admin 通配
        if "*" in allowed:
            return True

        action_name = request.data.get("action")
        if not action_name:
            return False

        return action_name in allowed
