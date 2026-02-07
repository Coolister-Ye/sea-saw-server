from rest_framework import permissions


class ContactPermission(permissions.BasePermission):
    """
    Permissions for Contact model:
    - SALE can create/list only visible contacts, retrieve own visible contacts, update/delete own contacts
    - ADMIN can do anything
    """

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        # Superusers and staff have full access
        if user.is_superuser or user.is_staff:
            return True

        role_type = getattr(user.role, "role_type", None)

        if view.action in ["create", "list", "options", "head"]:
            return role_type in ["SALE", "ADMIN"]

        if view.action in ["retrieve", "update", "partial_update", "destroy"]:
            return role_type in ["SALE", "ADMIN"]

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Superusers and staff have full access
        if user.is_superuser or user.is_staff:
            return True

        role_type = getattr(user.role, "role_type", None)

        if role_type == "ADMIN":
            return True

        if role_type == "SALE":
            if view.action == "retrieve":
                return self._is_visible(user, obj)
            elif view.action in ["update", "partial_update", "destroy"]:
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
