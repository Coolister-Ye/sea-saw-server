from rest_framework.permissions import BasePermission


class CompanyPermission(BasePermission):
    """
    Permission for Contact model.
    - SALE can create/list only visible contacts, retrieve own visible contacts, update/delete own contacts
    - ADMIN can do anything
    """

    def has_permission(self, request, view):
        user = request.user
        role_type = getattr(user.role, "role_type", None)

        # 所有已认证用户可访问
        if not user.is_authenticated:
            return False

        # CREATE / LIST / OPTIONS / HEAD
        if view.action in ["create", "list", "options", "head"]:
            return role_type in ["SALE", "ADMIN"]

        # RETRIEVE / UPDATE / PARTIAL_UPDATE / DESTROY
        if view.action in ["retrieve", "update", "partial_update", "destroy"]:
            return role_type in ["SALE", "ADMIN"]

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        role_type = getattr(user.role, "role_type", None)

        # ADMIN 可以操作所有对象
        if role_type == "ADMIN":
            return True

        # SALE 权限逻辑
        if role_type == "SALE":
            if view.action == "retrieve":
                # 只允许查看可见对象
                return self._is_visible(user, obj)
            elif view.action in ["update", "partial_update", "destroy"]:
                # 只允许操作自己的对象
                return getattr(obj, "owner", None) == user

        return False

    def _is_visible(self, user, obj):
        owner = getattr(obj, "owner", None)
        if not owner:
            return False
        get_users = getattr(owner, "get_all_visible_users", None)
        if not callable(get_users):
            return False
        return user in get_users()
