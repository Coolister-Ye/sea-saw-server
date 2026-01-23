"""
Order 权限类

专门针对 Order 模型的权限控制。
根据需求，Order 应该只允许 Admin 和 Sale 角色访问。
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class OrderAdminPermission(BasePermission):
    """
    Order Admin 权限

    Admin 角色对所有 Order 有完全权限。
    """

    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "ADMIN"

    def has_object_permission(self, request, view, obj):
        # 只有DRAFT 状态的 Order 可以被修改
        return getattr(obj, "status", None) == "draft"


class OrderSalePermission(BasePermission):
    """
    Order Sale 权限

    Sale 角色基于 owner 的 Order 权限：
    - 读取权限：可以查看自己或下属创建的订单
    - 修改权限：只能修改自己创建的且状态为 DRAFT 的订单
    """

    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "SALE"

    def has_object_permission(self, request, view, obj):
        user = request.user
        owner = getattr(obj, "owner", None)

        if request.method in SAFE_METHODS:
            # retrieve 权限：自己或可见用户
            if owner == user:
                return True
            get_parents = getattr(owner, "get_all_parent_users", None)
            return callable(get_parents) and user in get_parents()
        else:
            # update/delete 权限：仅 owner 且状态为 DRAFT
            return owner == user and getattr(obj, "status", None) == "draft"
