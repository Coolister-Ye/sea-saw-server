from rest_framework.permissions import BasePermission


class FieldPermission(BasePermission):
    """
    Only ADMIN users are allowed.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Superusers and staff have full access
        if user.is_superuser or user.is_staff:
            return True

        role_type = getattr(getattr(user, "role", None), "role_type", None)

        return role_type == "ADMIN"
