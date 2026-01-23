"""
Pipeline Permission Classes

针对 Pipeline 模型的权限控制，基于用户角色和 Pipeline 状态进行访问控制。
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class PipelineAdminPermission(BasePermission):
    """
    Admin 角色对所有 Pipeline 有完全权限

    注意: Pipeline 不允许 update/partial_update 操作,因为 base 字段
    (contact, order_date, total_amount, paid_amount) 应该通过关联对象自动更新
    """

    def has_permission(self, request, view):
        # 禁止 update 和 partial_update 操作
        if view.action in ["update", "partial_update"]:
            return False

        return (
            getattr(request.user.role, "role_type", None) == "ADMIN"
            or request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        return True  # admin 对所有对象都有权限


class PipelineSalePermission(BasePermission):
    """
    Sale 角色基于 owner 的 Pipeline 权限

    注意: Pipeline 不允许 update/partial_update 操作,因为 base 字段
    应该通过关联对象自动更新
    """

    def has_permission(self, request, view):
        # 禁止 update 和 partial_update 操作
        if view.action in ["update", "partial_update"]:
            return False

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
            # delete 权限：仅 owner 且状态为 DRAFT
            return owner == user and getattr(obj, "status", None) == "draft"


class PipelineProductionPermission(BasePermission):
    """
    Production 角色基于 Pipeline 状态的权限

    注意: Pipeline 不允许 update/partial_update 操作,因为 base 字段
    应该通过关联对象自动更新
    """

    def has_permission(self, request, view):
        """Production 用户只能操作特定状态的 Pipeline"""

        # 禁止 create, update, partial_update 和 destroy 操作
        if view.action in ["create", "update", "partial_update", "destroy"]:
            return False
        return getattr(request.user.role, "role_type", None) == "PRODUCTION"

    def has_object_permission(self, request, view, obj):  # noqa: ARG002
        # Production 角色只有读权限,所有非安全方法都拒绝
        return request.method in SAFE_METHODS


class PipelineWarehousePermission(BasePermission):
    """
    Warehouse 角色基于 Pipeline 状态的权限

    注意: Pipeline 不允许 update/partial_update 操作,因为 base 字段
    应该通过关联对象自动更新
    """

    def has_permission(self, request, view):
        """Warehouse 用户只能操作仓库相关状态的 Pipeline"""

        # 禁止 create, update, partial_update 和 destroy 操作
        if view.action in ["create", "update", "partial_update", "destroy"]:
            return False
        return getattr(request.user.role, "role_type", None) == "WAREHOUSE"

    def has_object_permission(self, request, view, obj):  # noqa: ARG002
        # Warehouse 角色只有读权限,所有非安全方法都拒绝
        return request.method in SAFE_METHODS


class PipelinePurchasePermission(BasePermission):
    """
    Purchase 角色基于 Pipeline 状态的权限

    注意: Pipeline 不允许 update/partial_update 操作,因为 base 字段
    应该通过关联对象自动更新
    """

    def has_permission(self, request, view):
        """Purchase 用户只能操作采购相关状态的 Pipeline"""

        # 禁止 create, update, partial_update 和 destroy 操作
        if view.action in ["create", "update", "partial_update", "destroy"]:
            return False
        return getattr(request.user.role, "role_type", None) == "PURCHASE"

    def has_object_permission(self, request, view, obj):  # noqa: ARG002
        # Purchase 角色只有读权限,所有非安全方法都拒绝
        return request.method in SAFE_METHODS
