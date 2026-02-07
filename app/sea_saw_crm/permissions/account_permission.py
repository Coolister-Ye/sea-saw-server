from rest_framework.permissions import BasePermission


class AccountPermission(BasePermission):
    """
    Permission for unified Account model.

    Since Account is a unified entity (not role-specific), both SALE and PURCHASE
    users can access accounts. The role distinction is handled at the business
    level (Order/PurchaseOrder creation).

    - SALE, PURCHASE, ADMIN can create/list accounts
    - Users can only update/delete their own accounts
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
            return role_type in ["SALE", "PURCHASE", "ADMIN"]

        if view.action in ["retrieve", "update", "partial_update", "destroy"]:
            return role_type in ["SALE", "PURCHASE", "ADMIN"]

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Superusers and staff have full access
        if user.is_superuser or user.is_staff:
            return True

        role_type = getattr(user.role, "role_type", None)

        if role_type == "ADMIN":
            return True

        if role_type in ["SALE", "PURCHASE"]:
            if view.action == "retrieve":
                return self._is_visible(user, obj)
            elif view.action in ["update", "partial_update", "destroy"]:
                return getattr(obj, "owner", None) == user

        return False

    def _is_visible(self, user, obj):
        """Check if the user can see this account based on visibility rules."""
        owner = getattr(obj, "owner", None)
        if not owner:
            return False
        get_users = getattr(user, "get_all_visible_users", None)
        if not callable(get_users):
            return False
        return owner in get_users()
