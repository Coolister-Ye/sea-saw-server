"""
通用角色权限类

这些权限类基于用户角色进行基础的访问控制，可以在多个 ViewSet 中复用。
每个权限类只检查用户的角色类型，不涉及具体的业务逻辑。

对于需要复杂业务逻辑的权限控制（如基于状态、owner 等），
应该创建特定的权限类（如 OrderPermission, PipelinePermission 等）。
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Admin 角色权限

    允许所有拥有 ADMIN 角色的用户访问。
    """

    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "ADMIN"

    def has_object_permission(self, request, view, obj):
        return True  # admin 对所有对象都有权限


class IsSale(BasePermission):
    """
    Sale 角色权限

    允许所有拥有 SALE 角色的用户访问。
    """

    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "SALE"

    def has_object_permission(self, request, view, obj):
        return True  # 默认允许访问所有对象，具体限制由子类或业务逻辑控制


class IsProduction(BasePermission):
    """
    Production 角色权限

    允许所有拥有 PRODUCTION 角色的用户访问。
    """

    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "PRODUCTION"

    def has_object_permission(self, request, view, obj):
        return True  # 默认允许访问所有对象，具体限制由子类或业务逻辑控制


class IsWarehouse(BasePermission):
    """
    Warehouse 角色权限

    允许所有拥有 WAREHOUSE 角色的用户访问。
    """

    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "WAREHOUSE"

    def has_object_permission(self, request, view, obj):
        return True  # 默认允许访问所有对象，具体限制由子类或业务逻辑控制


class IsPurchase(BasePermission):
    """
    Purchase 角色权限

    允许所有拥有 PURCHASE 角色的用户访问。
    """

    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "PURCHASE"

    def has_object_permission(self, request, view, obj):
        return True  # 默认允许访问所有对象，具体限制由子类或业务逻辑控制
