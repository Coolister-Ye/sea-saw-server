from rest_framework.permissions import BasePermission, SAFE_METHODS
from ..constants import OrderStatus


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "ADMIN"

    def has_object_permission(self, request, view, obj):
        return True  # admin 对所有对象都有权限


class IsSale(BasePermission):
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
            # update/delete 权限
            return owner == user and getattr(obj, "status", None) == "DRAFT"


class IsProduction(BasePermission):

    def has_permission(self, request, view):
        """Production 用户只能操作 PRODUCTION 状态的订单"""

        if view.action in ["create", "destroy"]:
            return False
        return getattr(request.user.role, "role_type", None) == "PRODUCTION"

    def has_object_permission(self, request, view, obj):
        status = getattr(obj, "status", None)
        if request.method in SAFE_METHODS:
            return status in OrderStatus.PRODUCTION_VISIBLE
        return status in OrderStatus.PRODUCTION_EDITABLE


class IsWarehouse(BasePermission):

    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "WAREHOUSE"

    def has_object_permission(self, request, view, obj):
        status = getattr(obj, "status", None)
        if request.method in SAFE_METHODS:
            return status in OrderStatus.WAREHOUSE_VISIBLE
        return status in OrderStatus.WAREHOUSE_EDITABLE
