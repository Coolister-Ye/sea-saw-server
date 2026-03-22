from rest_framework import permissions


class BankAccountPermission(permissions.BasePermission):
    """
    Permission for BankAccount model.

    Bank accounts are sub-entities of Account, accessible by both SALE
    and PURCHASE roles (customers and suppliers both have bank accounts).

    Object-level visibility follows the parent Account's ownership rules.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

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

        if user.is_superuser or user.is_staff:
            return True

        role_type = getattr(user.role, "role_type", None)

        if role_type == "ADMIN":
            return True

        if role_type in ["SALE", "PURCHASE"]:
            if view.action == "retrieve":
                return self._is_account_visible(user, obj)
            elif view.action in ["update", "partial_update", "destroy"]:
                # Allow if the user owns the parent account
                account = getattr(obj, "account", None)
                return account and getattr(account, "owner", None) == user

        return False

    def _is_account_visible(self, user, obj):
        """Check visibility via the parent account's owner."""
        account = getattr(obj, "account", None)
        if not account:
            return False
        owner = getattr(account, "owner", None)
        if not owner:
            return False
        get_users = getattr(user, "get_all_visible_users", None)
        if not callable(get_users):
            return False
        return owner in get_users()
