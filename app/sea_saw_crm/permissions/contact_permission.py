"""
Contact 权限类

专门针对 Contact 模型的权限控制。
Contact 允许 Admin 和 Sale 角色访问，基于 owner 进行访问控制。
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class ContactAdminPermission(BasePermission):
    """
    Contact Admin 权限

    Admin 角色对所有 Contact 有完全权限。
    """

    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "ADMIN"

    def has_object_permission(self, request, view, obj):
        return True  # admin 对所有对象都有权限


class ContactSalePermission(BasePermission):
    """
    Contact Sale 权限

    Sale 角色基于 owner 的 Contact 权限：
    - 读取权限：可以查看自己或可见用户创建的联系人
    - 创建权限：可以创建新联系人
    - 修改/删除权限：只能修改/删除自己创建的联系人
    """

    def has_permission(self, request, view):
        role_type = getattr(request.user.role, "role_type", None)
        if role_type != "SALE":
            return False

        # Sale 允许所有声明的操作（具体限制在对象级权限）
        return view.action in {
            "list",
            "retrieve",
            "create",
            "update",
            "partial_update",
            "destroy",
        }

    def has_object_permission(self, request, view, obj):
        user = request.user
        owner = getattr(obj, "owner", None)

        if request.method in SAFE_METHODS:
            # 读取权限：自己或可见用户创建的联系人
            if owner == user:
                return True

            # 检查是否在可见用户列表中
            get_visible_users = getattr(owner, "get_all_visible_users", None)
            if callable(get_visible_users):
                return user in get_visible_users()

            return False
        else:
            # 修改/删除权限：仅 owner
            return owner == user
